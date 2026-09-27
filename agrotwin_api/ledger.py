"""
Nutrient Ledger — executable version of
11_Digital_Twin_Schema/02_nutrient_ledger_equations.md

Rules enforced in code (not just described in prose):
 1. Required side comes ONLY from fertilizer_recommendations rows, which
    themselves cite 06_Fertilizer_Recommendations/mpkv_icar_rdf.md.
 2. Gap = required - available. Losses are NULL/unsourced, so gap is
    computed WITHOUT subtracting losses (conservative, per the equations doc).
 3. Conversion to product quantities uses ONLY the exact FCO percentages in
    fertilizer_products (sourced from 07_Fertilizer_Composition).
 4. Every calculation carries a list of "flags" for any proxy or derived
    assumption used, and confidence is downgraded automatically based on
    flag count. Nothing is silently treated as exact.
 5. If a crop has no usable requirement in kg/ha (e.g. missing density with
    no fallback), the engine ABSTAINs rather than guessing.
"""

import sqlite3
import json


def get_recommendation(conn, crop_code, rec_type):
    cur = conn.cursor()
    cur.execute(
        """SELECT fr.n_kg_ha, fr.p2o5_kg_ha, fr.k2o_kg_ha, fr.source_citation, fr.notes
           FROM fertilizer_recommendations fr
           JOIN crops c ON c.crop_id = fr.crop_id
           WHERE c.crop_code = ? AND fr.recommendation_type = ?""",
        (crop_code, rec_type),
    )
    row = cur.fetchone()
    if row is None:
        return None
    # Support both sqlite3.Row (index-able) and psycopg3 dict row
    if hasattr(row, 'keys'):
        return (row["n_kg_ha"], row["p2o5_kg_ha"], row["k2o_kg_ha"],
                row["source_citation"], row["notes"])
    return tuple(row)


def get_products(conn):
    cur = conn.cursor()
    cur.execute("SELECT product_code, n_percent, p2o5_percent, k2o_percent FROM fertilizer_products")
    rows = cur.fetchall()
    result = {}
    for row in rows:
        # Support both sqlite3.Row (index-able) and psycopg3 dict row
        if hasattr(row, 'keys'):
            code = row["product_code"]
            n, p, k = row["n_percent"], row["p2o5_percent"], row["k2o_percent"]
        else:
            code, n, p, k = row
        # cast to float: SQLite returns float, PostgreSQL NUMERIC returns Decimal
        result[code] = {"n": float(n), "p2o5": float(p), "k2o": float(k)}
    return result


def compute_gap(required_n, required_p2o5, required_k2o, soil_n, soil_p_kg_ha, soil_k):
    """gap = required - available (no loss subtraction; losses unsourced).

    P conversion:
        Soil tests in Maharashtra report available P as elemental P (kg/ha).
        RDF recommendations (MPKV/ICAR) express phosphorus as P₂O₅ (kg/ha).
        Official conversion: P₂O₅ = P × (MW of P₂O₅ / 2 × MW of P)
                                   = P × (141.94 / 61.98) = P × 2.291
        Source: FCO (Fertiliser Control Order) and ICAR soil testing methodology;
                used by all Maharashtra Soil Testing Laboratories (STLs).

    All inputs are cast to float to handle both SQLite float and PostgreSQL Decimal.
    """
    # P₂O₅ / P molar mass ratio — official ICAR/FCO conversion factor
    P_TO_P2O5 = 2.291

    def _f(v):
        return float(v) if v is not None else None

    rn, rp, rk = _f(required_n), _f(required_p2o5), _f(required_k2o)
    sn, sk = float(soil_n), float(soil_k)
    # Convert soil elemental P → P₂O₅ to match RDF units
    soil_p2o5_equivalent = round(float(soil_p_kg_ha) * P_TO_P2O5, 1)

    gap_n    = max(0.0, round(rn - sn, 1)) if rn is not None else None
    gap_p2o5 = max(0.0, round(rp - soil_p2o5_equivalent, 1)) if rp is not None else None
    gap_k2o  = max(0.0, round(rk - sk, 1)) if rk is not None else None
    return gap_n, gap_p2o5, gap_k2o


def convert_gap_to_products(gap_n, gap_p2o5, gap_k2o, products):
    """Prefer DAP for P, then Urea for remaining N, MOP for K.
    Exact logic from 07_Fertilizer_Composition/conversion_notes.md."""
    dap = products["DAP"]
    urea = products["UREA"]
    mop = products["MOP"]

    dap_kg = round(gap_p2o5 / (dap["p2o5"] / 100), 1) if gap_p2o5 > 0 else 0.0
    n_from_dap = round(dap_kg * (dap["n"] / 100), 1)
    remaining_n = max(0.0, round(gap_n - n_from_dap, 1))
    urea_kg = round(remaining_n / (urea["n"] / 100), 1) if remaining_n > 0 else 0.0
    mop_kg = round(gap_k2o / (mop["k2o"] / 100), 1) if gap_k2o > 0 else 0.0

    return {"DAP_kg_ha": dap_kg, "UREA_kg_ha": urea_kg, "MOP_kg_ha": mop_kg,
            "n_supplied_by_dap_kg_ha": n_from_dap}


def run_field(conn, field_id, field_meta, rec_type_map):
    """Runs the ledger for a single field. Returns a result dict.
    field_meta: {"field_id":.., "crop_code":.., "current_stage":.., "row": csv_row_dict}
    """
    row = field_meta["row"]
    record_id = row["record_id"]
    crop_code = field_meta["crop_code"]
    rec_type = rec_type_map[record_id]

    # P→P₂O₅ conversion applied (see compute_gap docstring).
    # Flag is now informational (unit-mismatch resolved), not a quality downgrade.
    flags = ["P_CONVERTED_TO_P2O5 (soil test P kg/ha × 2.291 → P₂O₅ kg/ha; "
             "ICAR/FCO molar mass ratio 141.94/61.98; confidence maintained)"]

    rec = get_recommendation(conn, crop_code, rec_type)
    if rec is None:
        return {
            "record_id": record_id, "crop": crop_code, "status": "ABSTAIN",
            "reason": f"No fertilizer_recommendations row for {crop_code}/{rec_type}",
            "flags": flags,
        }

    required_n, required_p2o5, required_k2o, citation, notes = rec
    # Cast NUMERIC → float (safe for both SQLite float and PostgreSQL Decimal)
    required_n    = float(required_n)    if required_n    is not None else None
    required_p2o5 = float(required_p2o5) if required_p2o5 is not None else None
    required_k2o  = float(required_k2o)  if required_k2o  is not None else None

    if crop_code == "BANANA":
        flags.append("DERIVED_DENSITY (Banana kg/ha derived from g/plant x mid-point "
                      "2,250 plants/ha; replace with exact field density when known)")
    if crop_code == "COTTON":
        flags.append("MIDPOINT_RANGE_RDF (source gives a range for Cotton; mid-point used)")

    soil_n = float(row["N_kg_ha"])
    soil_p_kg_ha = float(row["P_kg_ha"])   # elemental P — converted inside compute_gap
    soil_k = float(row["K_kg_ha"])

    gap_n, gap_p2o5, gap_k2o = compute_gap(required_n, required_p2o5, required_k2o,
                                            soil_n, soil_p_kg_ha, soil_k)

    products = get_products(conn)
    plan = convert_gap_to_products(gap_n, gap_p2o5, gap_k2o, products)

    # Confidence: HIGH when only the informational P-conversion flag is present,
    # LOW when extra flags are added (e.g. MIDPOINT_RANGE_RDF, DERIVED_DENSITY).
    confidence = "HIGH" if len(flags) == 1 else "MEDIUM" if len(flags) == 2 else "LOW"

    no_fertilizer_needed = (plan["DAP_kg_ha"] == 0 and plan["UREA_kg_ha"] == 0
                             and plan["MOP_kg_ha"] == 0)

    return {
        "record_id": record_id,
        "field_id": field_id,
        "crop": crop_code,
        "recommendation_type": rec_type,
        "current_stage": field_meta["current_stage"],
        "status": "NO_FERTILIZER_NEEDED" if no_fertilizer_needed else "PLAN_GENERATED",
        "required": {"N": required_n, "P2O5": required_p2o5, "K2O": required_k2o},
        "soil": {"N": soil_n, "P_kg_ha": soil_p_kg_ha,
                 "P2O5_equivalent": round(soil_p_kg_ha * 2.291, 1), "K": soil_k},
        "gap": {"N": gap_n, "P2O5": gap_p2o5, "K2O": gap_k2o},
        "plan_kg_ha": plan,
        "confidence": confidence,
        "flags": flags,
        "citation": citation,
        "recommendation_notes": notes,
    }
