-- ============================================================
-- AgroTwin AI — Digital Twin schema (SQLite port of the frozen
-- Postgres DDL from 11_Digital_Twin_Schema/01_digital_twin_schema.sql)
-- Kept table/column names identical for a 1:1 mapping back to Postgres.
-- Type changes only: SERIAL->INTEGER PK, JSONB->TEXT, GEOMETRY->TEXT,
-- TIMESTAMPTZ->TEXT, BOOLEAN kept (SQLite stores as 0/1).
--
-- Phase-2 additions (doc 03_DATABASE_SCHEMA.md):
--   - field_crops: one active crop per field
--   - weather_snapshots: cached Open-Meteo forecasts
--   - events: audit event stream (HEAVY_RAIN_ALERT, SOIL_REPORT_UPDATED, …)
--   - audit_log: extended with actor/old_value/new_value columns
--   - recommendations: added invalidated_at, superseded_by
--   - Indexes on (field_id, created_at DESC) for fast "latest" queries
-- ============================================================

PRAGMA foreign_keys = ON;

-- ──────────────────────────────────────────────
-- Geography / Admin hierarchy
-- ──────────────────────────────────────────────

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

-- ──────────────────────────────────────────────
-- Farmers & Fields
-- ──────────────────────────────────────────────

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
    -- Lat/lon stored as plain NUMERIC for MVP (no PostGIS in SQLite)
    lat             NUMERIC,
    lon             NUMERIC,
    geometry        TEXT,                   -- GeoJSON string, optional
    is_synthetic    BOOLEAN DEFAULT 0,
    label_note      TEXT,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at      TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fields_district   ON fields(district_id);
CREATE INDEX idx_fields_synthetic  ON fields(is_synthetic);

-- ──────────────────────────────────────────────
-- Crops & Calendars
-- ──────────────────────────────────────────────

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

-- One active crop-season per field (supports future multi-crop)
-- This is the Phase-2 addition that the Crop Agent reads.
CREATE TABLE field_crops (
    field_crop_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    field_id         INTEGER NOT NULL REFERENCES fields(field_id),
    crop_id          INTEGER NOT NULL REFERENCES crops(crop_id),
    variety          TEXT,
    sowing_date      TEXT,                  -- ISO date
    current_stage    TEXT,
    recommendation_type TEXT,               -- maps to fertilizer_recommendations
    target_yield_kg_ha NUMERIC,
    is_active        BOOLEAN DEFAULT 1,
    created_at       TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at       TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_field_crops_field  ON field_crops(field_id);
CREATE INDEX idx_field_crops_active ON field_crops(field_id, is_active);

-- Convenience view: latest active crop per field
-- Used by orchestrator to load field state in one query.
CREATE VIEW field_active_crop AS
SELECT
    f.field_id,
    f.field_code,
    f.area_ha,
    f.soil_type,
    f.irrigation_type,
    f.lat,
    f.lon,
    f.region_id,
    f.district_id,
    f.taluka_id,
    f.farmer_id,
    f.is_synthetic,
    fc.field_crop_id,
    fc.crop_id          AS current_crop_id,
    fc.variety          AS current_variety,
    fc.sowing_date,
    fc.current_stage,
    fc.recommendation_type,
    fc.target_yield_kg_ha
FROM fields f
LEFT JOIN field_crops fc
    ON fc.field_id = f.field_id AND fc.is_active = 1;

-- ──────────────────────────────────────────────
-- Fertilizers
-- ──────────────────────────────────────────────

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
    notes           TEXT,
    -- CHECK constraints to guard against obviously wrong values
    CHECK (n_kg_ha IS NULL  OR n_kg_ha  >= 0),
    CHECK (p2o5_kg_ha IS NULL OR p2o5_kg_ha >= 0),
    CHECK (k2o_kg_ha IS NULL  OR k2o_kg_ha  >= 0)
);

-- ──────────────────────────────────────────────
-- Soil Tests & Fertilizer Applications
-- ──────────────────────────────────────────────

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
    moisture_percent NUMERIC,
    micronutrients  TEXT,                   -- JSON string
    source          TEXT DEFAULT 'SYNTHETIC',  -- 'lab'|'ocr'|'manual'|'SYNTHETIC'
    ocr_confidence  NUMERIC,
    original_file_path TEXT,
    is_synthetic    BOOLEAN DEFAULT 0,
    label_note      TEXT,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
    -- CHECK: realistic agronomic bounds
    CHECK (ph IS NULL OR (ph >= 3.0 AND ph <= 11.0)),
    CHECK (oc_percent IS NULL OR oc_percent >= 0)
);

CREATE INDEX idx_soil_tests_field ON soil_tests(field_id, test_date DESC);

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
    is_synthetic    BOOLEAN DEFAULT 0,
    CHECK (quantity_kg_ha IS NULL OR quantity_kg_ha >= 0)
);

CREATE INDEX idx_applications_field ON applications(field_id, application_date DESC);

-- ──────────────────────────────────────────────
-- Nutrient Ledger & Recommendations
-- ──────────────────────────────────────────────

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
    flags               TEXT,               -- JSON array of flag strings
    confidence          TEXT,               -- HIGH|MEDIUM|LOW|ABSTAIN
    is_synthetic        BOOLEAN DEFAULT 0,
    created_at          TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ledger_field ON nutrient_ledger_entries(field_id, created_at DESC);

CREATE TABLE recommendations (
    recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_id        INTEGER NOT NULL REFERENCES fields(field_id),
    ledger_id       INTEGER REFERENCES nutrient_ledger_entries(ledger_id),
    generated_at    TEXT DEFAULT CURRENT_TIMESTAMP,
    plan_json       TEXT NOT NULL,          -- full proof-carrying object (JSON)
    total_cost_estimate NUMERIC,
    confidence      TEXT,                   -- HIGH|MEDIUM|LOW|ABSTAIN
    confidence_reason TEXT,
    evidence_citations TEXT,                -- JSON array of citation strings
    flags           TEXT,                   -- JSON array
    is_synthetic    BOOLEAN DEFAULT 0,
    status          TEXT DEFAULT 'PROPOSED', -- PROPOSED|ABSTAINED|NO_FERTILIZER_NEEDED|SUPERSEDED
    -- Phase-2: lifecycle tracking for Monitoring Agent
    invalidated_at  TEXT,                   -- ISO timestamp when Monitoring Agent superseded this
    superseded_by   INTEGER REFERENCES recommendations(recommendation_id),
    CHECK (status IN ('PROPOSED','ABSTAINED','NO_FERTILIZER_NEEDED','SUPERSEDED'))
);

CREATE INDEX idx_recs_field_latest ON recommendations(field_id, generated_at DESC);

-- ──────────────────────────────────────────────
-- Weather Snapshots (Weather Agent)
-- ──────────────────────────────────────────────

CREATE TABLE weather_snapshots (
    snapshot_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    field_id            INTEGER NOT NULL REFERENCES fields(field_id),
    fetched_at          TEXT NOT NULL,      -- ISO timestamp (UTC)
    forecast_json       TEXT,               -- raw Open-Meteo JSON response
    rainfall_probability NUMERIC,           -- max precipitation_probability_max (0-100)
    rainfall_mm_next_7d  NUMERIC,           -- sum of precipitation_sum (mm)
    heavy_rain_alert    BOOLEAN DEFAULT 0,
    source              TEXT DEFAULT 'open-meteo',
    created_at          TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_weather_field ON weather_snapshots(field_id, fetched_at DESC);

-- ──────────────────────────────────────────────
-- Events (Monitoring Agent event bus)
-- ──────────────────────────────────────────────
-- Stores every event the system emits. Monitoring Agent polls / reacts to these.
-- Event types: SOIL_REPORT_UPDATED | WEATHER_FORECAST_CHANGED | HEAVY_RAIN_ALERT |
--              CROP_STAGE_CHANGED | FERTILIZER_APPLIED | IRRIGATION_RECORDED |
--              PLAN_CREATED | PLAN_INVALIDATED | RECOMMENDATION_RECALCULATED |
--              EXPERT_OVERRIDE

CREATE TABLE events (
    event_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type      TEXT NOT NULL,
    field_id        INTEGER REFERENCES fields(field_id),
    payload         TEXT,                   -- JSON payload
    actor           TEXT DEFAULT 'system',  -- system|farmer|agronomist
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_events_field ON events(field_id, created_at DESC);
CREATE INDEX idx_events_type  ON events(event_type, created_at DESC);

-- ──────────────────────────────────────────────
-- Alerts (human-visible notifications)
-- ──────────────────────────────────────────────

CREATE TABLE alerts (
    alert_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    field_id        INTEGER REFERENCES fields(field_id),
    alert_type      TEXT NOT NULL,
    severity        TEXT,                   -- HIGH|MEDIUM|LOW
    message         TEXT,
    triggered_at    TEXT DEFAULT CURRENT_TIMESTAMP,
    resolved_at     TEXT,
    related_recommendation_id INTEGER REFERENCES recommendations(recommendation_id),
    CHECK (severity IN ('HIGH','MEDIUM','LOW',NULL))
);

-- ──────────────────────────────────────────────
-- Audit Log
-- ──────────────────────────────────────────────

CREATE TABLE audit_log (
    audit_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type     TEXT NOT NULL,          -- 'recommendation'|'soil_test'|'field_crop'|…
    entity_id       INTEGER,
    action          TEXT NOT NULL,          -- 'CREATE'|'UPDATE'|'SUPERSEDE'|…
    actor           TEXT DEFAULT 'system',  -- system|farmer|agronomist
    old_value       TEXT,                   -- JSON
    new_value       TEXT,                   -- JSON
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP
);

-- ──────────────────────────────────────────────
-- Soil report OCR uploads (doc 11)
-- Never written to soil_tests until farmer confirms.
-- ──────────────────────────────────────────────

CREATE TABLE soil_report_uploads (
    upload_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    field_id            INTEGER NOT NULL REFERENCES fields(field_id),
    original_file_path  TEXT,
    extracted_json      TEXT NOT NULL,      -- per-field {value, confidence}
    status              TEXT NOT NULL DEFAULT 'PENDING_CONFIRMATION',
    -- PENDING_CONFIRMATION | CONFIRMED | REJECTED | OCR_FAILED
    created_at          TEXT DEFAULT CURRENT_TIMESTAMP,
    confirmed_at        TEXT,
    soil_test_id        INTEGER REFERENCES soil_tests(soil_test_id),
    CHECK (status IN ('PENDING_CONFIRMATION','CONFIRMED','REJECTED','OCR_FAILED'))
);

CREATE INDEX idx_soil_uploads_field ON soil_report_uploads(field_id, created_at DESC);
