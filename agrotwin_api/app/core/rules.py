"""
Rule / constraint engine (doc 07).

Hard and warning checks are data-driven from region_config. Validation Agent
and the Optimizer both consume this engine. Rules never invent kg/ha.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Callable

from .region_config import load_region_config


@dataclass
class Violation:
    rule_id: str
    severity: str  # HARD | WARNING
    message: str
    passed: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def _product_codes(plan: dict[str, Any]) -> set[str]:
    how_much = plan.get("how_much") or plan.get("plan_kg_ha") or {}
    codes = set()
    for key, qty in how_much.items():
        if not key.endswith("_kg_ha") or key.startswith("n_supplied"):
            continue
        if float(qty or 0) > 0:
            codes.add(key.replace("_kg_ha", "").upper())
    return codes


def _supplied_npk(plan: dict[str, Any], products: dict[str, dict]) -> dict[str, float]:
    how_much = plan.get("how_much") or plan.get("plan_kg_ha") or {}
    n = p = k = 0.0
    for key, qty in how_much.items():
        if not key.endswith("_kg_ha") or key.startswith("n_supplied"):
            continue
        code = key.replace("_kg_ha", "")
        comp = products.get(code) or products.get(code.upper())
        if not comp:
            continue
        q = float(qty or 0)
        n += q * float(comp.get("n") or 0) / 100.0
        p += q * float(comp.get("p2o5") or 0) / 100.0
        k += q * float(comp.get("k2o") or 0) / 100.0
    return {"N": round(n, 1), "P2O5": round(p, 1), "K2O": round(k, 1)}


def _check_max_rates(plan: dict, twin: dict, cfg: dict) -> Violation:
    rule = cfg["rules"]["max_rates"]
    required = (plan.get("required") or twin.get("current_plan") or {}).get("required")
    if not required:
        required = plan.get("required") or {}
    products = twin.get("products") or {}
    if not required or not products:
        return Violation(
            rule["rule_id"],
            "WARNING",
            f"MAX_RATES skipped (missing RDF or product table). {rule['citation']}",
            passed=True,
        )
    supplied = _supplied_npk(plan, products)
    tol = float(rule["rounding_tol_kg_ha"])
    over = []
    for nutrient in ("N", "P2O5", "K2O"):
        req = required.get(nutrient)
        if req is None:
            continue
        if supplied[nutrient] > float(req) + tol:
            over.append(
                f"{nutrient} supplied {supplied[nutrient]} > required {req} + tol {tol}"
            )
    if over:
        return Violation(
            rule["rule_id"],
            "HARD",
            "MAX_RATES violated: " + "; ".join(over) + f" [{rule['citation']}]",
            passed=False,
        )
    return Violation(
        rule["rule_id"],
        "HARD",
        f"MAX_RATES ok (supplied {supplied} vs RDF {required}). [{rule['citation']}]",
        passed=True,
    )


def _check_compatibility(plan: dict, twin: dict, cfg: dict) -> Violation:
    rule = cfg["rules"]["compatibility"]
    codes = _product_codes(plan)
    for a, b in rule["incompatible_pairs"]:
        if a.upper() in codes and b.upper() in codes:
            return Violation(
                rule["rule_id"],
                "HARD",
                f"Incompatible mix: {a} + {b} in the same application. "
                f"[{rule['citation']}]",
                passed=False,
            )
    return Violation(rule["rule_id"], "HARD", "Compatibility ok.", passed=True)


def _check_weather(plan: dict, twin: dict, cfg: dict) -> Violation:
    rule = cfg["rules"]["weather_windows"]
    weather = twin.get("weather") or {}
    gap = plan.get("gap") or (twin.get("current_plan") or {}).get("gap") or {}
    heavy = bool(weather.get("heavy_rain_alert"))
    if heavy and rule.get("no_application_if_heavy_rain") and float(gap.get("N") or 0) > 0:
        return Violation(
            rule["rule_id"],
            "HARD",
            (
                "WEATHER_CONFLICT: heavy rain expected in the current application "
                f"window. Defer soluble N. {weather.get('alert_details', '')} "
                f"[{rule['citation']}]"
            ),
            passed=False,
        )
    return Violation(rule["rule_id"], "HARD", "Weather window ok.", passed=True)


def _check_soil_ph(plan: dict, twin: dict, cfg: dict) -> Violation:
    rule = cfg["rules"]["soil_limits"]
    soil = twin.get("soil") or {}
    ph = soil.get("ph")
    if ph is None:
        return Violation(rule["rule_id"], "WARNING", "pH not available — skipped.", passed=True)
    ph = float(ph)
    if ph > float(rule["ph_max"]):
        return Violation(
            rule["rule_id"],
            "WARNING",
            f"HIGH_PH_WARNING (pH {ph} > {rule['ph_max']}). [{rule['citation']}]",
            passed=False,
        )
    if ph < float(rule["ph_min"]):
        return Violation(
            rule["rule_id"],
            "WARNING",
            f"LOW_PH_WARNING (pH {ph} < {rule['ph_min']}). [{rule['citation']}]",
            passed=False,
        )
    return Violation(rule["rule_id"], "WARNING", f"Soil pH {ph} within window.", passed=True)


def _check_freshness(plan: dict, twin: dict, cfg: dict) -> Violation:
    rule = cfg["rules"]["data_freshness"]
    soil = twin.get("soil") or {}
    if not soil:
        # Isolated validation may omit soil; the pipeline already abstains
        # before optimization when no soil test exists.
        return Violation(
            rule["rule_id"],
            "WARNING",
            "Soil context not provided to rule engine — freshness skipped.",
            passed=True,
        )
    if soil.get("is_stale"):
        days = soil.get("days_since_test")
        return Violation(
            rule["rule_id"],
            "WARNING",
            f"STALE_SOIL_DATA (test is {days} days old; threshold "
            f"{rule['soil_max_age_days']}). Action={rule['stale_action']}. "
            f"[{rule['citation']}]",
            passed=False,
        )
    return Violation(rule["rule_id"], "WARNING", "Soil data is fresh.", passed=True)


def _check_ec(plan: dict, twin: dict, cfg: dict) -> Violation:
    rule = cfg["rules"]["ec_limits"]
    soil = twin.get("soil") or {}
    ec = soil.get("ec_ds_m")
    if ec is None:
        return Violation(rule["rule_id"], "WARNING", "EC not available — skipped.", passed=True)
    if float(ec) > float(rule["ec_ds_m_max"]):
        return Violation(
            rule["rule_id"],
            "WARNING",
            f"HIGH_EC_WARNING (EC {ec} dS/m > {rule['ec_ds_m_max']}). [{rule['citation']}]",
            passed=False,
        )
    return Violation(rule["rule_id"], "WARNING", f"Soil EC {ec} dS/m within window.", passed=True)


class RuleEngine:
    """List of callable checks that return (pass/fail, reason) as Violation."""

    def __init__(self, extra_checks: list[Callable] | None = None) -> None:
        self._checks: list[Callable] = [
            _check_freshness,
            _check_max_rates,
            _check_compatibility,
            _check_weather,
            _check_soil_ph,
            _check_ec,
        ]
        if extra_checks:
            self._checks.extend(extra_checks)

    def check(self, plan: dict[str, Any], twin: dict[str, Any]) -> list[Violation]:
        cfg = load_region_config(twin.get("region_id"))
        return [fn(plan, twin, cfg) for fn in self._checks]

    def hard_failures(self, plan: dict, twin: dict) -> list[Violation]:
        return [v for v in self.check(plan, twin) if v.severity == "HARD" and not v.passed]
