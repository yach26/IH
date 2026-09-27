"""
Report Agent — farmer / agronomist narrative over a proof-carrying plan.

Does NOT invent kg/ha. Every quantity in the report is copied from the
recommendation object produced by the ledger / optimizer.
"""

from __future__ import annotations

from typing import Any


def compile_report(proof: dict[str, Any]) -> dict[str, Any]:
    """
    Compile a structured, human-readable report from an existing plan.
    Safe to call on ABSTAIN results.
    """
    import json
    try:
        from ..core.llm import generate_chat_completion
    except ImportError:
        generate_chat_completion = None

    status = proof.get("status") or "UNKNOWN"
    how_much = proof.get("how_much")
    flags = list(proof.get("flags") or [])
    why = proof.get("why") or {}
    based = proof.get("based_on") or {}
    evidence = based.get("evidence") or []

    citations = []
    for chunk in evidence:
        if isinstance(chunk, dict):
            citations.append(
                chunk.get("citation")
                or chunk.get("source_file")
                or chunk.get("source")
            )
    citations = [c for c in citations if c]
    if based.get("citation"):
        citations.insert(0, based["citation"])

    if status == "ABSTAIN":
        summary = (
            "A reliable fertilizer plan cannot currently be produced. "
            + (proof.get("reason") or "")
        ).strip()
    elif status == "NO_FERTILIZER_NEEDED":
        summary = "Soil nutrient status already meets the RDF requirement. No fertilizer is recommended."
    elif status == "PLAN_REVISED":
        summary = (
            f"Revised plan: apply {proof.get('what')} "
            f"in window {proof.get('when')}. Quantities unchanged from the ledger."
        )
    else:
        summary = (
            f"Recommended {proof.get('what')} totalling "
            f"{_total_kg(how_much)} kg/ha. Apply {proof.get('when')}."
        )

    narrative = ""
    if generate_chat_completion:
        try:
            # We explicitly instruct the LLM NOT to alter quantities.
            prompt = f"Explain the following fertilizer recommendation to a farmer in simple, encouraging terms. Emphasize why these quantities were chosen. Do NOT change the quantities or recommend different fertilizers.\n\nPlan Details: {json.dumps(proof, indent=2)}"
            messages = [
                {"role": "system", "content": "You are a helpful agricultural advisor explaining a strictly calculated fertilizer plan."},
                {"role": "user", "content": prompt}
            ]
            narrative = generate_chat_completion(messages)
        except Exception as e:
            narrative = f"Narrative generation failed: {str(e)}"

    return {
        "status": status,
        "headline": summary,
        "what": proof.get("what"),
        "how_much": how_much,
        "when": proof.get("when"),
        "why": why,
        "confidence": proof.get("confidence"),
        "flags": flags,
        "narrative": narrative,
        "data_quality": proof.get("data_quality") or {},
        "citations": citations,
        "required_actions": proof.get("required_actions") or [],
        "numeric_source": proof.get("numeric_source")
        or "ledger.convert_gap_to_products (HeuristicOptimizer)",
        "disclaimer": (
            "Quantities (kg/ha) originate only from the Nutrient Ledger heuristic "
            "(DAP→Urea→MOP) and FCO product compositions. This report does not "
            "calculate or alter any numbers."
        ),
        "field_id": proof.get("field_id"),
        "field_code": proof.get("field_code"),
        "recommendation_id": proof.get("recommendation_id"),
    }


def _total_kg(how_much: dict | None) -> float:
    if not how_much:
        return 0.0
    return round(
        sum(
            float(v)
            for k, v in how_much.items()
            if str(k).endswith("_kg_ha") and not str(k).startswith("n_supplied")
        ),
        1,
    )
