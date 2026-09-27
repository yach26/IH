import sys
sys.path.insert(0, ".")
import json
import sqlite3
import sys
from fastapi.testclient import TestClient

from app.main import app
from app.db import get_db_connection
from tests.conftest import make_test_db
from app.agents import knowledge_agent, soil_report_agent

PASS = 0
FAIL = 0

def check(label: str, ok: bool, detail: str = ""):
    global PASS, FAIL
    sym = "PASS" if ok else "FAIL"
    print(f"  [{sym}] {label}" + (f"  ({detail})" if detail else ""))
    if ok:
        PASS += 1
    else:
        FAIL += 1

# Maintain a single connection for the test
_conn = make_test_db()
app.dependency_overrides[get_db_connection] = lambda: _conn
client = TestClient(app)

def make_db():
    return _conn

def setup_data():
    fid = 1
    # Deactivate previous crop if any, just assign Banana
    client.post(f"/fields/{fid}/crop", json={
        "crop_code": "BANANA", "variety": "Grand Naine",
        "sowing_date": "2024-01-01", "current_stage": "VEGETATIVE",
        "recommendation_type": "PRE_SEASONAL", "target_yield_kg_ha": 60000
    })
    return fid

def verify_rag():
    print("\n§P3-1: RAG internals pipeline")
    conn = make_db()
    fid = setup_data()
    evidence = knowledge_agent.retrieve_evidence("BANANA", "KOL", "PRE_SEASONAL")
    check("RAG returns evidence list", isinstance(evidence, list), f"len={len(evidence)}")
    if evidence:
        check("evidence has content and confidence", "content" in evidence[0] and "confidence" in evidence[0], f"keys={list(evidence[0].keys())}")
        check("BM25 score present (metadata)", "score" in evidence[0].get("metadata", {}), "")
    else:
        check("evidence has content and confidence", False, "No evidence returned")

def verify_ocr():
    print("\n§P3-2: OCR extraction accuracy (Deterministic Regex Fallback)")
    conn = make_db()
    fid = setup_data()
    sample_text = b"Nitrogen: 125.5 kg/ha\nPhosphorus = 45\nAvailable Potassium 80 kg\npH 7.2\nOrganic Carbon: 0.65%"
    res = soil_report_agent.process_upload(conn, fid, "sample_report.txt", sample_text)
    
    check("upload gets an upload_id", "upload_id" in res, res.get("upload_id"))
    check("extraction engine used", res.get("engine") == "regex_text", res.get("engine"))
    
    extracted = res.get("extracted", {})
    check("Nitrogen extracted correctly", extracted.get("n_kg_ha", {}).get("value") == 125.5, extracted.get("n_kg_ha"))
    check("Phosphorus extracted correctly", extracted.get("p_kg_ha", {}).get("value") == 45.0, extracted.get("p_kg_ha"))
    check("Potassium extracted correctly", extracted.get("k_kg_ha", {}).get("value") == 80.0, extracted.get("k_kg_ha"))
    check("pH extracted correctly", extracted.get("ph", {}).get("value") == 7.2, extracted.get("ph"))
    check("OC extracted correctly", extracted.get("oc_percent", {}).get("value") == 0.65, extracted.get("oc_percent"))

def verify_what_if():
    print("\n§P3-3: What-If optimizer re-run behavior")
    conn = make_db()
    fid = setup_data()
    # Add soil test and get baseline
    client.post(f"/fields/{fid}/soil-report/upload", files={"file": ("r.txt", b"N: 100\nP: 30\nK: 50")})
    client.post(f"/fields/{fid}/soil-report/1/confirm", json={"n_kg_ha": 100, "p_kg_ha": 30, "k_kg_ha": 50})
    client.post("/recommend", json={"field_id": fid})
    
    # What-If with delta +10%
    res = client.post(f"/fields/{fid}/what-if", json={"fertilizer_delta_pct": 10.0, "rainfall_mm": 50})
    check("What-If endpoint 200 OK", res.status_code == 200, res.status_code)
    
    data = res.json()
    check("simulated plan returned", "simulated_plan" in data, "")
    sim = data.get("simulated_plan", {})
    check("simulated plan has optimizer scaling", sim.get("how_much") is not None, "")

def verify_db_fk():
    print("\n§P3-4: DB Constraint Audit")
    conn = make_db()
    setup_data()
    violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    check("Foreign Key constraints are valid (no violations)", len(violations) == 0, f"{len(violations)} violations")

if __name__ == "__main__":
    verify_rag()
    verify_ocr()
    verify_what_if()
    verify_db_fk()
    
    print("\n" + "=" * 60)
    print(f"Phase 3 verification: {PASS} PASSED, {FAIL} FAILED")
    if FAIL > 0:
        print(f"WARNING: {FAIL} check(s) failed — review above")
        sys.exit(1)
    else:
        print("ALL PHASE 3 VERIFICATIONS PASSED")
        sys.exit(0)
