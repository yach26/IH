"""
Validation Agent — runs the Rule Engine after optimization (docs 05 + 07).

Does not override quantities. Returns is_valid / warnings / blocking_issues
and flags to append to the proof-carrying recommendation.
"""

from __future__ import annotations

from typing import Any

from ..core.rules import RuleEngine, Violation


def validate_ledger_result(
    ledger_result: dict,
    soil_context: dict | None,
    weather_context: dict | None,
    products: dict | None = None,
    region_id: str | None = None,
) -> dict:
    """
    Evaluates cross-agent constraints via RuleEngine.
    Returns: {"is_valid", "warnings", "blocking_issues", "flags_added", "violations"}
    """
    if ledger_result.get("status") == "ABSTAIN":
        return {
            "is_valid": False,
            "warnings": [],
            "blocking_issues": [f"LEDGER_ABSTAIN: {ledger_result.get('reason')}"],
            "flags_added": [],
            "violations": [],
        }

    twin = {
        "region_id": region_id,
        "soil": soil_context or {},
        "weather": weather_context or {},
        "products": products or {},
        "current_plan": ledger_result,
    }
    plan = {
        "plan_kg_ha": ledger_result.get("plan_kg_ha") or {},
        "how_much": ledger_result.get("plan_kg_ha") or {},
        "gap": ledger_result.get("gap") or {},
        "required": ledger_result.get("required") or {},
    }
    engine = RuleEngine()
    violations = engine.check(plan, twin)
    return _from_violations(violations)


def _from_violations(violations: list[Violation]) -> dict[str, Any]:
    warnings: list[str] = []
    blocking: list[str] = []
    flags_added: list[str] = []
    for v in violations:
        if v.passed:
            continue
        if v.severity == "HARD":
            blocking.append(v.message)
        else:
            warnings.append(v.message)
        if "WEATHER_CONFLICT" in v.message:
            flags_added.append("WEATHER_CONFLICT")
        elif "HIGH_PH" in v.message:
            flags_added.append("HIGH_PH_WARNING")
        elif "LOW_PH" in v.message:
            flags_added.append("LOW_PH_WARNING")
        elif "STALE_SOIL" in v.message:
            flags_added.append("STALE_SOIL_DATA")
        elif "HIGH_EC" in v.message:
            flags_added.append("HIGH_EC_WARNING")
        elif "SEVERE_OVER" in v.message:
            flags_added.append("SEVERE_OVER_APPLICATION")
        else:
            flags_added.append(v.rule_id)
    return {
        "is_valid": len(blocking) == 0,
        "warnings": warnings,
        "blocking_issues": blocking,
        "flags_added": flags_added,
        "violations": [v.to_dict() for v in violations],
    }
