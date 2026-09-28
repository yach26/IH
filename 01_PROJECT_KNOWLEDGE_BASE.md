# AgroTwin AI — Complete Project Knowledge Base

This is the exhaustive technical reference for the AgroTwin AI codebase: every
file, what it does, how the pieces connect, and why it's built this way.
Read `02_PROJECT_SUMMARY.md` first if you want the short version.

---

## 1. What the system is

AgroTwin AI is a **Digital Krishi (farm) Twin** — a living, per-field
representation of soil, crop, weather and nutrient history that produces
**proof-carrying fertilizer recommendations**: not just "apply X kg/ha" but
WHAT, HOW MUCH, WHEN, WHY, BASED ON WHAT EVIDENCE, and HOW CERTAIN.

Core design law (from `agrotwin_api`'s own docs and enforced throughout the
code): **the backend/domain state is the single source of truth. Nothing —
not the frontend, not an LLM — is allowed to invent an agronomic number.**
Every kg/ha shown anywhere in the UI traces back to a deterministic
calculation in `ledger.py` / `app/core/nutrient_ledger.py`.

---

## 2. Repository layout

```
IH/
├── agrotwin_api/        ← FastAPI backend (the only active backend — see §3)
├── agrotwin_frontend/    ← Next.js 16 frontend
├── backend/, archive/    ← superseded prototypes, kept for history only
├── docs/                 ← architecture docs (00_CONTEXT.md … 16_FRONTEND_…)
└── PROGRESS.md           ← running, honest changelog of every session's work
```

---

## 3. Backend (`agrotwin_api/`)

### 3.1 Entry point — `app/main.py`
FastAPI app factory. Registers the CORS middleware (`allow_origins=["*"]` —
fine for a hackathon pilot, would need locking down for production), mounts
the single `routes.py` router, and logs startup ("AgroTwin API starting
up…", DB backend chosen).

### 3.2 Database layer — `app/db.py`
One abstraction over **both** SQLite (local dev, what this pilot actually
runs on) and PostgreSQL/NeonDB (cloud option). Switches automatically based
on whether `DATABASE_URL` is set. Handles the SQL dialect differences
(`?` vs `%s` placeholders, `cur.lastrowid` vs Postgres `RETURNING`) so every
other file writes one query and it runs on either engine.

### 3.3 Schema — `schema_sqlite.sql` / `schema_postgres.sql`
Kept byte-for-byte structurally identical (a comment in both files says so
— a "drift guard"). Key tables:

| Table | Purpose |
|---|---|
| `regions`, `districts`, `talukas` | Geography. Originally only Kolhapur/Jalgaon (the two pilot districts with real lat/lon bounding boxes); all other Maharashtra districts plus an "Other" catch-all were added later so a farmer outside the two pilot districts isn't forced into a false one. |
| `farmers` | Farmer records. |
| `fields` | One row per physical field: area, irrigation type, lat/lon, `district_id`/`region_id` (NOT NULL FKs). |
| `crops` | Static crop catalogue: BANANA, SUGARCANE, COTTON, SOYBEAN (no RICE row — the frontend's "Rice" tab was removed for exactly this reason). |
| `field_crops` | The **active crop-season** for a field: `crop_id`, `sowing_date`, `current_stage`, `recommendation_type` (e.g. `PRE_SEASONAL`/`RATOON` for sugarcane), `target_yield_kg_ha`. One field can have history across seasons; `field_active_crop` (a VIEW) always returns the current one. |
| `crop_calendars` | Sourced day-after-planting stage ranges (see §3.6) — powers dynamic stage computation. |
| `soil_tests` | Every confirmed soil test for a field (N/P/K/pH/OC/EC, `source`: lab/ocr/manual). |
| `fertilizer_recommendations` | The RDF (Recommended Dose of Fertilizer) table: `crop_id` + `recommendation_type` → `n_kg_ha`/`p2o5_kg_ha`/`k2o_kg_ha` + `source_citation`. This is the single authoritative source of "how much fertilizer a crop needs" — sourced from MPKV/ICAR documents, never invented. |
| `fertilizer_products` | DAP/UREA/MOP/SSP with their real N/P₂O₅/K₂O percentages (FCO composition spec). |
| `recommendations` | Every recommendation ever generated for a field — the full proof-carrying JSON object (`plan_json`), status (`PROPOSED`/`SUPERSEDED`/`ABSTAINED`/…), confidence, citations. This is the audit trail the dashboard's "Recommendation History" panel reads. |
| `weather_snapshots` | Persisted Open-Meteo fetches per field (7-day rainfall, heavy-rain flag). |
| `alerts`, `events`, `audit_log` | Event-bus side effects: monitoring-triggered replans, agronomist overrides, etc. |
| `applications` | Farmer-recorded fertilizer applications, used for residual-nutrient credit. |

### 3.4 The Nutrient Ledger — the deterministic core

Two files implement the same math, kept in sync intentionally:
- **`ledger.py`** (repo root of `agrotwin_api`) — a thin compatibility
  shim re-exporting from `app/core/nutrient_ledger.py`, used by the original
  seed/demo scripts.
- **`app/core/nutrient_ledger.py`** — the real, active implementation.
- **`app/core/nutrients.py`** — unit normalization. Soil tests report
  **elemental** P and K; the RDF table and fertilizer composition use
  **oxide** form (P₂O₅, K₂O). `normalize()` converts using the sourced FAO
  ratios (P×2.2919, K×1.2046 — `CONVERSION_SOURCE` constant cites
  FAO aq348e Appendix Table 16). This conversion is applied **everywhere**
  nutrients are compared (soil-health scoring, the ledger, `/twin`) — a
  single canonical representation, not five different ad-hoc conversions.
- **`ledger.get_recommendation(conn, crop_code, rec_type)`** — looks up the
  RDF target for a crop+stage. Returns `None` (→ ABSTAIN) if no row exists;
  never guesses a universal number.
- **`compute_gap()`** → `actionable_gap()` — `gap = required − soil − credits`,
  clamped at 0 (never negative). `credits` come from
  **`app/core/application_history.py`**'s `residual_credit()`: if the farmer
  has recorded a previous fertilizer application recently enough (per an
  explicit, reviewed `AGROTWIN_RESIDUAL_POLICY` config — not a guessed
  percentage), some of it is credited against the new gap instead of being
  double-counted.
- **`convert_gap_to_products()`** — the default heuristic optimizer:
  DAP first (to cover P₂O₅), then Urea for any remaining N, then MOP for K.
- **`run_field_ledger()`** (in `ledger.py`) — the actual per-field entry
  point: fetches the latest soil test, resolves residual credits, builds a
  `field_meta` dict, and calls the raw `run_field()` ledger function. Returns
  ABSTAIN with a specific reason (no crop assigned / no rec_type / no soil
  test / no RDF row) rather than ever fabricating a plan.

### 3.5 The Multi-Agent Pipeline — `app/pipeline.py`

`RecommendationPipeline.run()` is the single orchestrator every
recommendation (full or partial replan) goes through. Sequence:

```
Soil Agent → Crop Agent → Weather Agent → Nutrient Ledger → Optimizer
  → Validation (rules) → Knowledge Agent (RAG evidence) → Confidence
  → Report Agent (narrative) → Persist (recommendations table) → Publish event
```

- **`app/agents/soil_agent.py`** — reads the latest soil test, flags
  `STALE_SOIL_DATA` if older than an explicit `ENGINEERING_DEFAULT` threshold
  (180 days).
- **`app/agents/crop_agent.py`** — reads the active crop/stage. Also owns
  **`resolve_dynamic_stage()`**: computes the field's real growth stage from
  `days_after_planting = today − sowing_date` against the sourced
  `crop_calendars` table, so a field's stage genuinely advances over time
  instead of being frozen at whatever was declared once. Falls back to the
  declared stage if there's no sourced calendar for that crop (Soybean has
  none — never invented).
- **`app/agents/weather_agent.py`** — Open-Meteo integration. 15-minute
  in-memory cache + a persisted `weather_snapshots` row. `get_weather_context()`
  needs only lat/lon (independent of soil/crop/recommendation state) —
  `/twin` now calls it directly on first load so weather doesn't stay
  "unavailable" just because `/recommend` was never run.
- **`app/core/optimizer.py`** (Protocol/interface) + **`app/agents/optimizer.py`**
  (`ScipyLinprogOptimizer`) — an alternative to the DAP→Urea→MOP heuristic:
  a real linear program (via SciPy `highs`) minimizing total fertilizer
  *weight* (not cost — no fertilizer price table has been sourced, and the
  code explicitly refuses to invent one; see `04_remaining_gaps.md` Gap #8).
  Selectable per-request (`optimizer: "heuristic" | "linprog"`).
- **`app/core/rules.py`** (`RuleEngine`) — hard/warning constraint checks
  (e.g. weather conflicts with application window, pH extremes) driven by
  `region_config.py`, not hardcoded.
- **`app/agents/validation_agent.py`** — runs the RuleEngine against the
  proposed plan, adds flags, can force ABSTAIN on a HARD violation.
- **`app/agents/knowledge_agent.py`** — the RAG layer (§3.7).
- **`app/agents/rag_validation_agent.py`** — checks whether the retrieved
  evidence actually matches the crop/region being recommended for; never
  blocks the plan, only downgrades confidence with a flag if evidence is
  thin or mismatched.
- **Confidence** (`app/core/proof.py`'s `compute_confidence`, called from
  `pipeline.py`) — HIGH/MEDIUM/LOW/ABSTAIN based on the **count** of
  flags accumulated. Flags from `soil_agent`, `validation_agent`, and
  `rules.py` are **deduplicated by leading code** before counting (fixed
  this project cycle — the same underlying issue, e.g. `STALE_SOIL_DATA`,
  was previously raised by two different agents and double-counted).
- **`app/agents/report_agent.py`** — `compile_report()` turns the proof
  object into a farmer-readable narrative. Never invents a kg/ha number —
  every quantity is copied from the already-computed plan.
- **`app/core/proof.py`** — `assemble_proof()` builds the final JSON shape
  every consumer (`/twin`, `/recommend`, `/what-if`, the frontend) expects:
  `status`, `what`, `how_much`, `when`, `why` (soil/crop/gap detail),
  `based_on` (citation + cost estimate), `confidence`, `flags`,
  `required_actions`.
- **`app/agents/monitoring_agent.py`** — listens on the event bus
  (`app/core/event_bus.py` / `events.py`) for triggers like
  `HEAVY_RAIN_ALERT`, `SOIL_REPORT_UPDATED`, `FERTILIZER_APPLIED`,
  `CROP_STAGE_CHANGED`; runs a **selective partial replan** (only the
  relevant agents re-run, e.g. weather+optimizer+validation for a rain
  event) rather than the whole pipeline, marks the old recommendation
  `SUPERSEDED`, and raises an `alerts` row.

### 3.6 Sourced reference data (never invented)

- **`rag/docs/crop_calendars.md`** — ICAR-NRRI + MPKV Rahuri Extension
  Bulletins (2022): stage timelines for Rice, Sugarcane, Cotton, Banana.
  Used both for RAG evidence citations **and** to seed the `crop_calendars`
  table (`seed_data.seed_crop_calendars()`) that drives dynamic stage
  resolution.
- **`rag/docs/mpkv_icar_rdf.md`**, **`jalgaon_rdf.md`** — the RDF numbers
  themselves (N/P₂O₅/K₂O per crop/stage) that seed `fertilizer_recommendations`.
- **`rag/docs/fco_fertilizer_spec.md`** — real Fertilizer Control Order
  product composition percentages, seeding `fertilizer_products`.
- **`data/real_kolhapur/`** — real Polgaon (Kolhapur) soil-test records
  (2016–2024) and district nutrient-dashboard statistics
  (`app/core/kolhapur_context.py` reads these) — used to ground the RAG
  knowledge base and the yield model's training data in real regional
  numbers, not synthetic ones.

### 3.7 Agentic RAG — `agrotwin_api/rag/`

`rag/ingestion.py` builds a **hybrid BM25 + dense-embedding** index (dense
half via `sentence-transformers` + `faiss-cpu`; gracefully falls back to
BM25-only if those optional packages aren't installed) over the markdown
docs in `rag/docs/`. `knowledge_agent.retrieve_evidence()` queries it with
crop/region/stage filters, retries without the filter if the strict query
returns nothing, and returns citation + excerpt pairs — this is what backs
every "Source: 06_Fertilizer_Recommendations/mpkv_icar_rdf.md, …" citation
shown in the UI.

### 3.8 OCR pipeline — `app/core/ocr.py`, `app/agents/soil_report_agent.py`

Handles the "Upload Soil Report" flow: accepts image/PDF, tries direct PDF
text extraction first (`pypdf`), falls back to `easyocr` for scanned
images, regex-extracts N/P/K/pH/OC/EC values, computes a **per-field
confidence score**, and flags any field below 0.85 confidence as
`fields_needing_review`. Nothing is written to the field's real soil record
until the farmer explicitly calls `/soil-report/confirm` — low-confidence
OCR values are never auto-accepted.

### 3.9 Yield model — `app/yield_prediction.py` + `ml/`

One XGBoost regressor **per crop** (Banana/Sugarcane/Cotton/Soybean),
trained on real Polgaon soil data + published Kolhapur yield averages
(see `ml/model_card.md`). Explicitly **read-only annotation** — "The Ledger
remains the fertilizer authority" (file's own docstring). ABSTAINs
(`predicted_yield_kg_ha: null`) outside its supported crop/district scope
rather than extrapolating. Runs as a subprocess with a timeout and a
bounded semaphore (max 2 concurrent) so a slow/hanging model call can't
take down the API.

### 3.10 What-If simulator — `app/core/what_if.py` + the `/what-if` route

Re-runs the same `RecommendationPipeline` with a modified
`fertilizer_delta_pct`/`rainfall_mm`, **never persists** the simulated
result as the active recommendation. Scales the already-computed plan by
`1 + pct/100` — meaning a field whose real nutrient gap is already 0 (soil
sufficient) stays at 0 no matter what percentage is requested, which is
agronomically correct (there's nothing to scale).

### 3.11 API surface — `app/api/routes.py` (~40 endpoints)

The single router file. Key groups:

| Group | Endpoints |
|---|---|
| Field lifecycle | `POST /farmers`, `POST /fields`, `GET /fields`, `GET /onboarding/options` |
| Digital Twin | `GET /fields/{id}/twin` — the one endpoint the whole dashboard is built from |
| Recommendation | `POST /fields/{id}/recommend`, `GET /fields/{id}/recommendations/latest`, **`GET /fields/{id}/recommendations`** (full history — added this cycle), `GET /recommend/{id}` (GET alias) |
| Oversight | **`POST /fields/{id}/override`** (agronomist override — existed server-side for a long time, only recently exposed in the UI; fixed this cycle to store a full proof-shaped `plan_json` instead of a bare dict so `/twin` can actually read it back) |
| Simulation | `POST /fields/{id}/what-if` |
| Soil data | `POST /fields/{id}/soil-report/upload`, `POST /fields/{id}/soil-report/confirm` |
| Crop | `POST /fields/{id}/crop` (assign/update active crop+stage) |
| Monitoring | `POST /events` (inject a demo event), `GET /fields/{id}/alerts`, `GET /alerts` (fleet-wide) |
| Misc | `GET /fields/{id}/yield-estimate`, `GET /fields/{id}/applications`, `POST /fields/{id}/applications`, `GET /fertilizer-products`, `/ocr/*` (standalone OCR test endpoints) |

`_field_row()` is the single helper almost every endpoint calls first — it
fetches the field's row from the `field_active_crop` view **and** now also
runs `resolve_dynamic_stage()` there, persisting a corrected `current_stage`
before returning — meaning every consumer (ledger, `/twin`, `/what-if`) sees
the same corrected stage without each of them needing their own fix.

### 3.12 Tests — `agrotwin_api/tests/` (146 tests, all passing)

Covers the ledger/optimizer/rules math, the full API surface via FastAPI's
`TestClient` against an isolated in-memory SQLite DB (`conftest.py`), the
OCR pipeline (including real sample soil-health-card images), the
monitoring "wow" scenario (event → replan → alert), seed-data date sanity,
and yield prediction. Purely additive changes this cycle (crop_calendars
seeding, district expansion) were verified not to affect any existing test.

---

## 4. Frontend (`agrotwin_frontend/`)

Next.js 16 (Turbopack, App Router), Tailwind, TypeScript.

### 4.1 Design system

Government-portal aesthetic (deliberately, not generic SaaS): institutional
green (`--primary: #0B5E2C`), muted saffron accent, near-black text, sharp
`.gov-panel` corners (not rounded bubbles), Merriweather serif headings +
Noto Sans (with Devanagari subset for Hindi/Marathi) body text, a tricolour
accent bar under the header. Defined in `globals.css` + `layout.tsx`.

### 4.2 Pages (`src/app/`)

| Route | File | What it is |
|---|---|---|
| `/` | `page.tsx` + `components/landing/*` | Marketing/landing page: hero, capability strip, decision-loop explainer, digital-twin explainer, proof/explainability section, what-if preview, pilot-regions map, human-oversight section, final CTA. |
| `/dashboard` | `dashboard/page.tsx` | **The core screen.** Fetches `/twin`, renders the **Official Recommendation** hero panel (big fertilizer-quantity cards, numbered Next Steps checklist, stamp-style confidence badge, Listen-aloud button, Print button), field overview banner, soil/weather/status/location cards, and the **Recommendation History & Agronomist Oversight** panel (added this cycle). |
| `/simulator` | `simulator/page.tsx` | What-If simulator: crop tabs (only crops with a real backing field — Sugarcane/Banana/Cotton), sliders (fertilizer, rainfall, irrigation, timing, planting shift), a real backend-driven **Fertilizer Plan Comparison** (big before→after numbers), a local **visual crop-condition simulation** (`simulationEngine.ts`) that genuinely responds to all 5 inputs, and an embedded Sketchfab 3D model per crop. |
| `/upload` | `upload/page.tsx` | Soil report OCR upload → per-field confidence review → confirm. |
| `/insights` | `insights/page.tsx` | Fleet-wide alert feed (`GET /alerts`), severity filters. |
| `/command-center` | `command-center/page.tsx` | Fleet overview table across every field (crop/stage/soil-health/status/confidence/alert), summary counts. |

### 4.3 Key libraries

- **`lib/api.ts`** — the single typed HTTP client. Every function maps 1:1
  to a real backend endpoint; no fabricated data lives here. Includes a
  transient-network-failure retry (one silent retry on GET requests that
  fail before any response, since a dev-server hiccup shouldn't surface as
  a permanent error).
- **`lib/useFieldParam.ts`** — the shared "which field is selected" hook.
  Source of truth is the URL's `?field=`; falls back to the last-selected
  field via `localStorage` when a nav link doesn't carry the param, so
  switching to Insights/Command Center and back doesn't lose your field.
- **`contexts/LanguageContext.tsx`** — English/Hindi/Marathi translations.
  Covers the header chrome and the dashboard's static labels
  (`dash.*` keys); backend-generated content (recommendation text,
  citations, crop/product names) is deliberately left in English since
  translating real backend output would mean inventing text the backend
  never said.
- **`simulation/simulationEngine.ts` + `cropConfigs.ts`** — a genuine, local,
  clearly-labelled "structural representation" of crop growth (stage
  timing from `stageDurations`, vigor/stress from fertilizer/rainfall/
  irrigation/timing inputs) used only for the simulator's visual feedback —
  never presented as real backend/AI output.

### 4.4 Shared components (`components/ui/`)

`FieldSelector`, `FieldOnboarding` (new-field creation form), `FieldMap` /
`PilotRegionsMap` (Leaflet), `StageTimeline` (shared, read-only, current-
stage pulse animation), `Badge`/`Button`/`Card`/`ProgressBar`/`Slider`
(generic primitives), `LanguageSwitcher`.

---

## 5. How a recommendation actually gets produced (end to end)

1. Farmer (or onboarding form) creates a field (`POST /fields`) with a
   real district (now 37 to choose from, not just 2) and, ideally, lat/lon.
2. Farmer assigns a crop (`POST /fields/{id}/crop`) — sowing date +
   recommendation type.
3. Farmer uploads a soil health card (`POST /soil-report/upload` → OCR →
   review → `POST /soil-report/confirm`), or the numbers are entered
   manually.
4. Any `GET /twin` call from here on: `_field_row()` resolves the *real*
   current stage from elapsed time, fetches/persists live weather if
   missing, computes soil-health score from the same RDF targets the
   ledger uses, and returns the latest recommendation (or an honest
   `NO_DATA` if none has been generated yet).
5. `POST /recommend` runs the full pipeline (§3.5) and persists a new
   `recommendations` row; `SUPERSEDED` marks the previous one.
6. A farmer can request a What-If scenario (`/what-if`) without touching
   the real recommendation, or an agronomist can `POST /override` a
   specific recommendation with a reason — both fully audited.
7. If conditions change (heavy rain forecast, a new soil test, a manual
   fertilizer application logged), the monitoring agent automatically
   triggers a selective replan and raises an alert — visible on that
   field's dashboard and fleet-wide on `/insights`.

---

## 6. Features & USPs

- **Proof-carrying recommendations** — every plan answers WHAT/HOW MUCH/
  WHEN/WHY/BASED ON WHAT/HOW SURE, not just a number.
- **Deterministic core, LLM-free math** — an LLM is never on the path that
  produces a kg/ha figure; it's only used (optionally, and can fail
  silently) for narrative phrasing.
- **Honest missing-data states** — ABSTAIN, `NO_DATA`, "Not available",
  "Weather unavailable" are first-class UI states, not bugs to paper over
  with fake defaults. This was enforced repeatedly across this project's
  history (removing Kolhapur-coordinate fallbacks, hardcoded weather,
  fabricated yield numbers, invented crop stage sequences).
- **Region-independent correctness** — verified end-to-end with a real
  field in Pune (well outside the two pilot districts): real weather for
  its real coordinates, a real dynamic stage, a real ledger-computed
  fertilizer plan. The RDF math was never region-gated to begin with.
- **Dynamic, calendar-driven growth stage** — computed from real elapsed
  time against a sourced crop calendar, not a value stamped once and
  forgotten.
- **Human-in-the-loop** — OCR confirmation gate, agronomist override with
  full audit trail, confidence-based ABSTAIN.
- **Multilingual + voice** — Hindi/Marathi UI translation and a
  language-aware text-to-speech "Listen" button that reads the full field
  status aloud (soil, weather, recommendation, next steps).
- **What-If simulation clearly separated from real output** — the backend
  delta and the local visual simulation are never blended into one
  number that looks more authoritative than it is.
- **Fleet-wide oversight** — Command Center and Insights give a
  government-agronomist-style view across every field, not just one.

---

## 7. Known, honestly-logged limitations (see `PROGRESS.md` for the full list)

- Cost figures are `ENGINEERING_DEFAULT` estimates — no fertilizer price
  table has been sourced yet.
- The yield model is a directional estimate on synthetic-adjacent training
  data for 4 crops in 2 districts only; it abstains everywhere else.
- Speech-to-text (voice *input*) is not built — only text-to-speech output.
- Simulator page still has its own separate visual style, not yet folded
  into the shared government-portal design system.
- Full multilingual coverage stops at the dashboard's static chrome;
  Simulator/Upload/Insights/Command Center are still English-only.
- No authentication/field-ownership boundary — appropriate for a pilot
  demo, not for multi-tenant production.
