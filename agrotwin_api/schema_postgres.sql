-- ============================================================
-- AgroTwin AI — PostgreSQL DDL (Production / NeonDB)
--
-- CRITICAL DRIFT GUARD:
-- schema_sqlite.sql and schema_postgres.sql MUST be kept structurally identical.
-- Integer primary keys (SERIAL) and integer foreign keys are used consistently
-- across both engines to ensure full compatibility with the application layer.
--
-- Apply with: psql $DATABASE_URL -f schema_postgres.sql
-- ============================================================

-- ──────────────────────────────────────────────
-- Geography / Admin hierarchy
-- ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS regions (
    region_id       SERIAL PRIMARY KEY,
    region_code     TEXT UNIQUE NOT NULL,
    region_name     TEXT NOT NULL,
    country_code    TEXT DEFAULT 'IN',
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS districts (
    district_id     SERIAL PRIMARY KEY,
    region_id       INTEGER NOT NULL REFERENCES regions(region_id),
    district_code   TEXT UNIQUE NOT NULL,
    district_name   TEXT NOT NULL,
    area_km2        NUMERIC,
    lat_min         NUMERIC,
    lat_max         NUMERIC,
    lon_min         NUMERIC,
    lon_max         NUMERIC,
    agro_zones_json JSONB,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS talukas (
    taluka_id       SERIAL PRIMARY KEY,
    district_id     INTEGER NOT NULL REFERENCES districts(district_id),
    taluka_code     TEXT NOT NULL,
    taluka_name     TEXT NOT NULL,
    is_pilot        BOOLEAN DEFAULT FALSE,
    UNIQUE (district_id, taluka_code)
);

-- ──────────────────────────────────────────────
-- Farmers & Fields
-- ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS farmers (
    farmer_id       SERIAL PRIMARY KEY,
    region_id       INTEGER NOT NULL REFERENCES regions(region_id),
    full_name       TEXT,
    mobile          TEXT,
    preferred_lang  TEXT DEFAULT 'mr',
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fields (
    field_id        SERIAL PRIMARY KEY,
    region_id       INTEGER NOT NULL REFERENCES regions(region_id),
    district_id     INTEGER NOT NULL REFERENCES districts(district_id),
    taluka_id       INTEGER REFERENCES talukas(taluka_id),
    farmer_id       INTEGER REFERENCES farmers(farmer_id),
    field_code      TEXT UNIQUE,
    area_ha         NUMERIC(8,2) NOT NULL,
    soil_type       TEXT,
    irrigation_type TEXT,
    lat             NUMERIC(10,6),
    lon             NUMERIC(10,6),
    is_synthetic    BOOLEAN DEFAULT FALSE,
    label_note      TEXT,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_fields_district   ON fields(district_id);
CREATE INDEX IF NOT EXISTS idx_fields_synthetic  ON fields(is_synthetic);

-- ──────────────────────────────────────────────
-- Crops & Calendars
-- ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS crops (
    crop_id         SERIAL PRIMARY KEY,
    crop_code       TEXT UNIQUE NOT NULL,
    crop_name       TEXT NOT NULL,
    scientific_name TEXT,
    is_pilot        BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS crop_calendars (
    calendar_id     SERIAL PRIMARY KEY,
    crop_id         INTEGER NOT NULL REFERENCES crops(crop_id),
    region_id       INTEGER REFERENCES regions(region_id),
    stage_name      TEXT NOT NULL,
    stage_order     INTEGER NOT NULL,
    days_after_planting_min INTEGER,
    days_after_planting_max INTEGER,
    notes           TEXT,
    source_file     TEXT DEFAULT '05_Crop_Calendars/four_pilot_crops.md'
);

-- Active crop season per field
CREATE TABLE IF NOT EXISTS field_crops (
    field_crop_id    SERIAL PRIMARY KEY,
    field_id         INTEGER NOT NULL REFERENCES fields(field_id),
    crop_id          INTEGER NOT NULL REFERENCES crops(crop_id),
    variety          TEXT,
    sowing_date      DATE,
    current_stage    TEXT,
    recommendation_type TEXT,
    target_yield_kg_ha NUMERIC,
    is_active        BOOLEAN DEFAULT TRUE,
    created_at       TIMESTAMPTZ DEFAULT now(),
    updated_at       TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_field_crops_field  ON field_crops(field_id);
CREATE INDEX IF NOT EXISTS idx_field_crops_active ON field_crops(field_id, is_active);

-- Convenience view matching SQLite view
CREATE OR REPLACE VIEW field_active_crop AS
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
    ON fc.field_id = f.field_id AND fc.is_active = TRUE;

-- ──────────────────────────────────────────────
-- Fertilizers
-- ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS fertilizer_products (
    product_id      SERIAL PRIMARY KEY,
    product_code    TEXT UNIQUE NOT NULL,
    product_name    TEXT NOT NULL,
    n_percent       NUMERIC NOT NULL,
    p2o5_percent    NUMERIC NOT NULL,
    k2o_percent     NUMERIC NOT NULL,
    notes           TEXT,
    source_file     TEXT DEFAULT '07_Fertilizer_Composition/npk_composition.csv'
);

CREATE TABLE IF NOT EXISTS fertilizer_recommendations (
    rec_id          SERIAL PRIMARY KEY,
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
    CHECK (n_kg_ha IS NULL  OR n_kg_ha  >= 0),
    CHECK (p2o5_kg_ha IS NULL OR p2o5_kg_ha >= 0),
    CHECK (k2o_kg_ha IS NULL  OR k2o_kg_ha  >= 0)
);

-- ──────────────────────────────────────────────
-- Soil Tests & Applications
-- ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS soil_tests (
    soil_test_id    SERIAL PRIMARY KEY,
    field_id        INTEGER NOT NULL REFERENCES fields(field_id),
    test_date       DATE NOT NULL,
    n_kg_ha         NUMERIC,
    p_kg_ha         NUMERIC,
    k_kg_ha         NUMERIC,
    ph              NUMERIC,
    oc_percent      NUMERIC,
    ec_ds_m         NUMERIC,
    moisture_percent NUMERIC,
    micronutrients  JSONB,
    source          TEXT DEFAULT 'SYNTHETIC',
    ocr_confidence  NUMERIC,
    original_file_path TEXT,
    is_synthetic    BOOLEAN DEFAULT FALSE,
    label_note      TEXT,
    created_at      TIMESTAMPTZ DEFAULT now(),
    CHECK (ph IS NULL OR (ph >= 3.0 AND ph <= 11.0)),
    CHECK (oc_percent IS NULL OR oc_percent >= 0)
);

CREATE INDEX IF NOT EXISTS idx_soil_tests_field ON soil_tests(field_id, test_date DESC);

CREATE TABLE IF NOT EXISTS applications (
    application_id  SERIAL PRIMARY KEY,
    field_id        INTEGER NOT NULL REFERENCES fields(field_id),
    product_id      INTEGER REFERENCES fertilizer_products(product_id),
    application_date DATE,
    quantity_kg     NUMERIC,
    quantity_kg_ha  NUMERIC,
    n_supplied_kg_ha NUMERIC,
    p2o5_supplied_kg_ha NUMERIC,
    k2o_supplied_kg_ha NUMERIC,
    notes           TEXT,
    is_synthetic    BOOLEAN DEFAULT FALSE,
    CHECK (quantity_kg_ha IS NULL OR quantity_kg_ha >= 0)
);

CREATE INDEX IF NOT EXISTS idx_applications_field ON applications(field_id, application_date DESC);

-- ──────────────────────────────────────────────
-- Nutrient Ledger & Recommendations
-- ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS nutrient_ledger_entries (
    ledger_id       SERIAL PRIMARY KEY,
    field_id        INTEGER NOT NULL REFERENCES fields(field_id),
    entry_date      DATE NOT NULL DEFAULT CURRENT_DATE,
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
    flags               JSONB,
    confidence          TEXT,
    is_synthetic        BOOLEAN DEFAULT FALSE,
    created_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ledger_field ON nutrient_ledger_entries(field_id, created_at DESC);

CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id SERIAL PRIMARY KEY,
    field_id        INTEGER NOT NULL REFERENCES fields(field_id),
    ledger_id       INTEGER REFERENCES nutrient_ledger_entries(ledger_id),
    generated_at    TIMESTAMPTZ DEFAULT now(),
    plan_json       JSONB NOT NULL,
    total_cost_estimate NUMERIC,
    confidence      TEXT,
    confidence_reason TEXT,
    evidence_citations JSONB,
    flags           JSONB,
    is_synthetic    BOOLEAN DEFAULT FALSE,
    status          TEXT DEFAULT 'PROPOSED',
    invalidated_at  TIMESTAMPTZ,
    superseded_by   INTEGER REFERENCES recommendations(recommendation_id),
    CHECK (status IN ('PROPOSED','ABSTAINED','NO_FERTILIZER_NEEDED','SUPERSEDED','PLAN_GENERATED','PLAN_REVISED'))
);

CREATE INDEX IF NOT EXISTS idx_recs_field_latest ON recommendations(field_id, generated_at DESC);

-- ──────────────────────────────────────────────
-- Weather Snapshots
-- ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS weather_snapshots (
    snapshot_id         SERIAL PRIMARY KEY,
    field_id            INTEGER NOT NULL REFERENCES fields(field_id),
    fetched_at          TIMESTAMPTZ NOT NULL,
    forecast_json       JSONB,
    rainfall_probability NUMERIC,
    rainfall_mm_next_7d  NUMERIC,
    heavy_rain_alert    BOOLEAN DEFAULT FALSE,
    source              TEXT DEFAULT 'open-meteo',
    created_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_weather_field ON weather_snapshots(field_id, fetched_at DESC);

-- ──────────────────────────────────────────────
-- Events & Monitoring
-- ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS events (
    event_id        SERIAL PRIMARY KEY,
    event_type      TEXT NOT NULL,
    field_id        INTEGER REFERENCES fields(field_id),
    payload         JSONB,
    actor           TEXT DEFAULT 'system',
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_events_field ON events(field_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_type  ON events(event_type, created_at DESC);

-- ──────────────────────────────────────────────
-- Alerts
-- ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS alerts (
    alert_id        SERIAL PRIMARY KEY,
    field_id        INTEGER REFERENCES fields(field_id),
    alert_type      TEXT NOT NULL,
    severity        TEXT,
    message         TEXT,
    triggered_at    TIMESTAMPTZ DEFAULT now(),
    resolved_at     TIMESTAMPTZ,
    related_recommendation_id INTEGER REFERENCES recommendations(recommendation_id),
    CHECK (severity IN ('HIGH','MEDIUM','LOW',NULL))
);

-- ──────────────────────────────────────────────
-- Audit Log
-- ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS audit_log (
    audit_id        SERIAL PRIMARY KEY,
    entity_type     TEXT NOT NULL,
    entity_id       INTEGER,
    action          TEXT NOT NULL,
    actor           TEXT DEFAULT 'system',
    old_value       JSONB,
    new_value       JSONB,
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- ──────────────────────────────────────────────
-- Soil Report OCR Uploads
-- ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS soil_report_uploads (
    upload_id           SERIAL PRIMARY KEY,
    field_id            INTEGER NOT NULL REFERENCES fields(field_id),
    original_file_path  TEXT,
    extracted_json      JSONB NOT NULL,
    status              TEXT NOT NULL DEFAULT 'PENDING_CONFIRMATION',
    created_at          TIMESTAMPTZ DEFAULT now(),
    confirmed_at        TIMESTAMPTZ,
    soil_test_id        INTEGER REFERENCES soil_tests(soil_test_id),
    CHECK (status IN ('PENDING_CONFIRMATION','CONFIRMED','REJECTED','OCR_FAILED'))
);

CREATE INDEX IF NOT EXISTS idx_soil_uploads_field ON soil_report_uploads(field_id, created_at DESC);
