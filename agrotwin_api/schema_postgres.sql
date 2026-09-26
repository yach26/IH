-- ============================================================
-- AgroTwin AI — PostgreSQL DDL (Phase-2, matches schema_sqlite.sql)
-- Apply with: psql -d agrotwin -f schema_postgres.sql
-- This is the Postgres-native DDL for production deployment.
-- Types mapped back from SQLite: TEXT→UUID/TIMESTAMPTZ/JSONB,
-- INTEGER PK → UUID DEFAULT gen_random_uuid(), NUMERIC stays NUMERIC.
-- ============================================================

-- Requires: pgcrypto (for gen_random_uuid on PG < 13)
-- CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ──────────────────────────────────────────────
-- Geography
-- ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS regions (
    region_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    region_code     TEXT UNIQUE NOT NULL,
    region_name     TEXT NOT NULL,
    country_code    TEXT DEFAULT 'IN',
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS districts (
    district_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    region_id       UUID NOT NULL REFERENCES regions(region_id),
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
    taluka_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    district_id     UUID NOT NULL REFERENCES districts(district_id),
    taluka_code     TEXT NOT NULL,
    taluka_name     TEXT NOT NULL,
    is_pilot        BOOLEAN DEFAULT FALSE,
    UNIQUE (district_id, taluka_code)
);

-- ──────────────────────────────────────────────
-- Farmers & Fields
-- ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS farmers (
    farmer_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    region_id       UUID NOT NULL REFERENCES regions(region_id),
    full_name       TEXT,
    mobile          TEXT,
    preferred_lang  TEXT DEFAULT 'mr',
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fields (
    field_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    region_id       UUID NOT NULL REFERENCES regions(region_id),
    district_id     UUID NOT NULL REFERENCES districts(district_id),
    taluka_id       UUID REFERENCES talukas(taluka_id),
    farmer_id       UUID REFERENCES farmers(farmer_id),
    field_code      TEXT UNIQUE,
    area_ha         NUMERIC(8,2) NOT NULL,
    soil_type       TEXT,
    irrigation_type TEXT,
    lat             NUMERIC(10,6),
    lon             NUMERIC(10,6),
    location        GEOGRAPHY(POINT, 4326),  -- requires PostGIS, optional for MVP
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
    crop_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crop_code       TEXT UNIQUE NOT NULL,
    crop_name       TEXT NOT NULL,
    scientific_name TEXT,
    is_pilot        BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS crop_calendars (
    calendar_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crop_id         UUID NOT NULL REFERENCES crops(crop_id),
    region_id       UUID REFERENCES regions(region_id),
    stage_name      TEXT NOT NULL,
    stage_order     INTEGER NOT NULL,
    days_after_planting_min INTEGER,
    days_after_planting_max INTEGER,
    notes           TEXT,
    source_file     TEXT DEFAULT '05_Crop_Calendars/four_pilot_crops.md'
);

CREATE TABLE IF NOT EXISTS field_crops (
    field_crop_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    field_id         UUID NOT NULL REFERENCES fields(field_id),
    crop_id          UUID NOT NULL REFERENCES crops(crop_id),
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

-- ──────────────────────────────────────────────
-- Fertilizers
-- ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS fertilizer_products (
    product_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_code    TEXT UNIQUE NOT NULL,
    product_name    TEXT NOT NULL,
    n_percent       NUMERIC(5,2) NOT NULL,
    p2o5_percent    NUMERIC(5,2) NOT NULL,
    k2o_percent     NUMERIC(5,2) NOT NULL,
    notes           TEXT,
    source_file     TEXT DEFAULT '07_Fertilizer_Composition/npk_composition.csv'
);

CREATE TABLE IF NOT EXISTS fertilizer_recommendations (
    rec_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crop_id         UUID NOT NULL REFERENCES crops(crop_id),
    region_id       UUID REFERENCES regions(region_id),
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
    soil_test_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    field_id        UUID NOT NULL REFERENCES fields(field_id),
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
    application_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    field_id        UUID NOT NULL REFERENCES fields(field_id),
    product_id      UUID REFERENCES fertilizer_products(product_id),
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

-- ──────────────────────────────────────────────
-- Ledger & Recommendations
-- ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS nutrient_ledger_entries (
    ledger_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    field_id        UUID NOT NULL REFERENCES fields(field_id),
    entry_date      DATE NOT NULL DEFAULT CURRENT_DATE,
    crop_id         UUID REFERENCES crops(crop_id),
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
    confidence          TEXT CHECK (confidence IN ('HIGH','MEDIUM','LOW','ABSTAIN', NULL)),
    is_synthetic        BOOLEAN DEFAULT FALSE,
    created_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ledger_field ON nutrient_ledger_entries(field_id, created_at DESC);

CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    field_id        UUID NOT NULL REFERENCES fields(field_id),
    ledger_id       UUID REFERENCES nutrient_ledger_entries(ledger_id),
    generated_at    TIMESTAMPTZ DEFAULT now(),
    plan_json       JSONB NOT NULL,
    total_cost_estimate NUMERIC,
    confidence      TEXT CHECK (confidence IN ('HIGH','MEDIUM','LOW','ABSTAIN', NULL)),
    confidence_reason TEXT,
    evidence_citations JSONB,
    flags           JSONB,
    is_synthetic    BOOLEAN DEFAULT FALSE,
    status          TEXT NOT NULL DEFAULT 'PROPOSED'
                    CHECK (status IN ('PROPOSED','ABSTAINED','NO_FERTILIZER_NEEDED','SUPERSEDED')),
    invalidated_at  TIMESTAMPTZ,
    superseded_by   UUID REFERENCES recommendations(recommendation_id)
);

CREATE INDEX IF NOT EXISTS idx_recs_field_latest ON recommendations(field_id, generated_at DESC);

-- ──────────────────────────────────────────────
-- Weather
-- ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS weather_snapshots (
    snapshot_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    field_id            UUID NOT NULL REFERENCES fields(field_id),
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
-- Events & Alerts
-- ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS events (
    event_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type      TEXT NOT NULL,
    field_id        UUID REFERENCES fields(field_id),
    payload         JSONB,
    actor           TEXT DEFAULT 'system',
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_events_field ON events(field_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_type  ON events(event_type, created_at DESC);

CREATE TABLE IF NOT EXISTS alerts (
    alert_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    field_id        UUID REFERENCES fields(field_id),
    alert_type      TEXT NOT NULL,
    severity        TEXT CHECK (severity IN ('HIGH','MEDIUM','LOW', NULL)),
    message         TEXT,
    triggered_at    TIMESTAMPTZ DEFAULT now(),
    resolved_at     TIMESTAMPTZ,
    related_recommendation_id UUID REFERENCES recommendations(recommendation_id)
);

-- ──────────────────────────────────────────────
-- Audit Log
-- ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS audit_log (
    audit_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type     TEXT NOT NULL,
    entity_id       UUID,
    action          TEXT NOT NULL,
    actor           TEXT DEFAULT 'system',
    old_value       JSONB,
    new_value       JSONB,
    created_at      TIMESTAMPTZ DEFAULT now()
);
