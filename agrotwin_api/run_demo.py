"""
End-to-end run: seed -> compute ledger for every field -> write
nutrient_ledger_entries + recommendations rows back into the twin ->
export a results table.

This replaces the hand-worked markdown table in
11_Digital_Twin_Schema/03_run_against_synthetic_records.md with an
actual executable pipeline against the same 8 synthetic records,
now including Banana (previously ABSTAIN due to a missed cross-reference
to the density figure in 05_Crop_Calendars).
"""

import sqlite3
import json
import csv
import os

from seed_data import seed_all, RECOMMENDATION_TYPE_BY_RECORD
from ledger import run_field

OUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUT_DIR, exist_ok=True)


def write_back(conn, result):
    cur = conn.cursor()
    if result["status"] == "ABSTAIN":
        cur.execute(
            """INSERT INTO recommendations (field_id, plan_json, confidence,
               confidence_reason, evidence_citations, is_synthetic, status)
               VALUES (?,?,?,?,?,?,?)""",
            (result.get("field_id"), json.dumps({}), "ABSTAIN",
             result["reason"], json.dumps(result["flags"]), 1, "ABSTAINED"),
        )
        conn.commit()
        return

    cur.execute(
        """INSERT INTO nutrient_ledger_entries
           (field_id, crop_id, current_stage, required_n_kg_ha, required_p2o5_kg_ha,
            required_k2o_kg_ha, required_source, soil_n_kg_ha, soil_p_kg_ha, soil_k_kg_ha,
            gap_n_kg_ha, gap_p2o5_kg_ha, gap_k2o_kg_ha, calculation_notes, is_synthetic)
           VALUES (?, (SELECT crop_id FROM crops WHERE crop_code=?), ?, ?,?,?,?,?,?,?,?,?,?,?,?)""",
        (result["field_id"], result["crop"], result["current_stage"],
         result["required"]["N"], result["required"]["P2O5"], result["required"]["K2O"],
         result["citation"], result["soil"]["N"], result["soil"]["P_proxy"], result["soil"]["K"],
         result["gap"]["N"], result["gap"]["P2O5"], result["gap"]["K2O"],
         "; ".join(result["flags"]), 1),
    )
    ledger_id = cur.lastrowid

    cur.execute(
        """INSERT INTO recommendations
           (field_id, ledger_id, plan_json, confidence, confidence_reason,
            evidence_citations, is_synthetic, status)
           VALUES (?,?,?,?,?,?,?,?)""",
        (result["field_id"], ledger_id, json.dumps(result["plan_kg_ha"]),
         result["confidence"], "; ".join(result["flags"]),
         json.dumps([result["citation"]]), 1, "PROPOSED"),
    )
    conn.commit()


def main():
    ctx = seed_all()
    conn = sqlite3.connect(ctx["db_path"])
    conn.execute("PRAGMA foreign_keys = ON")

    results = []
    for record_id, meta in ctx["field_ids"].items():
        result = run_field(conn, meta["field_id"], meta, RECOMMENDATION_TYPE_BY_RECORD)
        write_back(conn, result)
        results.append(result)

    conn.close()

    # ---- console report ----
    print("\n" + "=" * 100)
    print("AGROTWIN NUTRIENT LEDGER — LIVE RUN AGAINST 8 SYNTHETIC RECORDS (real code, not markdown)")
    print("=" * 100)
    for r in results:
        print(f"\n{r['record_id']} | {r['crop']} ({r.get('recommendation_type','-')}) | "
              f"stage: {r.get('current_stage','-')}")
        if r["status"] == "ABSTAIN":
            print(f"  STATUS: ABSTAIN — {r['reason']}")
            continue
        print(f"  Required (kg/ha):  N={r['required']['N']}  P2O5={r['required']['P2O5']}  K2O={r['required']['K2O']}")
        print(f"  Soil (kg/ha):      N={r['soil']['N']}  P(proxy)={r['soil']['P_proxy']}  K={r['soil']['K']}")
        print(f"  Gap (kg/ha):       N={r['gap']['N']}  P2O5={r['gap']['P2O5']}  K2O={r['gap']['K2O']}")
        print(f"  Plan (kg/ha):      DAP={r['plan_kg_ha']['DAP_kg_ha']}  "
              f"Urea={r['plan_kg_ha']['UREA_kg_ha']}  MOP={r['plan_kg_ha']['MOP_kg_ha']}")
        print(f"  Status: {r['status']}   Confidence: {r['confidence']}")
        print(f"  Flags: {r['flags']}")
        print(f"  Citation: {r['citation']}")

    # ---- CSV export ----
    csv_path = os.path.join(OUT_DIR, "ledger_results.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["record_id", "crop", "rec_type", "stage", "status", "confidence",
                    "required_N", "required_P2O5", "required_K2O",
                    "soil_N", "soil_P_proxy", "soil_K",
                    "gap_N", "gap_P2O5", "gap_K2O",
                    "DAP_kg_ha", "Urea_kg_ha", "MOP_kg_ha",
                    "flags", "citation"])
        for r in results:
            if r["status"] == "ABSTAIN":
                w.writerow([r["record_id"], r["crop"], "-", "-", "ABSTAIN", "-",
                            "", "", "", "", "", "", "", "", "", "", "", "",
                            "; ".join(r["flags"]), r["reason"]])
            else:
                w.writerow([r["record_id"], r["crop"], r["recommendation_type"], r["current_stage"],
                            r["status"], r["confidence"],
                            r["required"]["N"], r["required"]["P2O5"], r["required"]["K2O"],
                            r["soil"]["N"], r["soil"]["P_proxy"], r["soil"]["K"],
                            r["gap"]["N"], r["gap"]["P2O5"], r["gap"]["K2O"],
                            r["plan_kg_ha"]["DAP_kg_ha"], r["plan_kg_ha"]["UREA_kg_ha"],
                            r["plan_kg_ha"]["MOP_kg_ha"],
                            "; ".join(r["flags"]), r["citation"]])

    print(f"\nCSV results written to: {csv_path}")
    print(f"SQLite database (full Digital Twin) written to: {ctx['db_path']}")


if __name__ == "__main__":
    main()
