"""
Recommendation Pipeline (doc 05).

Ordered steps:
  Farmer Input → Validation → Twin update → Soil → Crop → Weather
  → Ledger (gap) → Optimizer (quantities) → Validation (rules)
  → Knowledge (citations only) → Confidence → persist proof object
  → PLAN_CREATED

Supports:
  - full run
  - selective re-plan (`agents=["weather","validation","optimizer"]`)

The LLM is not on this path. kg/ha come only from ledger.convert_gap_to_products
via HeuristicOptimizer.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Iterable

from . import ledger as ledger_module
from .agents import crop_agent, knowledge_agent, soil_agent, weather_agent
from .agents.twin_state import compute_confidence, make_empty_twin_state
from .core.event_bus import get_bus
from .core.events import Event, EventType
from .core.optimizer import HeuristicOptimizer, Optimizer, OptimizerPlan, get_optimizer
from .core.proof import assemble_proof
from .core.rules import RuleEngine
from .db import _json_load

FULL_STEPS = (
    "input_validation",
    "twin_update",
    "soil",
    "crop",
    "weather",
    "ledger",
    "optimizer",
    "validation",
    "knowledge",
    "confidence",
    "persist",
)

# Event → default agent subset for selective re-plan (doc 08 wow path)
EVENT_AGENT_MAP: dict[str, tuple[str, ...]] = {
    EventType.HEAVY_RAIN_ALERT.value: ("weather", "optimizer", "validation"),
    EventType.WEATHER_FORECAST_CHANGED.value: ("weather", "validation"),
    EventType.SOIL_REPORT_UPDATED.value: (
        "soil",
        "ledger",
        "optimizer",
        "validation",
    ),
    EventType.CROP_STAGE_CHANGED.value: (
        "crop",
        "ledger",
        "optimizer",
        "validation",
    ),
    EventType.FERTILIZER_APPLIED.value: ("ledger", "optimizer", "validation"),
}

# Always finish with knowledge + confidence + persist after a re-plan
_REPLAN_TAIL = ("knowledge", "confidence", "persist")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RecommendationPipeline:
    def __init__(
        self,
        optimizer: Optimizer | None = None,
        rule_engine: RuleEngine | None = None,
        bus=None,
    ) -> None:
        self.optimizer = optimizer or HeuristicOptimizer()
        self.rule_engine = rule_engine or RuleEngine()
        self.bus = bus or get_bus()

    def run(
        self,
        conn: sqlite3.Connection,
        field_row: sqlite3.Row,
        *,
        agents: Iterable[str] | None = None,
        optimizer: Optimizer | str | None = None,
        mock_weather: dict | None = None,
        farmer_input: dict | None = None,
        previous_plan: dict | None = None,
        emit_events: bool = True,
        persist: bool = True,
    ) -> dict[str, Any]:
        opt = self.optimizer
        if optimizer:
            opt = get_optimizer(optimizer) if isinstance(optimizer, str) else optimizer
        field_id = field_row["field_id"]
        field_code = field_row["field_code"]
        mode = "full" if not agents else "partial_replan"
        requested = set(agents) if agents else set(FULL_STEPS)
        if agents:
            requested.update(_REPLAN_TAIL)

        audit: list[dict] = []
        agents_run: list[str] = []

        region_id = ""
        if "region_id" in field_row.keys() and field_row["region_id"] is not None:
            region_id = str(field_row["region_id"])

        twin = make_empty_twin_state(str(field_id), region_id)
        twin["field_code"] = field_code  # type: ignore[typeddict-unknown-key]

        # ── 1. Farmer input + schema validation ─────────────────────────
        if "input_validation" in requested or mode == "full":
            agents_run.append("input_validation")
            missing = self._validate_input(conn, field_row, farmer_input)
            audit.append({"step": "input_validation", "missing": missing})
            if missing:
                return self._abstain(
                    conn,
                    twin,
                    ledger={"field_id": field_id, "field_code": field_code, "flags": []},
                    reason="Incomplete required fields: " + ", ".join(missing),
                    required_actions=[
                        "Provide crop, recommendation_type, and a soil test before recommending."
                    ],
                    mode=mode,
                    agents_run=agents_run,
                    audit=audit,
                    emit_events=emit_events,
                    persist=persist,
                )

        # ── 2. Digital twin update ──────────────────────────────────────
        if farmer_input and ("twin_update" in requested or mode == "full"):
            agents_run.append("twin_update")
            self._apply_farmer_input(conn, field_id, farmer_input)
            field_row = conn.execute(
                "SELECT * FROM field_active_crop WHERE field_id = ?",
                (field_id,),
            ).fetchone()
            audit.append({"step": "twin_update", "keys": list(farmer_input.keys())})

        history = self._load_history(conn, field_id)
        twin["history"] = history
        if previous_plan is None and mode == "partial_replan":
            previous_plan = history[0] if history else None

        products = ledger_module.get_products(conn)
        twin["products"] = products  # type: ignore[typeddict-unknown-key]

        # ── 3. Soil ─────────────────────────────────────────────────────
        if "soil" in requested:
            agents_run.append("soil")
            soil_ctx = soil_agent.get_soil_context(conn, field_id)
            if soil_ctx:
                twin["soil"] = soil_ctx
                twin["flags"].extend(soil_ctx.get("flags") or [])
                twin["data_quality"]["has_soil_test"] = True
                twin["data_quality"]["soil_is_fresh"] = not soil_ctx.get("is_stale")
            audit.append({"step": "soil", "present": soil_ctx is not None})
        elif previous_plan:
            twin["soil"] = previous_plan.get("soil_context") or {}
            twin["data_quality"]["has_soil_test"] = bool(twin["soil"])
            twin["data_quality"]["soil_is_fresh"] = not (twin["soil"] or {}).get("is_stale")

        # ── 4. Crop ─────────────────────────────────────────────────────
        if "crop" in requested:
            agents_run.append("crop")
            crop_ctx = crop_agent.get_crop_context(conn, field_row)
            if crop_ctx:
                twin["crop"] = crop_ctx
                twin["flags"].extend(crop_ctx.get("flags") or [])
                twin["data_quality"]["has_crop"] = True
                twin["data_quality"]["has_rec_type"] = bool(crop_ctx.get("recommendation_type"))
                twin["data_quality"]["stage_in_calendar"] = bool(crop_ctx.get("stage_valid", True))
            audit.append({"step": "crop", "present": crop_ctx is not None})
        elif previous_plan:
            twin["crop"] = previous_plan.get("crop_context") or {}
            twin["data_quality"]["has_crop"] = bool(twin["crop"])
            twin["data_quality"]["has_rec_type"] = bool((twin["crop"] or {}).get("recommendation_type"))

        # ── 5. Weather ──────────────────────────────────────────────────
        if "weather" in requested:
            agents_run.append("weather")
            lat = field_row["lat"] if "lat" in field_row.keys() else None
            lon = field_row["lon"] if "lon" in field_row.keys() else None
            weather_ctx = weather_agent.get_weather_context(
                conn, field_id, lat, lon, force_refresh=False, mock_snapshot=mock_weather
            )
            twin["weather"] = weather_ctx
            twin["flags"].extend(weather_ctx.get("flags") or [])
            twin["data_quality"]["has_weather"] = weather_ctx.get("snapshot") is not None
            twin["data_quality"]["weather_ok"] = "WEATHER_FETCH_ERROR" not in str(
                weather_ctx.get("flags")
            )
            audit.append(
                {
                    "step": "weather",
                    "heavy_rain_alert": weather_ctx.get("heavy_rain_alert"),
                }
            )
        elif previous_plan:
            twin["weather"] = previous_plan.get("weather_context") or {}
            twin["data_quality"]["has_weather"] = True

        # ── 6. Ledger (the only place nutrient gaps are born) ───────────
        if "ledger" in requested:
            agents_run.append("ledger")
            ledger_result = ledger_module.run_field_ledger(conn, field_row)
            audit.append(
                {
                    "step": "ledger",
                    "status": ledger_result.get("status"),
                    "gap": ledger_result.get("gap"),
                }
            )
            if ledger_result.get("status") == "ABSTAIN":
                twin["flags"].extend(ledger_result.get("flags") or [])
                twin["flags"].append("ABSTAIN:" + str(ledger_result.get("reason")))
                return self._abstain(
                    conn,
                    twin,
                    ledger=ledger_result,
                    reason=ledger_result.get("reason") or "Ledger abstained",
                    required_actions=self._actions_for_ledger_abstain(ledger_result),
                    mode=mode,
                    agents_run=agents_run,
                    audit=audit,
                    emit_events=emit_events,
                    persist=persist,
                )
        else:
            if not previous_plan or not previous_plan.get("ledger"):
                return self._abstain(
                    conn,
                    twin,
                    ledger={"field_id": field_id, "field_code": field_code, "flags": []},
                    reason="Partial re-plan requested without a prior ledger result.",
                    required_actions=["Run a full recommendation first."],
                    mode=mode,
                    agents_run=agents_run,
                    audit=audit,
                    emit_events=emit_events,
                    persist=persist,
                )
            ledger_result = dict(previous_plan["ledger"])
            audit.append({"step": "ledger", "reused": True, "status": ledger_result.get("status")})

        twin["flags"].extend(ledger_result.get("flags") or [])
        twin["current_plan"] = ledger_result

        # ── 7. Optimizer (heuristic by default, or linprog) ─────────────
        optimizer_plan: OptimizerPlan | None = None
        optimizer_dict: dict | None = None
        if "optimizer" in requested and ledger_result.get("status") != "ABSTAIN":
            agents_run.append("optimizer")
            optimizer_plan = opt.optimize(twin, candidates=None)
            # Enforce: quantities must match ledger heuristic if using heuristic
            ledger_qty = ledger_result.get("plan_kg_ha") or {}
            optimizer_dict = {
                "status": optimizer_plan.meta.get("status", "OK"),
                "flag": optimizer_plan.meta.get("flag", ""),
                "plan_kg_ha": optimizer_plan.plan_kg_ha,
                "total_kg_ha": optimizer_plan.total_kg_ha,
                "cost_estimate": optimizer_plan.cost_estimate,
                "cost_currency": optimizer_plan.cost_currency,
                "cost_citation": optimizer_plan.cost_citation,
                "optimizer_id": optimizer_plan.optimizer_id,
                "message": optimizer_plan.message,
            }
            # Prefer ledger plan_kg_ha as numeric truth when heuristic is selected
            if getattr(opt, "optimizer_id", "") == "heuristic_dap_urea_mop":
                for k in ("DAP_kg_ha", "UREA_kg_ha", "MOP_kg_ha"):
                    if k in ledger_qty and k in optimizer_plan.plan_kg_ha:
                        if float(optimizer_plan.plan_kg_ha[k]) != float(ledger_qty[k]):
                            optimizer_dict["flag"] = (
                                "OPTIMIZER_LEDGER_MISMATCH — falling back to ledger quantities"
                            )
                            optimizer_plan.plan_kg_ha = ledger_qty
                            optimizer_dict["plan_kg_ha"] = ledger_qty
            twin["flags"].extend(
                [optimizer_dict[k] for k in ("flag",) if optimizer_dict.get(k)]
            )
            audit.append(
                {
                    "step": "optimizer",
                    "optimizer_id": optimizer_plan.optimizer_id,
                    "total_kg_ha": optimizer_plan.total_kg_ha,
                    "cost_estimate": optimizer_plan.cost_estimate,
                }
            )
        elif previous_plan:
            optimizer_dict = previous_plan.get("optimizer_result")

        # ── 8. Agronomic validation (rule engine) ───────────────────────
        agents_run.append("validation")
        plan_for_rules = {
            "plan_kg_ha": (optimizer_dict or {}).get("plan_kg_ha")
            or ledger_result.get("plan_kg_ha"),
            "gap": ledger_result.get("gap"),
            "required": ledger_result.get("required"),
            "how_much": (optimizer_dict or {}).get("plan_kg_ha")
            or ledger_result.get("plan_kg_ha"),
        }
        violations = self.rule_engine.check(plan_for_rules, twin)
        validation = self._validation_from_violations(violations, ledger_result)
        twin["flags"].extend(validation.get("flags_added") or [])
        audit.append(
            {
                "step": "validation",
                "is_valid": validation["is_valid"],
                "blocking": validation["blocking_issues"],
            }
        )

        # Weather conflict → safer plan (defer window), not silent ABSTAIN
        status = ledger_result.get("status") or "PLAN_GENERATED"
        if mode == "partial_replan":
            status = "PLAN_REVISED"
        if status == "NO_FERTILIZER_NEEDED":
            pass
        elif not validation["is_valid"] and any(
            "WEATHER_CONFLICT" in b for b in validation["blocking_issues"]
        ):
            if mode == "partial_replan":
                status = "PLAN_REVISED"
            # keep quantities; when-window is derived from weather in proof

        # ── 9. Evidence (after a candidate plan exists) ─────────────────
        evidence: list[dict] = []
        if "knowledge" in requested:
            agents_run.append("knowledge")
            crop_code = (twin.get("crop") or {}).get("crop_code")
            rec_type = (twin.get("crop") or {}).get("recommendation_type")
            district_row = conn.execute(
                "SELECT district_code FROM districts WHERE district_id = ?",
                (field_row["district_id"],),
            ).fetchone()
            region_str = district_row["district_code"] if district_row else None
            extra = ""
            if (twin.get("weather") or {}).get("heavy_rain_alert"):
                extra = "heavy rainfall fertilizer application window"
            evidence = knowledge_agent.retrieve_evidence(
                crop_code=crop_code,
                region=region_str,
                recommendation_type=rec_type,
                extra_query=extra,
                top_k=4,
            )
            twin["evidence"] = evidence
            audit.append({"step": "knowledge", "n_chunks": len(evidence)})

        # ── 10. Confidence ──────────────────────────────────────────────
        # Soil/validation/rules agents each flag issues independently (e.g.
        # STALE_SOIL_DATA can be raised by soil_agent, validation_agent and
        # rules.py for the same underlying soil test) — dedupe by the leading
        # code before scoring so one real issue isn't double-counted or
        # double-displayed.
        seen_codes = set()
        deduped_flags = []
        for flag in twin["flags"]:
            code = flag.split(" (", 1)[0].split(":", 1)[0]
            if code in seen_codes:
                continue
            seen_codes.add(code)
            deduped_flags.append(flag)
        twin["flags"] = deduped_flags

        agents_run.append("confidence")
        twin["confidence"] = compute_confidence(twin["flags"])
        if twin["confidence"] == "ABSTAIN":
            return self._abstain(
                conn,
                twin,
                ledger=ledger_result,
                reason="Confidence collapsed to ABSTAIN",
                required_actions=["Review flags and supply missing data."],
                mode=mode,
                agents_run=agents_run,
                audit=audit,
                emit_events=emit_events,
                persist=persist,
            )
        ledger_result["confidence"] = twin["confidence"]
        ledger_result["flags"] = twin["flags"]
        audit.append({"step": "confidence", "level": twin["confidence"]})

        proof = assemble_proof(
            status=status,
            ledger=ledger_result,
            twin=twin,
            optimizer_plan=optimizer_dict,
            validation=validation,
            evidence=evidence,
            mode=mode,
            agents_run=agents_run,
            audit=audit,
        )
        twin["current_plan"] = proof

        # Narrative annotates the finalized deterministic plan; never changes quantities.
        from .agents.report_agent import compile_report
        proof["narrative"] = compile_report(proof)["narrative"]

        # ── 11. Persist + events ────────────────────────────────────────
        rec_id = None
        if persist and "persist" in requested:
            agents_run.append("persist")
            rec_id = self._persist(conn, proof, previous_plan=previous_plan)
            proof["recommendation_id"] = rec_id
            audit.append({"step": "persist", "recommendation_id": rec_id})

        if persist and emit_events and rec_id is not None:
            created_type = (
                EventType.RECOMMENDATION_RECALCULATED
                if mode == "partial_replan"
                else EventType.PLAN_CREATED
            )
            self.bus.publish(
                Event.create(
                    created_type,
                    field_id=int(field_id),
                    field_code=field_code,
                    payload={
                        "recommendation_id": rec_id,
                        "status": status,
                        "mode": mode,
                        "agents_run": agents_run,
                    },
                ),
                conn=conn,
            )

        # Backward-compatible keys used by existing orchestrator tests
        proof["gap"] = ledger_result.get("gap")
        proof["plan_kg_ha"] = ledger_result.get("plan_kg_ha")
        return proof

    # ── helpers ──────────────────────────────────────────────────────────

    def _validate_input(
        self,
        conn: sqlite3.Connection,
        field_row: sqlite3.Row,
        farmer_input: dict | None,
    ) -> list[str]:
        missing: list[str] = []
        crop_id = field_row["current_crop_id"] if "current_crop_id" in field_row.keys() else None
        rec_type = field_row["recommendation_type"] if "recommendation_type" in field_row.keys() else None
        if farmer_input:
            crop_id = farmer_input.get("crop_id", crop_id)
            rec_type = farmer_input.get("recommendation_type", rec_type)
        if crop_id is None:
            missing.append("crop")
        if not rec_type:
            missing.append("recommendation_type")
        soil = conn.execute(
            "SELECT soil_test_id FROM soil_tests WHERE field_id = ? LIMIT 1",
            (field_row["field_id"],),
        ).fetchone()
        if soil is None and not (farmer_input and farmer_input.get("soil_test")):
            missing.append("soil_test")
        return missing

    def _apply_farmer_input(
        self, conn: sqlite3.Connection, field_id: int, farmer_input: dict
    ) -> None:
        soil = farmer_input.get("soil_test")
        if soil:
            soil_agent.write_soil_test(
                conn,
                field_id,
                soil.get("test_date") or date_today(),
                float(soil["n_kg_ha"]),
                float(soil["p_kg_ha"]),
                float(soil["k_kg_ha"]),
                ph=soil.get("ph"),
                oc_percent=soil.get("oc_percent"),
                ec_ds_m=soil.get("ec_ds_m"),
                source=soil.get("source") or "manual",
            )
        if farmer_input.get("current_stage") or farmer_input.get("recommendation_type"):
            sets = []
            vals: list[Any] = []
            if farmer_input.get("current_stage"):
                sets.append("current_stage = ?")
                vals.append(farmer_input["current_stage"])
            if farmer_input.get("recommendation_type"):
                sets.append("recommendation_type = ?")
                vals.append(farmer_input["recommendation_type"])
            vals.append(field_id)
            conn.execute(
                f"UPDATE field_crops SET {', '.join(sets)} WHERE field_id = ? AND is_active = TRUE",
                vals,
            )
            conn.commit()

    def _load_history(self, conn: sqlite3.Connection, field_id: int) -> list[dict]:
        rows = conn.execute(
            """SELECT recommendation_id, plan_json, status, generated_at, invalidated_at
               FROM recommendations WHERE field_id = ?
               ORDER BY generated_at DESC LIMIT 10""",
            (field_id,),
        ).fetchall()
        out = []
        for r in rows:
            try:
                plan = _json_load(r["plan_json"])
            except (json.JSONDecodeError, TypeError):
                plan = {}
            plan["recommendation_id"] = r["recommendation_id"]
            plan["status_db"] = r["status"]
            plan["generated_at"] = r["generated_at"]
            out.append(plan)
        return out

    def _validation_from_violations(self, violations, ledger_result) -> dict:
        warnings = []
        blocking = []
        flags_added = []
        if ledger_result.get("status") == "ABSTAIN":
            return {
                "is_valid": False,
                "warnings": [],
                "blocking_issues": [f"LEDGER_ABSTAIN: {ledger_result.get('reason')}"],
                "flags_added": [],
                "violations": [v.to_dict() for v in violations],
            }
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
                flags_added.append(v.message)
            elif "HIGH_EC" in v.message:
                flags_added.append("HIGH_EC_WARNING")
            else:
                flags_added.append(v.rule_id)
        return {
            "is_valid": len(blocking) == 0,
            "warnings": warnings,
            "blocking_issues": blocking,
            "flags_added": flags_added,
            "violations": [v.to_dict() for v in violations],
        }

    def _actions_for_ledger_abstain(self, ledger_result: dict) -> list[str]:
        reason = (ledger_result.get("reason") or "").lower()
        if "soil" in reason:
            return ["Upload a current soil test (N, P, K, pH) and re-run."]
        if "crop" in reason:
            return ["Assign an active crop and recommendation type on the field."]
        if "recommendation" in reason:
            return ["Set recommendation_type (e.g. PRE_SEASONAL) on the active crop."]
        return ["Supply the missing agronomic inputs listed in `reason`."]

    def _abstain(
        self,
        conn,
        twin,
        *,
        ledger,
        reason,
        required_actions,
        mode,
        agents_run,
        audit,
        emit_events,
        persist=True,
    ) -> dict:
        twin["confidence"] = "ABSTAIN"
        validation = {
            "is_valid": False,
            "warnings": [],
            "blocking_issues": [reason],
            "flags_added": [],
        }
        proof = assemble_proof(
            status="ABSTAIN",
            ledger={**ledger, "status": "ABSTAIN", "reason": reason},
            twin=twin,
            optimizer_plan=None,
            validation=validation,
            evidence=[],
            mode=mode,
            agents_run=agents_run,
            audit=audit,
            reason=reason,
            required_actions=required_actions,
        )
        rec_id = None
        if persist:
            rec_id = self._persist(conn, proof, previous_plan=None)
        proof["recommendation_id"] = rec_id
        proof["gap"] = ledger.get("gap")
        proof["plan_kg_ha"] = None
        if persist and emit_events:
            self.bus.publish(
                Event.create(
                    EventType.PLAN_CREATED,
                    field_id=int(ledger.get("field_id") or twin.get("field_id") or 0),
                    field_code=str(ledger.get("field_code") or ""),
                    payload={"status": "ABSTAIN", "reason": reason, "recommendation_id": rec_id},
                ),
                conn=conn,
            )
        return proof

    def _persist(
        self,
        conn: sqlite3.Connection,
        proof: dict,
        previous_plan: dict | None,
    ) -> int | None:
        field_id = proof.get("field_id")
        if field_id is None:
            return None
        now = _now()
        if previous_plan and previous_plan.get("recommendation_id"):
            conn.execute(
                """UPDATE recommendations
                   SET status = 'SUPERSEDED', invalidated_at = ?
                   WHERE recommendation_id = ?""",
                (now, previous_plan["recommendation_id"]),
            )
        elif proof.get("mode") == "partial_replan":
            conn.execute(
                """UPDATE recommendations
                   SET status = 'SUPERSEDED', invalidated_at = ?
                   WHERE field_id = ? AND status = 'PROPOSED'""",
                (now, field_id),
            )

        # Reuse ledger write for nutrient_ledger_entries, then overwrite plan_json
        ledger_blob = proof.get("ledger") or {}
        merged = {
            **ledger_blob,
            "field_id": field_id,
            "flags": proof.get("flags") or [],
            "confidence": proof.get("confidence"),
            "optimizer_result": proof.get("optimizer_result"),
            "plan_kg_ha": (proof.get("how_much") or ledger_blob.get("plan_kg_ha") or {}),
            "status": proof.get("status"),
        }
        rec_id = ledger_module.write_ledger_result(conn, merged)
        if rec_id is None:
            rec_id = conn.execute(
                """SELECT recommendation_id FROM recommendations
                   WHERE field_id = ? ORDER BY recommendation_id DESC LIMIT 1""",
                (field_id,),
            ).fetchone()
            rec_id = rec_id["recommendation_id"] if rec_id else None
        if rec_id is not None:
            db_status = "ABSTAINED" if proof.get("status") == "ABSTAIN" else "PROPOSED"
            if proof.get("status") == "NO_FERTILIZER_NEEDED":
                db_status = "NO_FERTILIZER_NEEDED"
            conn.execute(
                """UPDATE recommendations
                   SET plan_json = ?, status = ?, confidence = ?,
                       confidence_reason = ?, evidence_citations = ?, flags = ?,
                       total_cost_estimate = ?
                   WHERE recommendation_id = ?""",
                (
                    json.dumps(proof, default=str),
                    db_status,
                    proof.get("confidence"),
                    proof.get("reason") or "; ".join(proof.get("flags") or []),
                    json.dumps((proof.get("based_on") or {}).get("evidence") or []),
                    json.dumps(proof.get("flags") or []),
                    (proof.get("based_on") or {}).get("cost_estimate"),
                    rec_id,
                ),
            )
            if previous_plan and previous_plan.get("recommendation_id"):
                conn.execute(
                    "UPDATE recommendations SET superseded_by = ? WHERE recommendation_id = ?",
                    (rec_id, previous_plan["recommendation_id"]),
                )
            conn.commit()
        return rec_id


def date_today() -> str:
    from datetime import date

    return date.today().isoformat()
