# AgroTwin AI — Project Summary

*(Short version of `01_PROJECT_KNOWLEDGE_BASE.md`)*

## What it is

AgroTwin AI is a **Digital Farm Twin** for fertilizer decision support. For
each farmer's field it maintains a living picture — soil, crop, growth
stage, weather, application history — and produces a **proof-carrying
fertilizer recommendation**: not just a number, but what to apply, how
much, when, why, what evidence it's based on, and how confident the system
is. Built for a Maharashtra agriculture pilot (Kolhapur & Jalgaon), but
proven to work correctly anywhere.

## The core rule everything is built around

**The backend is the only source of truth for agronomic numbers. Nothing —
not the UI, not an LLM — is allowed to invent a fertilizer quantity, a
weather value, or a crop stage.** Missing data shows as an honest "not
available" state, never a plausible-looking fake number.

## How it works, in one paragraph

A farmer registers a field and crop, uploads a soil health card (OCR-read,
farmer-reviewed, then confirmed), and the system runs a five-stage
pipeline — Soil → Crop → Weather → Nutrient Ledger → Optimizer → Validation
→ Evidence (RAG) → Confidence — to produce a plan. The **Nutrient Ledger**
is a deterministic calculation (`required RDF dose − current soil level −
credited previous applications = gap`, converted to DAP/Urea/MOP kg/ha) —
never an LLM guess. Every recommendation carries citations back to real
MPKV/ICAR agronomy documents. If conditions change (a rain forecast, a new
soil test), the system automatically re-evaluates and alerts the farmer.
An agronomist can review the audit trail and override any plan with a
recorded reason.

## Tech stack

- **Backend**: FastAPI (Python), SQLite/PostgreSQL, SciPy (linear-program
  optimizer option), XGBoost (yield model), BM25 + dense-embedding hybrid
  RAG, EasyOCR/pypdf for soil-card reading, Open-Meteo for weather.
- **Frontend**: Next.js 16, TypeScript, Tailwind, Leaflet maps, browser
  Web Speech API (multilingual voice read-aloud).

## What makes it different from "an AI that recommends fertilizer"

1. **The math is deterministic and auditable** — an LLM is never on the
   path that produces a kg/ha number.
2. **It says "I don't know" instead of guessing** — ABSTAIN states,
   confidence scoring, and "not available" everywhere data is genuinely
   missing.
3. **Every number has a citation** — real agronomy documents, not a
   black-box model output.
4. **It works for a farmer anywhere**, not just the two pilot districts —
   verified live with a test field in Pune.
5. **It has a human in the loop** — OCR confirmation before data is
   trusted, agronomist override with full audit history.
6. **It's accessible** — Hindi/Marathi translation and a voice read-aloud
   feature for lower-literacy users.
7. **It monitors continuously** — a recommendation isn't a one-time
   answer; the system watches weather and soil-data changes and
   automatically re-plans.

## Current scope / honest limitations

Piloted for 4 crops (Sugarcane, Banana, Cotton, Soybean); the yield model
covers those 4 crops in 2 districts and abstains elsewhere. Fertilizer
cost figures are engineering estimates (no price table sourced yet).
Voice input (speech-to-text) isn't built, only voice output. No
multi-tenant authentication — appropriate for a pilot, not production.

## Where to look next

- `03_FARMER_USAGE_AND_DATA_SOURCES.md` — what a farmer actually
  experiences, and exactly which external data sources back every number.
- `04_DEMO_PRESENTATION_SCRIPT.md` — a judge-facing walkthrough script.
- `01_PROJECT_KNOWLEDGE_BASE.md` — the full file-by-file technical
  reference.
