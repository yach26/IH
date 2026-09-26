"""
Crop Agent — wraps crop state reads and crop_calendar lookups.

Responsibility:
  - Fetch the field's current crop state (crop_id, crop_code, variety,
    sowing_date, current_stage, recommendation_type).
  - Validate the declared stage against the crop calendar.
  - Surface a structured CropContext dict used by the orchestrator.
  - ABSTAIN signal if no crop/recommendation_type is set (returns None).
  - Flag: STAGE_NOT_IN_CALENDAR if the declared stage doesn't match
    any calendar entry for this crop (informational, not blocking).

This agent never calculates fertilizer quantities.
"""

import sqlite3


def get_crop_context(conn: sqlite3.Connection, field_row: sqlite3.Row) -> dict | None:
    """
    Returns a CropContext dict or None (ABSTAIN) if crop/rec_type is missing.

    CropContext keys:
      crop_id, crop_code, crop_name, current_variety, sowing_date,
      current_stage, recommendation_type, calendar_entries (list),
      stage_valid (bool), flags (list[str])
    """
    if field_row["current_crop_id"] is None or field_row["recommendation_type"] is None:
        return None  # ABSTAIN

    crop = conn.execute(
        "SELECT crop_id, crop_code, crop_name FROM crops WHERE crop_id = ?",
        (field_row["current_crop_id"],),
    ).fetchone()

    if crop is None:
        return None  # defensive

    calendar_entries = conn.execute(
        """SELECT stage_name, stage_order,
                  days_after_planting_min, days_after_planting_max, notes
           FROM crop_calendars
           WHERE crop_id = ?
           ORDER BY stage_order""",
        (crop["crop_id"],),
    ).fetchall()

    flags: list[str] = []
    stage_valid = True
    declared_stage = field_row["current_stage"]

    # Validate declared stage against calendar entries (if calendar exists)
    if calendar_entries and declared_stage:
        known_stages = {r["stage_name"].upper() for r in calendar_entries}
        if declared_stage.upper() not in known_stages:
            stage_valid = False
            flags.append(
                f"STAGE_NOT_IN_CALENDAR (declared stage '{declared_stage}' "
                f"not in crop calendar for {crop['crop_code']}; "
                f"known stages: {', '.join(sorted(known_stages))})"
            )

    return {
        "crop_id": crop["crop_id"],
        "crop_code": crop["crop_code"],
        "crop_name": crop["crop_name"],
        "current_variety": field_row["current_variety"],
        "sowing_date": field_row["sowing_date"],
        "current_stage": declared_stage,
        "recommendation_type": field_row["recommendation_type"],
        "calendar_entries": [dict(e) for e in calendar_entries],
        "stage_valid": stage_valid,
        "flags": flags,
    }


def get_days_after_planting(sowing_date_str: str | None) -> int | None:
    """Returns days after planting from sowing_date to today, or None."""
    if not sowing_date_str:
        return None
    from datetime import date
    try:
        sd = date.fromisoformat(str(sowing_date_str))
        return (date.today() - sd).days
    except (ValueError, TypeError):
        return None
