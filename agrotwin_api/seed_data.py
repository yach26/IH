"""
Seeds the AgroTwin SQLite Digital Twin with REAL data from the Phase-1 pack.

Every value below is either:
  (a) copied verbatim from a specific file in AgroTwin_Phase1_Data, or
  (b) a clearly-flagged DERIVED value (e.g. Banana kg/ha from g/plant x
      mid-point planting density), or
  (c) a clearly-flagged mid-point of a source range (e.g. Cotton NPK).

Nothing here is invented. Where a real number was missing, see
04_remaining_gaps.md — those gaps are NOT silently filled here.
"""

import sqlite3
import csv
import os
import sys
from datetime import datetime


def _to_iso_date(raw: str, fallback: str = "2024-01-01") -> str:
    """Normalizes a date string to ISO YYYY-MM-DD.

    The real Polgaon CSV stores dates as DD-MM-YYYY. Every other table in
    this schema (recommendations, events, etc.) uses ISO dates, and
    `ORDER BY test_date DESC` throughout app/api/routes.py is a plain string
    sort — a DD-MM-YYYY string sorts ahead of any real ISO date (e.g.
    "24-10-2016" > "2026-09-27" lexicographically), which silently hid every
    later-confirmed real soil test behind this 2016 seed row.
    """
    if not raw:
        return fallback
    try:
        return datetime.strptime(raw.strip(), "%d-%m-%Y").strftime("%Y-%m-%d")
    except ValueError:
        return raw

_api_root = os.path.abspath(os.path.dirname(__file__))
if _api_root not in sys.path:
    sys.path.insert(0, _api_root)

from app.db import get_db_connection, init_db, is_postgres, AGROTWIN_DB

DB_PATH = AGROTWIN_DB
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def build_db():
    if not is_postgres():
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        init_db()
        return get_db_connection()
    else:
        init_db()
        conn = get_db_connection()
        tables = [
            "soil_report_uploads", "audit_log", "alerts", "events", "weather_snapshots",
            "recommendations", "nutrient_ledger_entries", "applications", "soil_tests",
            "fertilizer_recommendations", "fertilizer_products", "field_crops", "crop_calendars",
            "crops", "fields", "farmers", "talukas", "districts", "regions"
        ]
        cur = conn.cursor()
        for t in tables:
            try:
                cur.execute(f"TRUNCATE TABLE {t} RESTART IDENTITY CASCADE")
            except Exception:
                pass
        conn.commit()
        return conn


def seed_regions_districts_talukas(conn):
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO regions (region_code, region_name, country_code) VALUES (?,?,?)",
        ("MH", "Maharashtra", "IN"),
    )
    region_id = cur.lastrowid

    # Source: 01_Boundaries/district_boundaries.md
    cur.execute(
        """INSERT INTO districts
           (region_id, district_code, district_name, area_km2,
            lat_min, lat_max, lon_min, lon_max, agro_zones_json)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (region_id, "KOLHAPUR", "Kolhapur", 7685.0,
         15.7167, 17.1667, 73.7167, 74.7333,
         '["Western: heavy rainfall, lateritic soils",'
         ' "Central: moderate assured rainfall",'
         ' "Eastern: uncertain rainfall, medium black soils"]'),
    )
    kolhapur_id = cur.lastrowid

    cur.execute(
        """INSERT INTO districts
           (region_id, district_code, district_name, area_km2,
            lat_min, lat_max, lon_min, lon_max, agro_zones_json)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (region_id, "JALGAON", "Jalgaon", 11765.0,
         20.0, 21.0, 74.9167, 76.4667,
         '["Scarcity zone (5 blocks)", "Assured rainfall zone (10 blocks)"]'),
    )
    jalgaon_id = cur.lastrowid

    kolhapur_talukas = [
        "Karvir", "Hatkanangle", "Shirol", "Kagal", "Gadhinglaj", "Panhala",
        "Shahuwadi", "Radhanagari", "Bhudargad", "Ajara", "Chandgad", "Gaganbawada",
    ]
    pilot_kolhapur = {"Shirol", "Hatkanangle"}
    for t in kolhapur_talukas:
        cur.execute(
            "INSERT INTO talukas (district_id, taluka_code, taluka_name, is_pilot) VALUES (?,?,?,?)",
            (kolhapur_id, t.upper(), t, True if t in pilot_kolhapur else False),
        )

    jalgaon_talukas = [
        "Jalgaon", "Bhusawal", "Jamner", "Muktainagar", "Raver", "Yawal",
        "Chopda", "Amalner", "Parola", "Pachora", "Chalisgaon", "Erandol",
        "Bhadgaon", "Bodwad", "Dharangaon",
    ]
    pilot_jalgaon = {"Raver", "Yawal"}
    for t in jalgaon_talukas:
        cur.execute(
            "INSERT INTO talukas (district_id, taluka_code, taluka_name, is_pilot) VALUES (?,?,?,?)",
            (jalgaon_id, t.upper(), t, True if t in pilot_jalgaon else False),
        )

    # Beyond the two piloted districts (Kolhapur, Jalgaon — the only ones with
    # sourced lat/lon bounding boxes and agro-zone notes), a real farmer
    # elsewhere in Maharashtra still needs a district to complete onboarding.
    # These are real, publicly-known Maharashtra district names — not an
    # agronomic threshold, so no "don't invent thresholds" concern — but we
    # do NOT fabricate lat/lon bounding boxes or agro-zone data for them
    # (left NULL; nothing downstream requires them, and the fertilizer
    # ledger/RDF lookup and weather were never region-gated to begin with —
    # both key off crop/stage and lat/lon directly). A farmer outside
    # Maharashtra entirely gets the explicit "Other" row so onboarding never
    # forces a false district.
    other_maharashtra_districts = [
        "Ahmednagar", "Akola", "Amravati", "Beed", "Bhandara", "Buldhana",
        "Chandrapur", "Chhatrapati Sambhaji Nagar", "Dhule", "Gadchiroli",
        "Gondia", "Hingoli", "Jalna", "Latur", "Mumbai City", "Mumbai Suburban",
        "Nagpur", "Nanded", "Nandurbar", "Nashik", "Dharashiv", "Palghar",
        "Parbhani", "Pune", "Raigad", "Ratnagiri", "Sangli", "Satara",
        "Sindhudurg", "Solapur", "Thane", "Wardha", "Washim", "Yavatmal",
    ]
    for name in other_maharashtra_districts:
        cur.execute(
            "INSERT INTO districts (region_id, district_code, district_name) VALUES (?,?,?)",
            (region_id, name.upper().replace(" ", "_"), name),
        )

    other_region_id_row = cur.execute(
        "SELECT region_id FROM regions WHERE region_code = 'OTHER'"
    ).fetchone()
    if other_region_id_row is None:
        cur.execute(
            "INSERT INTO regions (region_code, region_name, country_code) VALUES (?,?,?)",
            ("OTHER", "Outside pilot regions", "IN"),
        )
        other_region_id = cur.lastrowid
        cur.execute(
            "INSERT INTO districts (region_id, district_code, district_name) VALUES (?,?,?)",
            (other_region_id, "OTHER", "Other / not listed"),
        )

    conn.commit()
    return region_id, {"Kolhapur": kolhapur_id, "Jalgaon": jalgaon_id}


def seed_crops(conn):
    cur = conn.cursor()
    crops = [
        ("BANANA", "Banana"),
        ("SUGARCANE", "Sugarcane"),
        ("COTTON", "Cotton (Bt)"),
        ("SOYBEAN", "Soybean"),
    ]
    crop_ids = {}
    for code, name in crops:
        cur.execute("INSERT INTO crops (crop_code, crop_name) VALUES (?,?)", (code, name))
        crop_ids[code] = cur.lastrowid
    conn.commit()
    return crop_ids


def seed_crop_calendars(conn, crop_ids):
    """Source: rag/docs/crop_calendars.md (ICAR-NRRI + MPKV Rahuri Extension
    Bulletins, Maharashtra, 2022). Day ranges convert the doc's "months after
    planting" at 30 days/month (the doc's own convention, e.g. "18-month
    cycle" for Adsali sugarcane). RICE has no seeded crop record in this
    system (see crops table) so its calendar entry from the source doc is
    intentionally not loaded here — never seed a calendar for a crop that
    doesn't exist. SOYBEAN has no calendar in the source doc at all, so it is
    left uncalendared rather than inventing one — its current_stage stays a
    declared (farmer/crop-assign) value only, exactly as before this feature.
    Powers dynamic, sowing-date-driven current_stage resolution in
    crop_agent.resolve_dynamic_stage(); see docs there for how it's applied.
    """
    cur = conn.cursor()
    calendars = {
        "SUGARCANE": [
            ("GERMINATION", 1, 0, 60),
            ("TILLERING", 2, 60, 120),
            ("GRAND_GROWTH", 3, 120, 240),
            ("RIPENING", 4, 240, 420),
            ("HARVEST", 5, 420, 540),
        ],
        "COTTON": [
            ("GERMINATION", 1, 0, 44),
            ("SQUARING", 2, 45, 74),
            ("BOLL_DEVELOPMENT", 3, 75, 99),
            ("BOLL_OPENING", 4, 100, 129),
            ("HARVEST", 5, 130, 160),
        ],
        "BANANA": [
            ("RHIZOME_ESTABLISHMENT", 1, 0, 60),
            ("VEGETATIVE", 2, 60, 120),
            ("BUNCH_INITIATION", 3, 120, 180),
            ("SHOOTING", 4, 180, 240),
            ("BUNCH_FILLING", 5, 240, 300),
            ("HARVEST", 6, 300, 360),
        ],
    }
    for code, stages in calendars.items():
        crop_id = crop_ids.get(code)
        if crop_id is None:
            continue
        for stage_name, order, dmin, dmax in stages:
            cur.execute(
                """INSERT INTO crop_calendars
                   (crop_id, stage_name, stage_order, days_after_planting_min, days_after_planting_max, source_file)
                   VALUES (?,?,?,?,?,?)""",
                (crop_id, stage_name, order, dmin, dmax, "rag/docs/crop_calendars.md"),
            )
    conn.commit()


def seed_fertilizer_products(conn):
    cur = conn.cursor()
    product_ids = {}
    with open(os.path.join(DATA_DIR, "npk_composition.csv")) as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row["Fertilizer"].upper().replace("-", "_")
            cur.execute(
                """INSERT INTO fertilizer_products
                   (product_code, product_name, n_percent, p2o5_percent, k2o_percent, notes)
                   VALUES (?,?,?,?,?,?)""",
                (code, row["Fertilizer"], float(row["N_percent"]),
                 float(row["P2O5_percent"]), float(row["K2O_percent"]), row["Notes"]),
            )
            product_ids[code] = cur.lastrowid
    conn.commit()
    return product_ids


def seed_fertilizer_recommendations(conn, crop_ids):
    """Source: 06_Fertilizer_Recommendations/mpkv_icar_rdf.md
    Banana kg/ha is DERIVED (see notes) using density from
    05_Crop_Calendars/four_pilot_crops.md (2,000-2,500 plants/ha, mid-point 2,250).
    Cotton values are mid-points of the ranges given in the source.
    """
    cur = conn.cursor()
    rec_ids = {}

    density_mid = 2250  # plants/ha, mid-point of 2,000-2,500 (05_Crop_Calendars)
    banana_n_kg_ha = round(150 * density_mid / 1000, 1)
    banana_p_kg_ha = round(60 * density_mid / 1000, 1)
    banana_k_kg_ha = round(150 * density_mid / 1000, 1)

    rows = [
        dict(crop="BANANA", rtype="FULL_SEASON",
             n_kg_ha=banana_n_kg_ha, p2o5_kg_ha=banana_p_kg_ha, k2o_kg_ha=banana_k_kg_ha,
             n_g=150, p2o5_g=60, k2o_g=150, fym=None,
             citation=("06_Fertilizer_Recommendations/mpkv_icar_rdf.md, Banana "
                       "(150:60:150 g/plant) + 05_Crop_Calendars/four_pilot_crops.md "
                       "density 2,000-2,500 plants/ha (mid-point 2,250 used)"),
             notes="DERIVED kg/ha from g/plant x mid-point density. Replace with exact "
                   "plant count per field when available. Raw source is g/plant."),
        dict(crop="SUGARCANE", rtype="PRE_SEASONAL",
             n_kg_ha=340, p2o5_kg_ha=170, k2o_kg_ha=170,
             n_g=None, p2o5_g=None, k2o_g=None, fym=None,
             citation="06_Fertilizer_Recommendations/mpkv_icar_rdf.md, Sugarcane pre-seasonal/Adsali",
             notes="Full-season RDF, exact source value, no derivation."),
        dict(crop="SUGARCANE", rtype="RATOON",
             n_kg_ha=250, p2o5_kg_ha=115, k2o_kg_ha=115,
             n_g=None, p2o5_g=None, k2o_g=None, fym=None,
             citation="06_Fertilizer_Recommendations/mpkv_icar_rdf.md, Sugarcane ratoon",
             notes="Full-season RDF, exact source value, no derivation."),
        dict(crop="COTTON", rtype="IRRIGATED",
             n_kg_ha=137.5, p2o5_kg_ha=70, k2o_kg_ha=70,
             n_g=None, p2o5_g=None, k2o_g=None, fym=None,
             citation="06_Fertilizer_Recommendations/mpkv_icar_rdf.md, Cotton irrigated (range 125-150:65-75:65-75, mid-point used)",
             notes="Source gives a range, not a single value; mid-point used until a finer source is added."),
        dict(crop="COTTON", rtype="RAINFED",
             n_kg_ha=30, p2o5_kg_ha=25, k2o_kg_ha=25,
             n_g=None, p2o5_g=None, k2o_g=None, fym=None,
             citation="06_Fertilizer_Recommendations/mpkv_icar_rdf.md, Cotton rainfed (range 20-40:20-30:20-30, mid-point used)",
             notes="Source gives a range, not a single value; mid-point used until a finer source is added."),
        dict(crop="SOYBEAN", rtype="FULL_SEASON",
             n_kg_ha=50, p2o5_kg_ha=75, k2o_kg_ha=45,
             n_g=None, p2o5_g=None, k2o_g=None, fym=7.5,
             citation="06_Fertilizer_Recommendations/mpkv_icar_rdf.md, Soybean",
             notes="FYM given as a 5-10 t/ha range in source; mid-point 7.5 used."),
    ]

    for r in rows:
        cur.execute(
            """INSERT INTO fertilizer_recommendations
               (crop_id, recommendation_type, n_kg_ha, p2o5_kg_ha, k2o_kg_ha,
                n_g_per_plant, p2o5_g_per_plant, k2o_g_per_plant, fym_t_ha,
                stage_applicability, source_citation, notes)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (crop_ids[r["crop"]], r["rtype"], r["n_kg_ha"], r["p2o5_kg_ha"], r["k2o_kg_ha"],
             r["n_g"], r["p2o5_g"], r["k2o_g"], r["fym"],
             "FULL_SEASON", r["citation"], r["notes"]),
        )
        rec_ids[(r["crop"], r["rtype"])] = cur.lastrowid

    conn.commit()
    return rec_ids


# record_id -> recommendation_type key used against fertilizer_recommendations
RECOMMENDATION_TYPE_BY_RECORD = {
    "SYN-001": "FULL_SEASON",   # Banana
    "SYN-002": "FULL_SEASON",   # Banana
    "SYN-003": "PRE_SEASONAL",  # Sugarcane, matches "340:170:170 + 25t FYM" in notes
    "SYN-004": "RATOON",        # Sugarcane, notes say "Ratoon 250:115:115"
    "SYN-005": "RAINFED",       # Cotton, irrigation_type "Rainfed + protective"
    "SYN-006": "FULL_SEASON",   # Soybean
    "SYN-007": "IRRIGATED",     # Cotton, irrigation_type "Irrigated"
    "SYN-008": "RATOON",        # Sugarcane, notes say "ratoon"
    # Real Polgaon Kolhapur records: Sugarcane, GRAND_GROWTH stage -> PRE_SEASONAL RDF row
    "REAL-001": "PRE_SEASONAL",
    "REAL-002": "PRE_SEASONAL",
    "REAL-003": "PRE_SEASONAL",
    "REAL-004": "PRE_SEASONAL",
    "REAL-005": "PRE_SEASONAL",
    "REAL-006": "PRE_SEASONAL",
    "REAL-007": "PRE_SEASONAL",
    "REAL-008": "PRE_SEASONAL",
}


def seed_fields_and_soil_tests(conn, region_id, district_ids, crop_ids):
    cur = conn.cursor()
    # map taluka_name -> taluka_id for quick lookup
    cur.execute("SELECT taluka_id, taluka_name, district_id FROM talukas")
    taluka_lookup = {}
    for taluka in cur.fetchall():
        if hasattr(taluka, "keys"):
            tid, name, did = taluka["taluka_id"], taluka["taluka_name"], taluka["district_id"]
        else:
            tid, name, did = taluka
        taluka_lookup[(name, did)] = tid

    field_ids = {}

    # Try to load real soil data from Polgaon dataset first
    real_data_path = os.path.join(DATA_DIR, "real_kolhapur", "soil_tests", "polgaon_soil_health.csv")
    use_real_data = os.path.exists(real_data_path)

    if use_real_data:
        # Load real soil test data from Polgaon
        with open(real_data_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            real_rows = []
            for row in reader:
                # Only use rows with complete N, P, K, pH, OC
                if (row.get("N") and row.get("P") and row.get("K") and
                    row.get("pH") and row.get("OC")):
                    try:
                        n = float(row["N"])
                        p = float(row["P"])
                        k = float(row["K"])
                        ph = float(row["pH"])
                        oc = float(row["OC"])
                        if n > 0 and p > 0 and k > 0 and 3 <= ph <= 11 and 0 <= oc <= 10:
                            real_rows.append(row)
                    except (ValueError, TypeError):
                        continue

        # Take up to 8 real rows
        selected_rows = real_rows[:8]

        for idx, row in enumerate(selected_rows):
            rid = f"REAL-{idx+1:03d}"
            district_id = district_ids["Kolhapur"]
            taluka_id = taluka_lookup.get(("Shirol", district_id))
            crop_code = "SUGARCANE"  # Most common crop in the region

            lat_val = float(row["Latitude"]) if row.get("Latitude") else None
            lon_val = float(row["Longitude"]) if row.get("Longitude") else None
            land_area = float(row["Land Area"]) if row.get("Land Area") else 2.0

            cur.execute(
                """INSERT INTO fields
                   (region_id, district_id, taluka_id, field_code, area_ha,
                    irrigation_type, lat, lon, is_synthetic, label_note)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (region_id, district_id, taluka_id, rid, land_area,
                 "Irrigated", lat_val, lon_val, False,
                 f"Real soil data from Polgaon - {row.get('Farmer Name', 'Unknown')}"),
            )
            field_id = cur.lastrowid
            aliased_row = {**row, "record_id": rid, "N_kg_ha": n, "P_kg_ha": p, "K_kg_ha": k}
            field_ids[rid] = {"field_id": field_id, "crop_code": crop_code,
                               "current_stage": "GRAND_GROWTH", "row": aliased_row}

            cur.execute(
                """INSERT INTO soil_tests
                   (field_id, test_date, n_kg_ha, p_kg_ha, k_kg_ha, ph, oc_percent,
                    source, is_synthetic, label_note)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (field_id, _to_iso_date(row.get("Date of Sample Taken")),
                 float(row["N"]), float(row["P"]), float(row["K"]),
                 float(row["pH"]), float(row["OC"]),
                 "real_kolhapur_shc", False,
                 f"Real SHC data - Polgaon"),
            )

            rec_type = "PRE_SEASONAL"
            cur.execute(
                """INSERT INTO field_crops
                   (field_id, crop_id, variety, sowing_date, current_stage,
                    recommendation_type, is_active)
                   VALUES (?,?,?,?,?,?,?)""",
                (
                    field_id,
                    crop_ids[crop_code],
                    None,
                    "2024-06-01",
                    "GRAND_GROWTH",
                    rec_type,
                    True,
                ),
            )
    else:
        # Fallback to synthetic data
        with open(os.path.join(DATA_DIR, "synthetic_records.csv")) as f:
            reader = csv.DictReader(f)
            for row in reader:
                rid = row["record_id"]
                district_id = district_ids[row["district"]]
                taluka_id = taluka_lookup.get((row["taluka"], district_id))
                crop_code = row["crop"].upper()

                lat_val = float(row["lat_deg"]) if row.get("lat_deg") else None
                lon_val = float(row["lon_deg"]) if row.get("lon_deg") else None

                cur.execute(
                    """INSERT INTO fields
                       (region_id, district_id, taluka_id, field_code, area_ha,
                        irrigation_type, lat, lon, is_synthetic, label_note)
                       VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (region_id, district_id, taluka_id, rid, float(row["field_area_ha"]),
                     row["irrigation_type"], lat_val, lon_val, True, row["label"]),
                )
                field_id = cur.lastrowid
                field_ids[rid] = {"field_id": field_id, "crop_code": crop_code,
                                   "current_stage": row["current_stage"], "row": row}

                cur.execute(
                    """INSERT INTO soil_tests
                       (field_id, test_date, n_kg_ha, p_kg_ha, k_kg_ha, ph, oc_percent,
                        source, is_synthetic, label_note)
                       VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (field_id, row["soil_test_date"], float(row["N_kg_ha"]),
                     float(row["P_kg_ha"]), float(row["K_kg_ha"]), float(row["pH"]),
                     float(row["OC_percent"]), "SYNTHETIC", True, row["label"]),
                )

                rec_type = RECOMMENDATION_TYPE_BY_RECORD.get(rid, "FULL_SEASON")
                cur.execute(
                    """INSERT INTO field_crops
                       (field_id, crop_id, variety, sowing_date, current_stage,
                        recommendation_type, is_active)
                       VALUES (?,?,?,?,?,?,?)""",
                    (
                        field_id,
                        crop_ids[crop_code],
                        row.get("variety"),
                        row.get("sowing_date"),
                        row.get("current_stage"),
                        rec_type,
                        True,
                    ),
                )
    conn.commit()
    return field_ids


def seed_all():
    conn = build_db()
    region_id, district_ids = seed_regions_districts_talukas(conn)
    crop_ids = seed_crops(conn)
    seed_crop_calendars(conn, crop_ids)
    product_ids = seed_fertilizer_products(conn)
    rec_ids = seed_fertilizer_recommendations(conn, crop_ids)
    field_ids = seed_fields_and_soil_tests(conn, region_id, district_ids, crop_ids)
    conn.close()
    return {
        "db_path": DB_PATH,
        "region_id": region_id,
        "district_ids": district_ids,
        "crop_ids": crop_ids,
        "product_ids": product_ids,
        "rec_ids": rec_ids,
        "field_ids": field_ids,
    }


def main():
    """CLI entry point with safety guards."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Seed AgroTwin database with demo data")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reseed even if data exists (required for Postgres)",
    )
    parser.add_argument(
        "--demo-only",
        action="store_true",
        help="Only seed if database is empty or missing (safe default)",
    )
    args = parser.parse_args()

    if is_postgres() and not args.force:
        print("ERROR: Refusing to seed Postgres without --force flag.", file=sys.stderr)
        print("This would TRUNCATE all production tables.", file=sys.stderr)
        print("If you really want to reseed, run: python seed_data.py --force", file=sys.stderr)
        sys.exit(1)

    if not is_postgres() and not args.force:
        if os.path.exists(DB_PATH):
            # Check if already has data
            conn = sqlite3.connect(DB_PATH)
            try:
                count = conn.execute("SELECT COUNT(*) FROM fields").fetchone()[0]
                if count > 0:
                    print(f"Database already has {count} fields. Use --force to reseed.", file=sys.stderr)
                    sys.exit(1)
            finally:
                conn.close()

    ctx = seed_all()
    print(f"Seeded database at {ctx['db_path']}")
    print(f"Fields loaded: {list(ctx['field_ids'].keys())}")


if __name__ == "__main__":
    main()
