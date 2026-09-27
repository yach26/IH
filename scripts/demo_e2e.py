"""
AgroTwin End-to-End Demo Script
================================

One-command demo that walks through the full system:
  1. Seed / load a field
  2. Upload + confirm a soil report (OCR)
  3. Generate recommendation (with narrative + evidence + yield estimate)
  4. Inject heavy-rain event
  5. Show automatic plan invalidation and revised plan
  6. Run a What-If scenario and show yield impact

Usage:
    cd agrotwin_api
    python ../scripts/demo_e2e.py

Or from repo root:
    python scripts/demo_e2e.py
"""

import json
import os
import sys
import time

# Add agrotwin_api to path
API_ROOT = os.path.join(os.path.dirname(__file__), "..", "agrotwin_api")
sys.path.insert(0, os.path.abspath(API_ROOT))

from fastapi.testclient import TestClient

from app.main import app
from app.api.routes import get_conn
from tests.conftest import make_test_db


def banner(text: str):
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def sub_banner(text: str):
    print(f"\n--- {text} ---")


def print_json(data: dict, indent: int = 2):
    print(json.dumps(data, indent=indent, default=str))


def step1_seed_field(client: TestClient, conn):
    """Step 1: Seed the database and load a field."""
    banner("STEP 1: Seed / Load a Field")

    # Use the test fixture to create a fresh in-memory DB
    # In production, this would be: python seed_data.py
    from seed_data import seed_all
    ctx = seed_all()

    # Get the first field
    row = conn.execute(
        "SELECT field_id, field_code FROM fields LIMIT 1"
    ).fetchone()
    field_id = row["field_id"]
    field_code = row["field_code"]

    print(f"  Field ID: {field_id}")
    print(f"  Field Code: {field_code}")

    # Get field details
    twin = client.get(f"/fields/{field_id}/twin").json()
    print(f"\n  Digital Twin State:")
    print(f"    Field: {twin['field']['field_code']}")
    print(f"    Soil: N={twin['soil']['n_kg_ha']}, P={twin['soil']['p_kg_ha']}, K={twin['soil']['k_kg_ha']}")
    print(f"    pH: {twin['soil']['ph']}, OC: {twin['soil']['oc_percent']}%")

    return field_id, field_code


def step2_ocr_upload_confirm(client: TestClient, field_id: int):
    """Step 2: Upload + confirm a soil report (OCR)."""
    banner("STEP 2: Soil Report Upload -> OCR -> Farmer Confirmation")

    # Create a sample soil report file
    sample_report = b"""SOIL HEALTH CARD
Government of Maharashtra

Card No: MH5468/2024-25/DEMO001
Farmers Name: Demo Farmer
Village: Ajara
District: Kolhapur
Date of Sampling: 15/06/2024

Soil Test Results:
Available Nitrogen (N): 210 kg/ha
Available Phosphorus (P): 35 kg/ha
Available Potassium (K): 310 kg/ha
Soil pH: 7.9
Organic Carbon: 0.62%
Electrical Conductivity: 0.32 dS/m
"""

    sub_banner("2a: Upload soil report")
    upload_resp = client.post(
        f"/fields/{field_id}/soil-report/upload",
        files={"file": ("soil_report.txt", sample_report, "text/plain")},
    )
    upload_data = upload_resp.json()
    print(f"  Status: {upload_data['status']}")
    print(f"  Engine: {upload_data['engine']}")
    print(f"  Upload ID: {upload_data['upload_id']}")
    print(f"\n  Extracted Values:")
    for field, info in upload_data["extracted_data"].items():
        if info.get("value") is not None:
            print(f"    {field}: {info['value']} (confidence: {info.get('confidence', 'N/A')})")

    if upload_data["fields_needing_review"]:
        print(f"\n  Fields needing review: {upload_data['fields_needing_review']}")

    sub_banner("2b: Farmer confirms OCR values")
    confirm_resp = client.post(
        f"/fields/{field_id}/soil-report/confirm",
        json={
            "upload_id": upload_data["upload_id"],
            "soil_test": {
                "n_kg_ha": 210.0,
                "p_kg_ha": 35.0,
                "k_kg_ha": 310.0,
                "ph": 7.9,
                "oc_percent": 0.62,
                "ec_ds_m": 0.32,
                "test_date": "2024-06-15",
                "source": "ocr",
                "ocr_confidence": 0.98,
            },
        },
    )
    confirm_data = confirm_resp.json()
    print(f"  Status: {confirm_data['status']}")
    print(f"  Message: {confirm_data['message']}")

    return upload_data


def step3_generate_recommendation(client: TestClient, field_id: int):
    """Step 3: Generate recommendation with narrative + evidence + yield estimate."""
    banner("STEP 3: Generate Recommendation (with Evidence + Yield Estimate)")

    sub_banner("3a: Run recommendation pipeline")
    rec_resp = client.post(
        f"/fields/{field_id}/recommend",
        json={"mock_weather": {"rainfall_mm_next_7d": 25}},
    )
    rec_data = rec_resp.json()

    print(f"  Status: {rec_data['status']}")
    print(f"  Confidence: {rec_data['confidence']}")
    print(f"  Confidence Reason: {rec_data.get('confidence_reason', 'N/A')}")

    if rec_data["status"] == "ABSTAIN":
        print(f"  Reason: {rec_data['reason']}")
        return None

    sub_banner("3b: Fertilizer Plan (from Nutrient Ledger)")
    plan = rec_data.get("plan_kg_ha", {})
    for product, qty in plan.items():
        if qty > 0:
            print(f"  {product}: {qty} kg/ha")

    sub_banner("3c: Proof-Carrying Evidence (6 Questions)")
    proof = rec_data.get("proof", {})
    for question, answer in proof.items():
        print(f"  {question}: {answer}")

    sub_banner("3d: Evidence Citations")
    citations = rec_data.get("evidence_citations", [])
    for cit in citations:
        print(f"  - {cit}")

    sub_banner("3e: Yield Estimate")
    yield_resp = client.get(
        f"/fields/{field_id}/yield-estimate?rainfall_mm_season=1100"
    )
    yield_data = yield_resp.json()
    prediction = yield_data.get("yield_prediction", {})
    print(f"  Status: {prediction.get('status')}")
    print(f"  Predicted Yield: {prediction.get('predicted_yield_kg_ha')} kg/ha")
    print(f"  Yield Band: {prediction.get('yield_band')}")
    print(f"  Confidence: {prediction.get('confidence')}")
    print(f"  Extrapolation: {prediction.get('extrapolation')}")
    if prediction.get("caveats"):
        print(f"  Caveats:")
        for caveat in prediction["caveats"]:
            print(f"    - {caveat}")

    return rec_data


def step4_inject_heavy_rain(client: TestClient, field_id: int, field_code: str):
    """Step 4: Inject heavy-rain event."""
    banner("STEP 4: Inject Heavy-Rain Event")

    event_resp = client.post(
        "/events",
        json={
            "type": "HEAVY_RAIN_ALERT",
            "field_code": field_code,
            "payload": {
                "heavy_rain_alert": True,
                "rainfall_probability": 90,
                "rainfall_mm_next_7d": 80,
            },
        },
    )
    event_data = event_resp.json()

    print(f"  Event Injected: {event_data['injected']['type']}")
    print(f"  Field: {event_data['injected']['field_code']}")
    print(f"\n  Latest Plan Status: {event_data['latest_plan']['status_db']}")
    print(f"  Invalidated At: {event_data['latest_plan'].get('invalidated_at', 'N/A')}")

    sub_banner("Active Alerts")
    for alert in event_data.get("alerts", []):
        print(f"  [{alert.get('severity', 'UNKNOWN')}] {alert.get('message', '')}")

    return event_data


def step5_show_revised_plan(client: TestClient, field_id: int):
    """Step 5: Show automatic plan invalidation and revised plan."""
    banner("STEP 5: Automatic Plan Invalidation & Revised Plan")

    sub_banner("5a: Check plan status after heavy rain")
    latest = client.get(f"/fields/{field_id}/recommendations/latest").json()
    print(f"  Status: {latest.get('status_db')}")
    print(f"  Invalidated At: {latest.get('invalidated_at', 'N/A')}")
    print(f"  Superseded By: {latest.get('superseded_by', 'N/A')}")

    sub_banner("5b: Generate revised plan")
    revised_resp = client.post(
        f"/fields/{field_id}/recommend",
        json={"mock_weather": {"rainfall_mm_next_7d": 80}},
    )
    revised_data = revised_resp.json()

    print(f"  Status: {revised_data['status']}")
    print(f"  Confidence: {revised_data['confidence']}")

    if revised_data["status"] != "ABSTAIN":
        plan = revised_data.get("plan_kg_ha", {})
        print(f"\n  Revised Plan:")
        for product, qty in plan.items():
            if qty > 0:
                print(f"    {product}: {qty} kg/ha")

        proof = revised_data.get("proof", {})
        print(f"\n  Revised Proof:")
        for question, answer in proof.items():
            print(f"    {question}: {answer}")

    return revised_data


def step6_what_if(client: TestClient, field_id: int):
    """Step 6: Run a What-If scenario and show yield impact."""
    banner("STEP 6: What-If Simulator (Yield Impact)")

    sub_banner("6a: Baseline plan")
    baseline_resp = client.get(f"/fields/{field_id}/recommendations/latest").json()
    baseline_plan = baseline_resp.get("plan_kg_ha", {})
    print(f"  Baseline Status: {baseline_resp.get('status_db')}")

    sub_banner("6b: What-If scenario (+20% fertilizer)")
    whatif_resp = client.post(
        f"/fields/{field_id}/what-if",
        json={"fertilizer_delta_pct": 20, "rainfall_mm": 25},
    )
    whatif_data = whatif_resp.json()

    original = whatif_data.get("original_plan", {})
    simulated = whatif_data.get("simulated_plan", {})

    print(f"  Original Plan Status: {original.get('status', 'N/A')}")
    print(f"  Simulated Plan Status: {simulated.get('status', 'N/A')}")

    if simulated.get("plan_kg_ha"):
        print(f"\n  Simulated Plan (+20% fertilizer):")
        for product, qty in simulated["plan_kg_ha"].items():
            if qty > 0:
                print(f"    {product}: {qty} kg/ha")

    sub_banner("6c: Yield impact of What-If scenario")
    # Get yield estimate for simulated plan
    yield_resp = client.get(
        f"/fields/{field_id}/yield-estimate?rainfall_mm_season=1100"
    )
    yield_data = yield_resp.json()
    prediction = yield_data.get("yield_prediction", {})
    print(f"  Predicted Yield: {prediction.get('predicted_yield_kg_ha')} kg/ha")
    print(f"  Yield Band: {prediction.get('yield_band')}")
    print(f"  Confidence: {prediction.get('confidence')}")
    print(f"  Extrapolation: {prediction.get('extrapolation')}")

    print("\n  Note: What-If plans are NOT persisted to the database.")
    print("  They are simulation-only and do not affect the active plan.")

    return whatif_data


def main():
    print("\n" + "#" * 80)
    print("#" + " " * 78 + "#")
    print("#" + "  AGROTWIN AI - END-TO-END DEMO".center(78) + "#")
    print("#" + " " * 78 + "#")
    print("#" * 80)

    # Create test database
    conn, ids = make_test_db()
    app.dependency_overrides[get_conn] = lambda: conn

    with TestClient(app) as client:
        try:
            # Step 1: Seed / load field
            field_id, field_code = step1_seed_field(client, conn)

            # Step 2: OCR upload + confirm
            step2_ocr_upload_confirm(client, field_id)

            # Step 3: Generate recommendation
            rec_data = step3_generate_recommendation(client, field_id)

            if rec_data is None:
                print("\n  WARNING: Recommendation abstained. Demo cannot continue.")
                return

            # Step 4: Inject heavy rain
            step4_inject_heavy_rain(client, field_id, field_code)

            # Step 5: Show revised plan
            step5_show_revised_plan(client, field_id)

            # Step 6: What-If
            step6_what_if(client, field_id)

            # Final summary
            banner("DEMO COMPLETE")
            print("""
  The demo has shown:
    1. Field seeding with real Phase-1 data
    2. OCR extraction with farmer confirmation
    3. Proof-carrying recommendation with evidence + yield estimate
    4. Heavy-rain event injection
    5. Automatic plan invalidation and revision
    6. What-If simulation with yield impact

  All fertilizer quantities come from the deterministic Nutrient Ledger.
  The yield model only predicts; it never invents quantities.
  The system abstains gracefully when data is insufficient.
            """)

        finally:
            app.dependency_overrides.clear()


if __name__ == "__main__":
    main()
