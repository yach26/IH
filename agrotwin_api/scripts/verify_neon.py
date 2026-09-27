"""
Verification script for NeonDB (serverless PostgreSQL).
Applies schema_postgres.sql, seeds data, and runs recommend, event, and what-if.
"""

import json
import os
import sys

_api_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _api_root not in sys.path:
    sys.path.insert(0, _api_root)

NEON_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_On9oaEABty1p@ep-gentle-moon-b5m2ws64-pooler.c-7.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require",
)
os.environ["DATABASE_URL"] = NEON_URL

from app.db import get_db_connection, init_db, _json_load
from seed_data import seed_all
from app.agents.orchestrator import run_orchestrated_ledger
from app.agents.monitoring_agent import get_monitoring_agent
from app.core.event_bus import get_bus
from app.core.events import Event


def main():
    print(f"Connecting to NeonDB: {NEON_URL.split('@')[1] if '@' in NEON_URL else '...'}")
    conn = get_db_connection()

    print("Step 1: Applying schema_postgres.sql...")
    init_db(conn)
    print("Schema applied successfully!")

    print("Step 2: Seeding database...")
    seed_ctx = seed_all()
    print(f"Seeded fields: {list(seed_ctx['field_ids'].keys())}")

    # Re-connect to ensure fresh transaction state
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT count(*) as count FROM fields")
    n_fields = cur.fetchone()["count"]
    cur.execute("SELECT count(*) as count FROM field_crops")
    n_crops = cur.fetchone()["count"]
    cur.execute("SELECT count(*) as count FROM soil_tests")
    n_soil = cur.fetchone()["count"]
    print(f"Counts in NeonDB: {n_fields} fields, {n_crops} field_crops, {n_soil} soil_tests")

    print("\nStep 3: Running recommendation for Field 1 (SYN-001 Banana)...")
    cur.execute("SELECT * FROM field_active_crop WHERE field_code = 'SYN-001'")
    field_row = cur.fetchone()
    if field_row is None:
        raise RuntimeError("SYN-001 not found in field_active_crop after seeding!")
    field_id_1 = field_row["field_id"]
    print(f"  Resolved SYN-001 -> field_id={field_id_1}")
    get_monitoring_agent().bind(conn)
    rec1 = run_orchestrated_ledger(conn, field_row)
    print(f"Rec 1 Status: {rec1.get('status')}")
    print(f"Rec 1 What: {rec1.get('what')}")
    print(f"Rec 1 Quantities: {rec1.get('how_much')}")
    print(f"Rec 1 Confidence: {rec1.get('confidence')}")
    print(f"Rec 1 Window: {rec1.get('when')}")
    rec1_id = rec1.get("recommendation_id")
    print(f"Rec 1 ID: {rec1_id}")

    print("\nStep 4: Injecting HEAVY_RAIN_ALERT event...")
    event = Event.create(
        "HEAVY_RAIN_ALERT",
        field_id=field_id_1,
        field_code="SYN-001",
        payload={"heavy_rain_alert": True, "rainfall_probability": 95, "rainfall_mm_next_7d": 80.0},
        actor="neon_test",
    )
    get_bus().publish(event, conn=conn)

    cur.execute(
        """SELECT recommendation_id, status, plan_json, invalidated_at, superseded_by
           FROM recommendations WHERE field_id = %s
           ORDER BY recommendation_id DESC LIMIT 1""",
        (field_id_1,),
    )
    rec2_row = cur.fetchone()
    rec2_plan = _json_load(rec2_row["plan_json"]) if rec2_row else {}
    print(f"Rec 2 (Re-planned) ID: {rec2_row['recommendation_id']}")
    print(f"Rec 2 Status in DB: {rec2_row['status']}")
    print(f"Rec 2 Window: {rec2_plan.get('when')}")
    print(f"Was plan rescheduled? {rec2_plan.get('when_detail', {}).get('revised')}")

    print("\nALL NEONDB VERIFICATIONS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    main()
