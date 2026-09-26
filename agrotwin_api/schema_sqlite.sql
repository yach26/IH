-- ============================================================
-- AgroTwin AI — Digital Twin schema (SQLite port of the frozen
-- Postgres DDL from 11_Digital_Twin_Schema/01_digital_twin_schema.sql)
-- Kept table/column names identical for a 1:1 mapping back to Postgres.
-- Type changes only: SERIAL->INTEGER PK, JSONB->TEXT, GEOMETRY->TEXT,
-- TIMESTAMPTZ->TEXT, BOOLEAN kept (SQLite stores as 0/1).
-- ============================================================

PRAGMA foreign_keys = ON;

CREATE TABLE regions (
    region_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    region_code     TEXT UNIQUE NOT NULL,
    region_name     TEXT NOT NULL,
    country_code    TEXT DEFAULT 'IN',
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE districts (
    district_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    region_id       INTEGER NOT NULL REFERENCES regions(region_id),
    district_code   TEXT UNIQUE NOT NULL,
    district_name   TEXT NOT NULL,
    area_km2        NUMERIC,
    lat_min         NUMERIC,
    lat_max         NUMERIC,
    lon_min         NUMERIC,
    lon_max         NUMERIC,
    agro_zones_json TEXT,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE talukas (
    taluka_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    district_id     INTEGER NOT NULL REFERENCES districts(district_id),
    taluka_code     TEXT NOT NULL,
    taluka_name     TEXT NOT NULL,
    is_pilot        BOOLEAN DEFAULT 0,
    UNIQUE (district_id, taluka_code)
);

CREATE TABLE farmers (
    farmer_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    region_id       INTEGER NOT NULL REFERENCES regions(region_id),
    full_name       TEXT,
    mobile          TEXT,
    preferred_lang  TEXT DEFAULT 'mr',
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE fields (
    field_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    region_id       INTEGER NOT NULL REFERENCES regions(region_id),
    district_id     INTEGER NOT NULL REFERENCES districts(district_id),
    taluka_id       INTEGER REFERENCES talukas(taluka_id),
    farmer_id       INTEGER REFERENCES farmers(farmer_id),
    field_code      TEXT UNIQUE,
    area_ha         NUMERIC NOT NULL,
    soil_type       TEXT,
    irrigation_type TEXT,
    geometry        TEXT,
    is_synthetic    BOOLEAN DEFAULT 0,
    label_note      TEXT,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at      TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fields_district ON fields(district_id);
CREATE INDEX idx_fields_synthetic ON fields(is_synthetic);

CREATE TABLE crops (
    crop_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    crop_code       TEXT UNIQUE NOT NULL,
    crop_name       TEXT NOT NULL,
    scientific_name TEXT,
    is_pilot        BOOLEAN DEFAULT 1
);

CREATE TABLE crop_calendars (
    calendar_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    crop_id         INTEGER NOT NULL REFERENCES crops(crop_id),
    region_id       INTEGER REFERENCES regions(region_id),
    stage_name      TEXT NOT NULL,
    stage_order     INTEGER NOT NULL,
    days_after_planting_min INTEGER,
    days_after_planting_max INTEGER,
    notes           TEXT,
    source_file     TEXT DEFAULT '05_Crop_Calendars/four_pilot_crops.md'
);

CREATE TABLE fertilizer_products (
    product_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    product_code    TEXT UNIQUE NOT NULL,
    product_name    TEXT NOT NULL,
    n_percent       NUMERIC NOT NULL,
    p2o5_percent    NUMERIC NOT NULL,
    k2o_percent     NUMERIC NOT NULL,
    notes           TEXT,
    source_file     TEXT DEFAULT '07_Fertilizer_Composition/npk_composition.csv'
);

CREATE TABLE fertilizer_recommendations (
    rec_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    crop_id         INTEGER NOT NULL REFERENCES crops(crop_id),
    region_id       INTEGER REFERENCES regions(region_id),
    recommendation_type TEXT NOT NULL,
    n_kg_ha         NUMERIC,
    p2o5_kg_ha      NUMERIC,
    k2o_kg_ha       NUMERIC,
    n_g_per_plant   NUMERIC,
    p2o5_g_per_plant NUMERIC,
    k2o_g_per_plant NUMERIC,
    fym_t_ha        NUMERIC,
    stage_applicability TEXT,
    source_citation TEXT NOT NULL,
    notes           TEXT
);

CREATE TABLE soil_tests (
    soil_test_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    field_id        INTEGER NOT NULL REFERENCES fields(field_id),
    test_date       TEXT NOT NULL,
    n_kg_ha         NUMERIC,
    p_kg_ha         NUMERIC,
    k_kg_ha         NUMERIC,
    ph              NUMERIC,
    oc_percent      NUMERIC,
    ec_ds_m         NUMERIC,
    source          TEXT DEFAULT 'SYNTHETIC',
    is_synthetic    BOOLEAN DEFAULT 0,
    label_note      TEXT,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE applications (
    application_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    field_id        INTEGER NOT NULL REFERENCES fields(field_id),
    product_id      INTEGER REFERENCES fertilizer_products(product_id),
    application_date TEXT,
    quantity_kg     NUMERIC,
    quantity_kg_ha  NUMERIC,
    n_supplied_kg_ha NUMERIC,
    p2o5_supplied_kg_ha NUMERIC,
    k2o_supplied_kg_ha NUMERIC,
    notes           TEXT,
    is_synthetic    BOOLEAN DEFAULT 0
);

CREATE TABLE nutrient_ledger_entries (
    ledger_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    field_id        INTEGER NOT NULL REFERENCES fields(field_id),
    entry_date      TEXT NOT NULL DEFAULT CURRENT_DATE,
    crop_id         INTEGER REFERENCES crops(crop_id),
    current_stage   TEXT,
    required_n_kg_ha    NUMERIC,
    required_p2o5_kg_ha NUMERIC,
    required_k2o_kg_ha  NUMERIC,
    required_source     TEXT,
    soil_n_kg_ha        NUMERIC,
    soil_p_kg_ha        NUMERIC,
    soil_k_kg_ha        NUMERIC,
    fertilizer_n_supplied NUMERIC DEFAULT 0,
    fertilizer_p2o5_supplied NUMERIC DEFAULT 0,
    fertilizer_k2o_supplied NUMERIC DEFAULT 0,
    estimated_losses_n  NUMERIC,
    estimated_losses_p  NUMERIC,
    estimated_losses_k  NUMERIC,
    gap_n_kg_ha         NUMERIC,
    gap_p2o5_kg_ha      NUMERIC,
    gap_k2o_kg_ha       NUMERIC,
    calculation_notes   TEXT,
    is_synthetic        BOOLEAN DEFAULT 0,
    created_at          TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE recommendations (
    recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_id        INTEGER NOT NULL REFERENCES fields(field_id),
    ledger_id       INTEGER REFERENCES nutrient_ledger_entries(ledger_id),
    generated_at    TEXT DEFAULT CURRENT_TIMESTAMP,
    plan_json       TEXT NOT NULL,
    total_cost_estimate NUMERIC,
    confidence      TEXT,
    confidence_reason TEXT,
    evidence_citations TEXT,
    is_synthetic    BOOLEAN DEFAULT 0,
    status          TEXT DEFAULT 'PROPOSED'
);

CREATE TABLE alerts (
    alert_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    field_id        INTEGER REFERENCES fields(field_id),
    alert_type      TEXT NOT NULL,
    severity        TEXT,
    message         TEXT,
    triggered_at    TEXT DEFAULT CURRENT_TIMESTAMP,
    resolved_at     TEXT,
    related_recommendation_id INTEGER REFERENCES recommendations(recommendation_id)
);

CREATE TABLE audit_log (
    audit_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type     TEXT NOT NULL,
    entity_id       INTEGER,
    action          TEXT NOT NULL,
    actor           TEXT,
    old_value       TEXT,
    new_value       TEXT,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP
);
