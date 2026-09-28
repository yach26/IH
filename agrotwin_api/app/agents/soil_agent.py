"""
Soil Agent — wraps all soil_tests reads/writes and staleness logic.

Responsibility:
  - Fetch the latest soil test for a field.
  - Determine whether the soil data is "stale".
  - Surface a structured SoilContext dict used by the orchestrator.
  - Flag: STALE_SOIL_DATA when the soil test is older than STALE_DAYS.
  - ABSTAIN signal when no soil test exists at all (returns None context).

Staleness threshold: 180 days.
Rationale (ENGINEERING_DEFAULT — no agronomic source backs this exact number):
  Soil NPK status can shift meaningfully within a single growing season
  (≈ 120–180 days for kharif crops). The 180-day cut-off is a conservative
  engineering default ensuring at minimum the test post-dates the previous
  season's harvest. A more rigorous agronomic threshold would require
  published SHC re-testing frequency guidance from MoA/NHM — not yet
  sourced (Gap #2 in 04_remaining_gaps.md). This default will be replaced
  when such guidance is available.
"""

import sqlite3
from datetime import date, timedelta

# -----------------------------------------------------------------------
# ENGINEERING_DEFAULT: stale-soil threshold = 180 days
# See module docstring for full rationale.
# -----------------------------------------------------------------------
STALE_SOIL_DAYS = 180


def get_soil_context(conn: sqlite3.Connection, field_id: int) -> dict | None:
    """
    Returns a SoilContext dict or None (ABSTAIN signal) if no soil test exists.

    SoilContext keys:
      soil_test_id, test_date, n_kg_ha, p_kg_ha, k_kg_ha,
      ph, oc_percent, ec_ds_m, source, is_synthetic,
      is_stale (bool), days_since_test (int), flags (list[str])
    """
    row = conn.execute(
        """SELECT * FROM soil_tests WHERE field_id = ?
           ORDER BY test_date DESC, soil_test_id DESC LIMIT 1""",
        (field_id,),
    ).fetchone()

    if row is None:
        return None  # ABSTAIN — caller must handle

    ctx = dict(row)
    flags: list[str] = []

    # Staleness check
    try:
        test_date = date.fromisoformat(str(ctx["test_date"]))
        days_since = (date.today() - test_date).days
    except (ValueError, TypeError):
        days_since = None
        flags.append("SOIL_DATE_UNKNOWN: freshness cannot be verified")

    ctx["days_since_test"] = days_since
    ctx["is_stale"] = days_since is None or days_since < 0 or days_since > STALE_SOIL_DAYS

    if ctx["is_stale"]:
        flags.append(
            f"STALE_SOIL_DATA (test is {days_since} days old; "
            f"ENGINEERING_DEFAULT threshold = {STALE_SOIL_DAYS} days — "
            f"replace when MoA/NHM re-testing frequency guidance is sourced)"
        )

    ctx["flags"] = flags
    return ctx


def write_soil_test(
    conn: sqlite3.Connection,
    field_id: int,
    test_date: str,
    n_kg_ha: float,
    p_kg_ha: float,
    k_kg_ha: float,
    ph: float | None = None,
    oc_percent: float | None = None,
    ec_ds_m: float | None = None,
    source: str = "API",
    is_synthetic: bool = False,
    label_note: str | None = None,
) -> int:
    """Inserts a soil test; returns the new soil_test_id."""
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO soil_tests
           (field_id, test_date, n_kg_ha, p_kg_ha, k_kg_ha, ph, oc_percent,
            ec_ds_m, source, is_synthetic, label_note)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (field_id, test_date, n_kg_ha, p_kg_ha, k_kg_ha,
         ph, oc_percent, ec_ds_m, source, is_synthetic, label_note),
    )
    conn.commit()
    return cur.lastrowid
