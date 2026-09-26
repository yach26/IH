# 03 — Database Schema & Data Architecture

## 1. Current State (SQLite Prototype)

The working prototype uses `schema_sqlite.sql` which is a direct port of the frozen Postgres design.

Key tables already present and populated:

| Table | Purpose |
|-------|---------|
| `farmers` | Farmer identity |
| `fields` | Field identity + region_id + area |
| `crops` | Crop master data |
| `soil_tests` | N, P, K, pH, OC, test_date, source |
| `fertilizer_recommendations` | RDF requirements + `source_citation` |
| `fertilizer_products` | FCO NPK % (Urea, DAP, MOP, ...) |
| `nutrient_ledger_entries` | Results of ledger runs |
| `recommendations` | Full proof-carrying plans (JSON + flags + confidence) |

**Rule**: Keep the schema identical when moving to Postgres. Only change the connection layer.

---

## 2. Target Production Schema (PostgreSQL)

```sql
-- Core identity
CREATE TABLE farmers (
  farmer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  phone TEXT,
  preferred_language TEXT DEFAULT 'mr',   -- mr | en
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE fields (
  field_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  farmer_id UUID REFERENCES farmers(farmer_id),
  region_id TEXT NOT NULL,                -- 'kolhapur' | 'jalgaon' | ...
  name TEXT,
  area_ha NUMERIC(8,2),
  soil_type TEXT,
  location GEOGRAPHY(POINT, 4326),        -- optional for MVP
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Crop state (one active crop per field for MVP)
CREATE TABLE field_crops (
  field_crop_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  field_id UUID REFERENCES fields(field_id),
  crop_code TEXT NOT NULL,
  variety TEXT,
  sowing_date DATE,
  current_stage TEXT,
  target_yield_kg_ha NUMERIC,
  is_active BOOLEAN DEFAULT true
);

-- Soil
CREATE TABLE soil_tests (
  soil_test_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  field_id UUID REFERENCES fields(field_id),
  test_date DATE NOT NULL,
  n_kg_ha NUMERIC,
  p_kg_ha NUMERIC,                        -- currently treated as proxy for P2O5
  k_kg_ha NUMERIC,
  ph NUMERIC,
  oc_percent NUMERIC,
  ec NUMERIC,
  moisture_percent NUMERIC,
  micronutrients JSONB,
  source TEXT,                            -- 'lab' | 'ocr' | 'manual'
  ocr_confidence NUMERIC,
  original_file_path TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Applications & history
CREATE TABLE fertilizer_applications (
  application_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  field_id UUID REFERENCES fields(field_id),
  product_code TEXT,
  quantity_kg_ha NUMERIC,
  applied_at DATE,
  recorded_at TIMESTAMPTZ DEFAULT now()
);

-- Knowledge & recommendations (static + generated)
CREATE TABLE fertilizer_recommendations (
  rec_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  crop_id UUID,                           -- or crop_code
  recommendation_type TEXT,               -- e.g. 'basal', 'tillering'
  n_kg_ha NUMERIC,
  p2o5_kg_ha NUMERIC,
  k2o_kg_ha NUMERIC,
  source_citation TEXT NOT NULL,          -- critical for proof-carrying
  notes TEXT
);

CREATE TABLE fertilizer_products (
  product_code TEXT PRIMARY KEY,
  name TEXT,
  n_percent NUMERIC,
  p2o5_percent NUMERIC,
  k2o_percent NUMERIC,
  source TEXT                             -- FCO
);

-- Ledger results & plans
CREATE TABLE nutrient_ledger_entries (
  entry_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  field_id UUID REFERENCES fields(field_id),
  soil_test_id UUID,
  required JSONB,
  available JSONB,
  gap JSONB,
  flags TEXT[],
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE recommendations (
  recommendation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  field_id UUID REFERENCES fields(field_id),
  status TEXT,                            -- PLAN_GENERATED | ABSTAIN | NO_FERTILIZER_NEEDED
  plan_json JSONB,                        -- full proof-carrying object
  confidence TEXT,                        -- HIGH | MEDIUM | LOW | ABSTAIN
  flags TEXT[],
  evidence_citations JSONB,
  created_at TIMESTAMPTZ DEFAULT now(),
  invalidated_at TIMESTAMPTZ,             -- set by Monitoring Agent
  superseded_by UUID                      -- points to newer recommendation
);

-- Events & audit
CREATE TABLE events (
  event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type TEXT NOT NULL,               -- SOIL_REPORT_UPDATED, HEAVY_RAIN_ALERT, ...
  field_id UUID REFERENCES fields(field_id),
  payload JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE audit_log (
  audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_type TEXT,
  entity_id UUID,
  action TEXT,
  actor TEXT,                             -- system | farmer | agronomist
  old_value JSONB,
  new_value JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 3. Supporting Stores

| Store | Purpose | Technology (Hackathon) | Production |
|-------|---------|------------------------|------------|
| PostgreSQL | Transactional state, twin, recommendations, audit | SQLite for local, Postgres in Docker | Postgres |
| Vector DB | Agricultural knowledge chunks | FAISS or Chroma (local) | Qdrant / pgvector |
| Object Storage | Soil report images/PDFs, source documents | Local `uploads/` folder | S3 / MinIO |
| Cache | Weather snapshots, repeated queries | Redis or in-memory dict | Redis |
| Time-series (optional) | IoT sensor readings | Skip for MVP | TimescaleDB |

**Do not** put everything into the vector database.

---

## 4. Region Configuration (File-based for speed)

```
regions/{region_id}/
├── config.yaml                 # crops grown, default language, weather station ids
├── crops/                      # crop calendars, stage definitions
├── agronomic_rules/            # hard limits, compatibility rules
├── knowledge_sources/          # PDFs / markdown fed into RAG ingestion
├── soil_datasets/              # optional government soil-health-card extracts
└── geospatial_metadata/        # bounding boxes, satellite suitability notes
```

At runtime the Orchestrator loads `region_id` from the field and injects the corresponding config into agents.

---

## 5. Migration Path

1. Keep SQLite for local development and the current demo (`agrotwin.db`).
2. Introduce SQLAlchemy (or raw asyncpg) models that work with both SQLite and Postgres.
3. Provide a `docker-compose.yml` with Postgres + Redis for the full stack.
4. Seed script must work against both backends.
5. Use Alembic (or simple SQL migration files) once the schema stabilises.

---

## 6. Implementation Checklist

- [ ] Formalise the full Postgres DDL matching current SQLite + new event/audit tables.
- [ ] Ensure every `recommendations` row stores the complete proof-carrying payload in `plan_json`.
- [ ] Add `invalidated_at` and `superseded_by` so the Monitoring Agent can mark plans stale.
- [ ] Index on `(field_id, created_at DESC)` for “latest active plan” lookups.
- [ ] Add foreign-key constraints and basic check constraints (confidence values, status values).
- [ ] Write a small migration script from current SQLite → Postgres.
