# AgroTwin AI — Progress & Running Audit Log

## Standard of Honesty
Every change, verified run, and stubbed feature is tracked here following the project's strict conventions (flags, citations, `ENGINEERING_DEFAULT` labels for unsourced assumptions).

---

## 1. Repository Cleanup & Canonical Backend
- [x] **Archive Superseded Prototype**: `agrotwin_prototype/` moved to `archive/agrotwin_prototype/` with notes in root `README.md`.
- [x] **Canonical Backend**: `agrotwin_api/` is the single application backend.
- [x] **Dependencies Updated**: Added `python-multipart>=0.0.9` and `psycopg[binary]>=3.1.18` to `agrotwin_api/requirements.txt`.

---

## 2. Database ID-Scheme Architecture Decision
- **Decision**: Keep `SERIAL` integer primary keys in PostgreSQL matching `schema_sqlite.sql`.
- **Rationale**: The entire application layer (`routes.py`'s `_field_row`, `isdigit()` routing, ledger methods, agent state, and queries) was written assuming integer primary keys (`field_id`, `crop_id`, `soil_test_id`, `recommendation_id`). Adopting UUIDs would require disruptive rewrites across dozens of call sites without agronomic benefit.
- **Action Implemented**: Updated `schema_postgres.sql` to use `SERIAL PRIMARY KEY` and integer foreign keys matching `schema_sqlite.sql` exactly 1:1.
- **Drift Guard**: Added synchronized headers to both `schema_sqlite.sql` and `schema_postgres.sql` stating they must remain structurally identical.

---

## 3. Seed Data & Crop Assignment Endpoint
- [x] **Seed Data Fixed**: Updated `seed_data.py` so that all 8 synthetic records (`SYN-001` through `SYN-008`) populate the `field_crops` table with their crop code, variety, sowing date, current stage, and recommendation type (`RECOMMENDATION_TYPE_BY_RECORD`). Fresh seeding no longer ABSTAINs on `/recommend`.
- [x] **New Endpoint**: Added `POST /fields/{id}/crop` to `app/api/routes.py` with `CropAssignRequest` schema. Clients can assign or update a field's active crop, variety, sowing date, and growth stage, emitting a `CROP_STAGE_CHANGED` event on the bus.

---

## 4. Soil Report OCR Wiring
- [x] **Replaced Mock OCR**: Replaced the hardcoded mock in `app/core/ocr.py` with `app/agents/soil_report_agent.py` in `POST /fields/{id}/soil-report/upload`.
- [x] **Real Extraction & Review**: Uploaded reports now extract real NPK, pH, OC, EC values using regex over text/bytes, calculate per-field confidence, and flag fields needing review (<0.85).
- [x] **PDF & EasyOCR Support**: Enhanced `_try_ocr()` in `soil_report_agent.py` with PDF text extraction and tempfile-backed EasyOCR execution when available.
- [x] **Farmer Confirmation**: Wired `POST /fields/{id}/soil-report/confirm` to update the digital twin only after confirmation, and publish `SOIL_REPORT_UPDATED`.

---

## 5. Selectable Optimizer (Heuristic & Linprog)
- [x] **Linprog Optimizer Implemented**: Added `ScipyLinprogOptimizer` to `app/core/optimizer.py` implementing the `Optimizer` protocol and delegating to `app/agents/optimizer.py` (solving LP via SciPy `highs` solver).
- [x] **Selectable in Pipeline & API**: Made optimizer selectable in `RecommendationPipeline.run` and `POST /fields/{id}/recommend` (`optimizer="heuristic"` or `"linprog"`). Default remains the explainable heuristic DAP→Urea→MOP.

---

## 6. Hybrid RAG Integration
- [x] **Merged RAG Engine**: Copied `backend/rag` (ingestion module and markdown doc pack: `mpkv_icar_rdf.md`, `jalgaon_rdf.md`, `fco_fertilizer_spec.md`, `crop_calendars.md`) into `agrotwin_api/rag`.
- [x] **Knowledge Agent Updated**: Refactored `agrotwin_api/app/agents/knowledge_agent.py` to use `HybridIndex` (BM25 + dense fallback) over `rag/docs/`. Queries now return real evidence citations and topically relevant text excerpts for Banana, Sugarcane, Cotton, and Soybean.

---

## 7. Database Abstraction Layer (SQLite & NeonDB Postgres)
- [x] **Unified DB Layer (`app/db.py`)**: Supports both SQLite (local development and fast unit testing) and PostgreSQL / NeonDB (serverless cloud Postgres), switched automatically when `DATABASE_URL` is set.
- [x] **Query & Row Adapter**: Automatically maps query parameters (`?` to `%s`), handles `cur.lastrowid` on Postgres inserts with `RETURNING`, and exposes dictionary row access.
- [x] **Dual-Mode Seed Script**: `seed_data.py` targets SQLite when `DATABASE_URL` is unset, and PostgreSQL when `DATABASE_URL` is provided.

---

## 8. Next.js Frontend Built
- [x] **Design Spec Compliance**: Minimalist light theme (#FAFAFA / #FFFFFF), WCAG AA high-contrast neutrals (#18181B / #52525B), calm agricultural green accent (#15803D), consistent confidence badges (HIGH, MEDIUM, LOW, ABSTAIN).
- [x] **Screens Implemented**:
  1. Main Dashboard: Living farm twin, crop metrics, soil NPK progress bars, active alerts.
  2. Proof-Carrying Recommendation: WHAT / HOW MUCH / WHEN / WHY / BASED ON WHAT / HOW SURE ARE WE.
  3. Evidence Viewer: Real RAG evidence chunks with citation links.
  4. What-If Simulator: Sliders for fertilizer delta % and 7-day rainfall forecast with side-by-side plan comparison.
  5. Soil Report OCR: File upload, per-field confidence preview, and farmer verification form.
  6. Crop Setup: Live assignment form for crop, stage, variety, and RDF recommendation pattern.
  7. Agronomist Oversight: Flagged recommendations and expert override form with audit trail.
- [x] **Tailwind & Tokens**: Custom tokens defined in `tailwind.config.ts` and `globals.css`.

---

## 9. Deployment Wiring
- [x] **Frontend Containerized**: Added `agrotwin_frontend/Dockerfile`.
- [x] **Docker Compose**: Updated `docker-compose.yml` to orchestrate both `api` (port 8000) and `frontend` (port 3000) with optional `DATABASE_URL`.
- [x] **Environment Template**: Created `.env.example` documenting all configuration keys.

---

## 10. Priority-1 Demo Readiness (In Progress)
- [x] **P → P₂O₅ Conversion Fixed**: Soil tests in Maharashtra report elemental P, while MPKV RDF uses P₂O₅. Applied the official ICAR/FCO molar mass ratio (P₂O₅ = P × 2.291) inside the deterministic ledger (`compute_gap`). Removed the `P_PROXY` flag and replaced it with an informational `P_CONVERTED_TO_P2O5` flag. Confidence is now `HIGH` when only this conversion applies.
- [x] **Lat/Lon Coordinates Added**: Added real geographic coordinates (`lat_deg`, `lon_deg`) to `synthetic_records.csv` by querying the centroids of Jalgaon and Kolhapur talukas. `seed_data.py` now maps these to the `fields` table, enabling fully functional live Open-Meteo weather forecasts without mocking.
- [x] **End-to-End Demo Script Created**: Developed `agrotwin_api/scripts/demo_e2e.py` which seamlessly runs the entire workflow: DB Seed → LLM Narrative + Recommendation → RAG Evidence → Real OCR Upload → Heavy Rain Event Injection → Automatic Plan Invalidation. Ready for a judge walkthrough.

## Verification & Status
- **Local SQLite Testing**: 73/73 tests passing. Demo script runs flawlessly.
- **NeonDB Cloud Postgres**: Awaiting user's `DATABASE_URL` environment variable for real cloud verification.
- **Soil Health Cards**: Awaiting 5-10 real Maharashtra Soil Health Card samples to finalize OCR tuning.

---

## Final Polish — Government Portal Redesign

Frontend-only visual/UX pass. No backend agronomy logic, ledger math, schema, or
ABSTAIN/confidence rules were touched — `pytest agrotwin_api/tests/` still passes
146/146 before and after, and every number shown remains one already returned by
`GET /fields/{id}/twin` or `POST /fields/{id}/what-if`.

### Part 1 — Official government-portal look
- [x] **Color system**: replaced the light-SaaS palette in `globals.css` with an institutional
  green (`#0B5E2C`), white surface, muted-saffron accent (`#B45F06`, used only for
  warnings/flags), and near-black text (`#1A1A1A`). Sharp corners via a `.gov-panel`
  utility (3px radius) used on the new hero panel and its buttons.
- [x] **Header**: `TopNavigation.tsx` rebuilt as an official top bar — an identity strip
  ("भारत सरकार · Government of Maharashtra — Department of Agriculture (Pilot
  Programme)") with a language switcher, an emblem placeholder (`lucide-react`
  `Landmark` icon in a circular badge — a real state emblem asset was not available,
  this is a labelled placeholder), the "AgroTwin AI / Digital Krishi Twin" lockup, and a
  tricolour accent bar under the header (`.tricolor-bar` in `globals.css`).
- [x] **Language switcher wired to the existing `LanguageContext.tsx`** (English /
  हिन्दी / मराठी) — it already had full landing-page translations; this pass only added
  the switcher control to the app-wide header. Dashboard/simulator/upload copy is
  **not yet translated** (English only) — see limitations below.
- [x] **Typography**: added `Merriweather` (serif, headings) and `Noto Sans` +
  `Noto Sans Devanagari` (body, via `next/font/google`) in `layout.tsx`.
- [x] **Footer**: new `components/layout/Footer.tsx` — helpline (Kisan Call Centre
  number), "Last updated" date, advisory disclaimer, data-source list (MPKV/ICAR RDF,
  Open-Meteo, FCO), and placeholder Accessibility/Report-an-issue links (no real
  target pages exist yet — `href="#"`, flagged here rather than silently faked).
- [x] **Emoji → icon set**: replaced emoji in the header/nav with `lucide-react`.
  The dashboard/simulator body copy still uses emoji in several places (soil/weather/
  status cards) — not swept in this pass for time; safe to do incrementally.

### Part 2 — Fertilizer plan as the hero
- [x] **Dashboard** (`dashboard/page.tsx`): the recommendation is now a full-width
  `OfficialRecommendationPanel` at the very top of the page (above the field-overview
  banner), replacing the old `lg:col-span-3` card buried in the metrics grid.
  - Big numeric cards render every key in `currentPlan.fertilizerBreakdown` (e.g.
    `DAP — 358 kg/ha`) at `text-3xl`/`text-4xl` — this field already existed on
    `TwinCurrentPlan` in `api.ts` but the dashboard wasn't rendering it.
  - "Next Steps" is a numbered checklist built only from real fields: step 1 is
    `applicationWindow`, the middle steps are `required_actions` verbatim, and the
    last step is a generic re-check reminder explicitly labelled
    `(ENGINEERING_DEFAULT — no sourced re-testing interval)` — no interval or
    threshold was invented. Steps toggle a client-side-only "done" checkmark
    (`useState`, not persisted) — this is a UI convenience, not a tracked backend
    state; flagged here per the project's honesty convention.
  - Confidence badge restyled as a rotated "stamp" (double border, `-rotate-6`) in
    the panel's top-right corner instead of an inline pill.
  - ABSTAIN and NO_DATA states are **the same logic branches as before**, only
    restyled to match the new panel — the reason text, `required_actions` list, and
    "Generate Recommendation" button are unchanged.
  - Added a "Download / Print Official Recommendation" button. Implementation is
    `window.print()` with a `.no-print` class (see `globals.css` `@media print`)
    hiding nav/footer/buttons — this prints the real panel content, not a
    separately-generated document. A dedicated PDF export library was not added
    (scope/time); this is the ENGINEERING_DEFAULT print path.
- [x] **Simulator** (`simulator/page.tsx`): added a full-width `FertilizerComparison`
  block above the crop-selector tabs, parsed directly from the real
  `POST /fields/{id}/what-if` response's `original.fertilizer` /
  `simulated.fertilizer` strings (no new backend field — just surfacing what the
  API already returns). Shows baseline → simulated per product in large type with
  a colored `+/- kg/ha` delta, so the effect of a slider change is now the most
  visually obvious thing on the page.
- [x] **Mobile (375px) verified** in-browser for both the dashboard hero panel and
  the simulator comparison — cards stack to a single column, stamp badge and text
  wrap without overlapping.

### Part 3 — Feature completion (partial — deprioritized per task instructions)
Explicitly told to skip Part 3 before Part 1/2 if time-constrained; time was
constrained, so only the near-zero-cost item was done:
- [x] Language switcher exposed in the header (see Part 1).
- [ ] Agronomist override endpoint (`POST /fields/{id}/override`) — exists in
  `routes.py`/`api.ts` but still has no UI surface.
- [ ] Audit/history view per field using `pipeline_audit` — not built.
- [ ] SMS/notification-style reminder banner — not built.
- [ ] Full multilingual coverage of dashboard/simulator/upload copy — not built
  (only the header chrome is translatable right now).

### Verification run for this pass
- `pytest agrotwin_api/tests -q` → **146 passed** (unchanged from before this pass;
  no backend files were edited).
- `npm run build` (agrotwin_frontend) → clean, 0 TypeScript errors.
- `npm run lint` → 0 errors, only pre-existing `<img>`/unused-var warnings.
- Manually verified live in-browser (real backend, `REAL-001`): hero panel renders
  real fertilizer quantities and next steps; simulator comparison updates live off
  a real `/what-if` call when the fertilizer slider moves; mobile viewport checked
  at 375px.

---

## What-If Fix + Insights / Command Center

### What-If simulator — real bug fix
Root cause: `irrigation`, `applicationTiming`, and `plantingShift` were dead
sliders. `POST /fields/{id}/what-if` (`WhatIfRequest` in `schemas.py`) only ever
accepted `fertilizer_delta_pct` and `rainfall_mm` — the other three inputs were
never sent to the backend, yet the on-screen "Crop Condition" panel was being
populated *only* from the backend response's `modelSignals`. Moving those three
sliders visibly changed nothing.
- [x] Fixed in `simulator/page.tsx`: the local `simulateCrop()` engine (already
  in the codebase, previously wired only as an error-fallback) now runs
  unconditionally on every input change and drives the Crop Condition panel —
  it's a genuine function of all five inputs (fertilizer, rainfall, irrigation,
  timing, planting shift), not fabricated.
- [x] The real backend numbers (fertilizer kg/ha delta, cost, yield band) stay
  on their own path, still fertilizer+rainfall only, feeding the `Fertilizer
  Plan Comparison` big-number cards and a separate "scenario estimate" line —
  never blended with the local visual simulation, so real vs. illustrative
  stays clearly separated per `CLAUDE.md`.
- [x] Verified live: setting Irrigation=Low + Rainfall=-40% now correctly shows
  Water Stress: Severe / Overall: High Stress (previously inert); fertilizer
  slider still correctly moves the real DAP/UREA/MOP numbers via `/what-if`.

### Insights (`/insights`) — new page
- [x] Fleet-wide alert feed off the existing `GET /alerts` endpoint (already
  built, never surfaced in the frontend). Severity filter (ALL/HIGH/MEDIUM/LOW),
  relative timestamps, resolved-state badge, link back to the alert's field
  dashboard. Auto-refreshes every 20s (same pattern as the dashboard's twin
  poll). Honest empty state when no alerts exist — verified against a live
  injected `HEAVY_RAIN_ALERT` event, which appeared correctly.

### Command Center (`/command-center`) — new page
- [x] Fleet overview table across every field from `GET /fields`, each row
  enriched with its own real `GET /fields/{id}/twin` call (crop/stage, soil
  health score, recommendation status, confidence, active alert) — no new
  backend endpoint, just a summary render of state that already exists per
  field. Summary strip: total fields / fields needing attention (ABSTAIN or
  unreachable) / active alerts. Verified live against all 11 seeded fields.

### Verification
- `npm run build` — clean, 0 TypeScript errors, both new routes compiled.
- `npm run lint` — 0 errors (fixed one `react-hooks/set-state-in-effect` this
  pass introduced in Command Center; pre-existing `<img>`/unused-var warnings
  untouched).
- No backend files changed this pass — `pytest` result from the prior pass
  (146/146) still holds.
- Not done: neither new page is translated via `LanguageContext` yet (English
  only, consistent with the dashboard/simulator/upload gap already logged
  above).

---

## Stage Timeline Fix — "static" bug

Both stage timelines were reported static:
- [x] **Simulator** (`GrowthStageTimeline` in `simulator/page.tsx`): the
  connector segment leaving the current stage was always drawn fully gray —
  it never used `CropVisualState.stageProgress` at all, so moving the
  planting-shift slider only changed a number ("Stage Progress: 68%") with no
  visible motion in the graphic itself. Fixed: that segment now fills
  proportionally to `stageProgress` (`transition-all duration-500`, so it
  animates), and the current-stage dot got a pulsing ring so it reads as
  "live" rather than inert.
- [x] Root cause behind why it rarely even *looked* like it should move:
  Planting Date Shift was capped at ±30 days, which for a crop like Sugarcane
  (Grand Growth alone is a 180-day stage) can never cross a stage boundary.
  Widened to −60 / +90 days so the timeline can actually be seen advancing
  into the next named stage, not just filling within one. Verified live:
  +90 days moves Sugarcane from "Grand Growth" into "Ripening" with the
  correct checkmarks/pulse.
- [x] **Dashboard** (`StageTimeline.tsx`, shared component, read-only): this
  one is correctly static between real state changes — it renders the twin's
  actual committed `growthStage`, which only changes via a real crop-stage
  update or replan, never a slider. Added the same pulsing ring to its current
  dot so it visibly reads as a live "you are here" indicator rather than a
  dead graphic, without fabricating any progress data the backend doesn't
  have (no fractional in-stage progress exists there, only a discrete current
  stage name).

### Verification
- `npm run build` — clean. `npm run lint` — 0 errors (only the same
  pre-existing `<img>`/unused-var warnings). No backend files touched.

---

## Dynamic Growth Stage, Regional Coverage, Voice — real root causes

Follow-up to "why is it always Grand Growth". The stage-timeline animation
fix above was correct but insufficient — the actual reason every seeded field
showed identical "Grand Growth" was upstream in the data/backend, not the UI:

### Root cause found
`current_stage` was a value stamped once at seed/crop-assign time and never
advanced — `app/agents/crop_agent.py` even had a dead, never-called
`get_days_after_planting()` function and the `crop_calendars` table (schema
already had `days_after_planting_min/max` columns, `source_file` default
pointing at `rag/docs/crop_calendars.md`) was **seeded with zero rows**. All 8
`REAL-*` pilot fields also share the exact same hardcoded `sowing_date`
(2024-06-01) and `current_stage` ("GRAND_GROWTH") — so even before the
calendar gap, there was nothing that could have varied between them.

### Fix — current_stage is now computed from real elapsed time
- [x] `seed_data.py`: new `seed_crop_calendars()` populates real day-ranges
  for Sugarcane, Cotton, and Banana **sourced from `rag/docs/crop_calendars.md`**
  (ICAR-NRRI + MPKV Rahuri, 2022 — the same doc already used for RAG
  citations), converting the doc's "months after planting" at 30 days/month
  (the doc's own stated convention). Soybean has no calendar in that source
  doc, so it is deliberately left uncalendared rather than inventing one —
  its stage stays a declared-only value, same as before. Rice has no seeded
  crop record in this system at all, so its calendar entry is skipped too.
- [x] `app/agents/crop_agent.py`: new `resolve_dynamic_stage(conn, crop_id,
  sowing_date)` — computes days-after-planting and matches it against the
  seeded calendar. Returns `None` (caller keeps the declared stage) when
  there's no sowing_date or no calendar for that crop — never guesses.
- [x] `app/api/routes.py`: `_field_row()` (the single function every
  field-scoped endpoint routes through — `/twin`, `/recommend`, `/what-if`,
  the ledger, the pipeline) now calls `resolve_dynamic_stage` and, when it
  disagrees with the stored value, **persists** the correction to
  `field_crops.current_stage` before returning the row. One fix, every
  consumer gets it — no other file needed to change.
- [x] Verified live: `REAL-001` (sown 2024-06-01, ~850 days ago — past even
  Sugarcane's full 540-day calendar) now correctly resolves to **Harvest**,
  not a frozen "Grand Growth". Three fresh test fields with different real
  sowing dates each resolve to their own correct stage (Cotton sown 15 days
  ago → Germination; Banana sown 29 days ago → Rhizome Establishment;
  Sugarcane sown 27 days ago → Germination) — genuinely dynamic and different
  per field, which is what "I want it dynamic" was asking for.
- **Known demo-data caveat**: because the `REAL-*` pilot records' sowing date
  is itself stale (2024), they now honestly resolve to Harvest — agronomically
  odd to show a fresh fertilizer plan at Harvest, but this is a demo-data
  freshness issue, not a code bug. If a cleaner demo look is wanted, update
  those 8 records' `sowing_date` to something recent — I did not do this
  unprompted since `REAL-*` is explicitly pilot/demo data the project's own
  rules say to preserve, not silently edit.

### Bonus fixes found while wiring this up
- [x] `stage_sequence` lookup in `/twin` used `crop_name` ("Cotton (Bt)")
  instead of `crop_code` ("COTTON") — never matched, so every Cotton field
  got an empty `stageSequence` and a blank stage display. Fixed to read
  `crop_code_str`.
- [x] `stage_sequence`/`stage_display_map` had no entries at all for COTTON
  or BANANA (only Sugarcane/Rice/Soybean) — added both, aligned with the
  same sourced calendar stage names above.
- [x] Bonus of the bonus: populating `crop_calendars` also fixed the
  onboarding form's "Current crop stage: No supported stages available"
  dropdown (it reads `crop_calendars` via `/onboarding/options`) for
  Sugarcane/Cotton/Banana — previously always empty regardless of crop.

### Question: does the system work for a farmer outside Kolhapur/Jalgaon?
Investigated rather than assumed, since this changes what I'd recommend:
- **The fertilizer math was never region-gated.** `fertilizer_recommendations`
  is keyed by `crop_id` + `recommendation_type` only. Weather is fetched by
  the field's own `lat`/`lon` via Open-Meteo, which works anywhere. RAG
  evidence retrieval filters by region when possible but **falls back to an
  unfiltered query automatically** (`knowledge_agent.py`) if the strict
  region filter returns nothing — it never blocks or degrades the answer.
- **The real gap was administrative, not computational**: `districts` only
  had 2 rows (Kolhapur, Jalgaon) seeded, and `fields.district_id` is a
  required (`NOT NULL`) foreign key — so a genuinely new farmer elsewhere
  literally could not complete onboarding without picking a false district.
- [x] Fixed by adding the other 34 real Maharashtra districts (real,
  publicly-known names only — no fabricated lat/lon bounding boxes or
  agro-zone data attached, since only Kolhapur/Jalgaon have a sourced
  boundary reference) plus an explicit "Other / not listed" region+district
  for anyone outside Maharashtra, so onboarding never forces a false
  district again. `seed_data.py` updated for future reseeds; the already-
  running dev DB was patched live the same way.
- **Verified end-to-end with a real test field**: created `PUNE-TEST-001`
  (Pune district, lat/lon 18.5204/73.8567 — nowhere near either pilot
  district), assigned Sugarcane, confirmed a soil test, and ran the full
  pipeline. Result: a genuine live Open-Meteo forecast for Pune (15.4mm/7d,
  correctly different from Kolhapur's), a correctly dynamic Germination stage
  from its own real sowing date, and a fully real DAP/UREA/MOP plan from the
  same deterministic ledger — nothing hardcoded, nothing region-blocked.
  (This test field is left in the dev DB — there's no delete-field endpoint
  to remove it with; harmless, but flagging it exists.)

### Voice
- [x] Added a "Listen" button to the dashboard's Official Recommendation
  panel using the browser's built-in `SpeechSynthesis` API (no new
  dependency, no backend call) — reads the same WHAT/HOW MUCH/WHEN/WHY/
  confidence text already on screen aloud, toggling to "Stop". English only:
  the recommendation text itself (product codes, citations) is generated in
  English and isn't machine-translated, so speaking it with a Hindi/Marathi
  voice would just mispronounce English words, not genuinely narrate in that
  language — noted as a real limitation, not silently pretended away.
- **Not done** (flagging rather than silently skipping, since "voice and
  whatever we need" was open-ended): speech-to-text for filling onboarding
  forms by voice. Deprioritized this pass — the Web Speech
  `SpeechRecognition` API has materially worse cross-browser support than
  `SpeechSynthesis` (Chrome-only in practice), and picking the right places
  to accept voice input (which fields, in which language) is a genuine
  product decision, not a mechanical one.

### Verification
- `pytest agrotwin_api/tests -q` — **146/146 passed** (crop_calendars/district
  seeding is purely additive; test DB has no calendar rows seeded in
  `conftest.py`, so `resolve_dynamic_stage` returns `None` there and existing
  test fixtures' declared stages are untouched).
- `npm run build` — clean, 0 TypeScript errors. `npm run lint` — 0 errors.
- Manually verified live against the running backend/frontend, including the
  new Pune field described above.

---

## Voice, Translation, and Farm-Page UI Consistency Fix

Follow-up: the Listen feature was flagged as "very basic," the language
switcher was reported as not working at all on the Farm (dashboard) page,
and the page's UI needed a consistency pass.

### Language switcher — root cause: nothing on the Farm page was wired to it
The switcher itself worked (it's the same `LanguageContext` used correctly by
the landing page) — but `dashboard/page.tsx` never called `t()` anywhere.
Every label was a hardcoded English string, so switching language changed
nothing on that page. This matches the honest limitation already logged in
this file after the government-portal redesign pass ("neither new page is
translated yet").
- [x] Added ~50 `dash.*` translation keys (English/Hindi/Marathi) to
  `LanguageContext.tsx` for all dashboard chrome: section headers, status
  words (High/Moderate/Low/Healthy/etc.), buttons, gate/error states, the
  Official Recommendation panel, and the confidence stamp.
- [x] Wired `dashboard/page.tsx` to `useLanguage()` and replaced every static
  chrome string with `t('dash.…')`. Status words that are also used in
  equality checks (`'Healthy'`, `'Good'`, etc.) were **not** translated at
  the data layer — a small `tStatus()` lookup translates them only at render
  time, so the underlying logic never touches a translated string.
- [x] Backend-generated content (the recommendation's description paragraph,
  citations, product/crop names, dates) is deliberately **not** translated —
  it's real ledger/RAG output in English, and machine-translating it would
  mean presenting invented text as if the backend said it. Verified this is
  the only remaining English content when Hindi or Marathi is selected.
- [x] Verified live: switching to Hindi visibly translates the whole page
  (headers, buttons, next steps, confidence stamp, nutrient status words);
  same for Marathi.

### Voice — made it a real farm-status assistant, not a one-liner
Previous version read only "apply X, quantity Y, confidence Z" in English
only. Now:
- [x] Narration covers soil health score, each nutrient's status, this
  week's weather, the recommendation, confidence, and every next step —
  the same information already on the card, read in full.
- [x] Language-aware: the fixed narration phrases translate with the
  selected language and `SpeechSynthesisUtterance.lang` is set to
  `hi-IN`/`mr-IN`/`en-IN` accordingly. Verified live in all three languages
  by intercepting `speechSynthesis.speak()` and inspecting the actual
  utterance text/lang.
- [x] Picks a matching installed voice by exact-then-prefix language match
  instead of silently using a default English voice while claiming a
  Hindi/Marathi `lang` tag; shows a small on-screen notice when no matching
  voice is installed in the browser, rather than pretending it spoke Hindi
  when it didn't.
- **Still not done** (flagged, not silently skipped): speech-to-text input.
  Deprioritized again this pass for the same reason as before — inconsistent
  browser support and it's a scope decision (which fields accept voice
  input), not a mechanical add.

### UI consistency ("fix UI of the website")
Found a concrete, visible defect while working on the above: the dashboard
had two different design languages stacked on one page — the Official
Recommendation hero panel used the government-portal system (sharp
`gov-panel` corners, `--primary` green, `--surface`/`--border` tokens) from
the earlier redesign pass, but every card below it (Soil Health, Weather,
Field Status, Location, Insights, Timeline) was still the original rounded
light-SaaS style (`rounded-xl`, `bg-white`, hardcoded `bg-gray-900` buttons)
that redesign never touched.
- [x] Restyled every remaining card, button, and background on
  `dashboard/page.tsx` to the same design tokens as the hero panel — one
  consistent look top to bottom instead of two.
- [x] Restyled `upload/page.tsx` the same way — it had been left entirely on
  the pre-redesign look (rounded cards, hardcoded hex `#0F4D35`, black
  buttons); now matches Farm/Insights/Command Center.
- **Not done this pass**: `simulator/page.tsx` still uses its own separate
  visual style (`#FDFBF7` cream background, different card treatment) — it
  was intentionally left alone in the original redesign because it has a
  richer, purpose-built layout (3D viewer, sliders); it was not touched here
  either since the user's specific complaints were the Farm page and the
  language switcher. Flagging it as the next place this same inconsistency
  will be visible if asked to continue the sweep.

### Verification
- `npm run build` — clean, 0 TypeScript errors. `npm run lint` — 0 errors
  (same pre-existing `<img>`/unused-var warnings only).
- No backend files changed this pass.
- Manually verified live: Hindi/Marathi translation and voice narration both
  checked against the real running app (not assumed from reading the code).

---

## Fertilizer Plan Comparison Fix + Agronomist Override & History (new feature)

### The "Fertilizer Plan Comparison" bug — three real, distinct root causes
Investigated live rather than guessing:
1. **Crop tabs pointed at the wrong fields.** `CROP_TO_FIELD` in
   `simulator/page.tsx` mapped Banana→REAL-002, Cotton→REAL-003,
   Rice→REAL-004 — but `GET /fields` shows **every** REAL-001..008 record is
   Sugarcane. Clicking "Banana" or "Cotton" silently loaded a mismatched
   Sugarcane field; clicking "Rice" pointed at a crop with no record in this
   system at all (`crops` table has no RICE row). Fixed: Banana/Cotton now
   point at the real Banana/Cotton test fields created earlier this session
   (`FARM-de3b356b…`, `FARM-5df3a349…`, both with confirmed soil + a real
   generated plan); the Rice tab was removed rather than left pointing at
   nothing real.
2. **Cotton specifically then hit a second bug**: `SimulatorGate` checked
   `CROPS[twin.crop.toLowerCase()]` — but `twin.crop` is the backend's
   *display* name ("Cotton (Bt)"), not a clean code, so it never matched the
   `CROPS` config key `cotton` and showed "Simulation unavailable for this
   crop" even once pointed at a real Cotton field. Fixed by stripping the
   `"(...)"` suffix before matching.
3. **Division by zero when a field's real N gap is genuinely 0** (soil
   already meets the target — a valid `NO_FERTILIZER_NEEDED` state, not
   missing data): `fertilizer_delta_pct = (nKgHa - baseline) / baseline * 100`
   with `baseline = 0` produces `NaN`/`Infinity`, both of which
   `JSON.stringify` silently turns into JSON `null` — so the slider looked
   completely inert for any such field, no matter where it was moved. Fixed
   by clamping to the schema's own bounds (`-100..500`) instead of sending a
   value that can't survive being sent. Also added an honest "No fertilizer
   needed — soil already meets the target" message for this state instead of
   silently rendering nothing, which had looked like the panel failed to load.
- Verified live for all three: Banana and Cotton tabs now show correct,
  distinct real data; the zero-baseline Cotton field now visibly reflects
  slider changes and shows the explicit no-fertilizer-needed message.

### New feature — Recommendation History & Agronomist Oversight
Per the explicit ask to keep adding real features: checked for unused
backend capability first, per this project's own stated priority order.
`POST /fields/{id}/override` already existed, fully implemented server-side
(audit log, event bus, supersession) — never surfaced in the frontend, and a
history list endpoint didn't exist at all.
- [x] **New backend endpoint** `GET /fields/{id}/recommendations` — every
  recommendation ever generated for a field, most recent first, read-only
  over the existing `recommendations` table (no new domain concept).
- [x] **Fixed a real bug in the existing override endpoint** while wiring it
  up: `agronomist_override` stored the agronomist's `new_plan` dict directly
  as `plan_json`, but `/twin` expects the full proof-object shape (`status`,
  `what`, `how_much`, `when`, `based_on`, …). An override was silently
  invisible on `/twin` — the dashboard showed "no recommendation generated
  yet" right after a successful override. Fixed by carrying over the
  original recommendation's `when`/`based_on`/citation and only replacing
  `how_much`/`what`/`status`/`confidence`/`reason` with the agronomist's
  values.
- [x] **New frontend panel** (`HistoryOversightPanel` in `dashboard/page.tsx`):
  a timeline of every past recommendation (status, confidence, timestamp,
  supersession chain) plus an "Override latest plan" action that opens an
  inline form (editable kg/ha per product + required reason) and calls the
  real override endpoint, then refetches both the history and the twin so
  the Official Recommendation panel updates immediately.
- Verified live end-to-end: submitted a real override on `REAL-003`
  (120/40/10 DAP/UREA/MOP, with a reason), confirmed the Official
  Recommendation panel updated to HIGH confidence with the new quantities,
  and the history list showed the correct PROPOSED → SUPERSEDED chain with
  "Manually overridden by an agronomist" on the new entry.

### Verification
- `pytest agrotwin_api/tests -q` — **146/146 passed**, both before and after
  the override plan_json fix (the existing override test only asserts DB
  row status/confidence_reason/audit log, not plan_json shape, so it wasn't
  protecting against this bug — worth noting as a real test gap, not fixed
  this pass).
- `npm run build` — clean, 0 TypeScript errors. `npm run lint` — 0 errors.
- Backend was restarted clean (not `--reload`) after this session hit
  repeated confusion from stale/orphaned `--reload` reloader processes
  surviving normal `Stop-Process` calls on Windows — future backend restarts
  in this environment should kill by exact PID via `taskkill /F /T` and
  verify `GET /health` responds before assuming new code is live.

---

## Weather-Unavailable Fix + Full-Site Sweep

### Root cause: weather was gated behind a full recommendation run
`GET /fields/{id}/twin` only ever read a persisted `weather_snapshots` row,
which was only ever written as a side effect of running the full
`/recommend` pipeline (weather is one step in that pipeline). A field that
had a confirmed soil test but had never had `/recommend` called on it — or
any field freshly onboarded — showed "Weather unavailable" forever, even
though the weather agent (`weather_agent.get_weather_context`) only ever
needed the field's own lat/lon and doesn't depend on soil test, crop, or
recommendation state at all.
- [x] Fixed in `/twin` (`routes.py`): when no snapshot or injected weather
  event exists yet, it now calls `weather_agent.get_weather_context()`
  directly (using the field's real lat/lon) and persists the result, the
  same as `/recommend` already does — a field shows its real weather on its
  very first look, not only after generating a plan. A field with no
  recorded lat/lon still correctly shows "unavailable" — that's honest
  missing-data, not a bug, and the fix does not fabricate coordinates.
- Verified across every currently-seeded field: `REAL-005`..`REAL-008` (soil
  confirmed, no `/recommend` ever run) now return real Open-Meteo data
  immediately; the three `FARM-*` test fields (real lat/lon = null) correctly
  still show unavailable — coordinates genuinely don't exist for them.

### Full-site sweep (per "everything must be working")
Rather than only patching the one reported symptom, checked every page
against every currently-seeded field:
- **Command Center**: all 12 fields render correctly (crop/stage, soil
  score, status, confidence, alert) — no errors.
- **Insights**: real alert (the `REAL-002` heavy-rain event) renders
  correctly with severity/timestamp/field link.
- **Dashboard**: spot-checked multiple fields; the `Volume2 is not defined`
  console error seen mid-sweep was confirmed to be a **stale Next.js
  Fast-Refresh artifact** left over from live-editing this file earlier in
  the session, not a real current bug — a fresh navigation shows the import
  is correct and the Listen button renders and works. Verified via a clean
  reload, not assumed.
- **Simulator**: confirmed the Fertilizer Plan Comparison genuinely renders
  after its ~400ms debounce + network round trip on every field checked —
  an earlier "it's missing" read during this same sweep was my own check
  running before that round trip finished, not a product bug (confirmed by
  re-checking network requests, which showed the real 200 OK arriving a
  moment later).
- **Upload**: renders correctly with the government-portal styling.
- No new frontend or backend defects found beyond the weather fix above.

### Verification
- `pytest agrotwin_api/tests -q` — **146/146 passed**.
- `npm run build` — clean, 0 TypeScript errors. `npm run lint` — 0 errors.
- Checked live against the running app for every field in the database, not
  a single happy-path field.
