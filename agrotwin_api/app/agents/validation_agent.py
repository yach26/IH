"""
Validation Agent — multi-context plausibility checks (Phase-2).

Responsibility:
  - Takes the outputs from the Ledger (nutrient gaps) and contexts
    (Weather, Soil, Crop).
  - Evaluates cross-cutting agronomic constraints (e.g., weather conflicts,
    extreme soil pH).
  - Returns a structured validation result (is_valid, warnings, blocking_issues).
  - Also surfaces new flags to append to the ledger result.

ENGINEERING_DEFAULT Rules (Gap #6):
  1. WEATHER_CONFLICT: Block soluble N application if a HEAVY_RAIN_ALERT
     is active (leaching risk).
  2. HIGH_PH_WARNING: Warn if soil pH > 8.0 (nutrient lockout risk).
"""


def validate_ledger_result(
    ledger_result: dict,
    soil_context: dict | None,
    weather_context: dict | None,
) -> dict:
    """
    Evaluates cross-agent constraints.
    Returns: {"is_valid": bool, "warnings": list, "blocking_issues": list, "flags_added": list}
    """
    is_valid = True
    warnings = []
    blocking_issues = []
    flags_added = []

    # If ledger already abstained (e.g., no soil test), skip deeper checks
    if ledger_result.get("status") == "ABSTAIN":
        return {
            "is_valid": False,
            "warnings": [],
            "blocking_issues": [f"LEDGER_ABSTAIN: {ledger_result.get('reason')}"],
            "flags_added": [],
        }

    # 1. Weather Conflict Check (ENGINEERING_DEFAULT)
    # If heavy rain is expected, applying soluble fertilizers (like Urea/N) is wasteful
    # and environmentally harmful due to leaching/runoff.
    gap = ledger_result.get("gap", {})
    if weather_context and weather_context.get("heavy_rain_alert"):
        if gap.get("N", 0) > 0:
            is_valid = False
            msg = (
                "WEATHER_CONFLICT: HEAVY_RAIN_ALERT active. Applying soluble nitrogen "
                "in this window risks significant N leaching/runoff. Reschedule "
                "application after rain window. "
                f"{weather_context.get('alert_details')} "
                "[ENGINEERING_DEFAULT rule — see validation_agent.py docstring]"
            )
            blocking_issues.append(msg)
            flags_added.append("WEATHER_CONFLICT")

    # 2. Soil pH Plausibility Check
    if soil_context and soil_context.get("ph") is not None:
        ph = float(soil_context["ph"])
        if ph > 8.0:
            warnings.append(
                f"HIGH_PH_WARNING (pH {ph}): Risk of micronutrient lockout and "
                "reduced P availability. Consider soil amendments."
            )
            flags_added.append("HIGH_PH_WARNING")
        elif ph < 5.5:
            warnings.append(
                f"LOW_PH_WARNING (pH {ph}): Risk of Al toxicity and reduced "
                "base cation availability. Consider liming."
            )
            flags_added.append("LOW_PH_WARNING")

    # 3. Gap Plausibility (detect massive accidental over-application in history)
    # If gap is deeply negative (e.g., applied 500kg N when 100 was needed)
    if gap.get("N", 0) < -100 or gap.get("P2O5", 0) < -100 or gap.get("K2O", 0) < -100:
        warnings.append(
            "SEVERE_OVER_APPLICATION: The ledger shows one or more nutrients "
            "exceeding requirement by > 100 kg/ha. Verify application records."
        )
        flags_added.append("SEVERE_OVER_APPLICATION")

    return {
        "is_valid": is_valid,
        "warnings": warnings,
        "blocking_issues": blocking_issues,
        "flags_added": flags_added,
    }
