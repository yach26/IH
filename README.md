# AgroTwin AI

An Agentic, Evidence-Grounded Digital Twin for Continuous Farm Nutrient Monitoring and Sustainable Fertilizer Optimization.

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# From repo root
docker-compose up --build
```

This starts:
- API at `http://localhost:8000`
- Frontend at `http://localhost:3000`
- API docs at `http://localhost:8000/docs`

### Option 2: Local Development

```bash
# 1. Install Python dependencies
cd agrotwin_api
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Seed the database (disposable demo data)
python seed_data.py

# 3. Start the API
uvicorn app.main:app --reload

# 4. In another terminal, start the frontend
cd ../agrotwin_frontend
npm install
npm run dev
```

### Option 3: One-Command Demo

```bash
cd agrotwin_api
python ../scripts/demo_e2e.py
```

This runs the full end-to-end demo: seed -> OCR -> recommend -> heavy-rain -> what-if.

## Repository Layout

- `agrotwini_api/` - FastAPI backend with deterministic Nutrient Ledger, optimizer, OCR, RAG, yield model
- `agrotwin_frontend/` - Next.js frontend (separate repo)
- `scripts/` - Demo and utility scripts
- `docs/` - Architecture docs, OCR field guide, ADRs
- `ml/` - Yield prediction model card and metadata

## What is Real vs Synthetic vs Optional

| Component | Status | Notes |
|-----------|--------|-------|
| Nutrient Ledger | **Real** | Deterministic DAP->Urea->MOP calculation |
| Fertilizer quantities | **Real** | Always from Ledger, never from LLM |
| RDF values | **Real** | From published MAHAFPDF/ICAR documents |
| Soil test data (8 fields) | **Synthetic** | Calibrated to published averages |
| Yield model training data | **Synthetic** | Calibrated to published averages |
| Yield model predictions | **Real** | XGBoost inference, but trained on synthetic data |
| OCR pipeline | **Real** | EasyOCR + regex + LLM refinement |
| SHC test fixtures | **Synthetic** | 5 text-based fixtures for testing |
| LLM narratives | **Optional** | Groq/xAI, degrades gracefully |
| Weather data | **Real** | Open-Meteo (free, no key needed) |
| RAG documents | **Real** | Published agricultural PDFs |

## Environment Variables

See `.env.example` for all variables. Key ones:

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | (empty) | Postgres connection string; empty = SQLite |
| `GROQ_API_KEY` | (empty) | Groq LLM API key (optional) |
| `XAI_API_KEY` | (empty) | xAI/Grok API key (optional) |
| `AGROTWIN_DB` | `./agrotwin_api/agrotwin.db` | SQLite file path |

## Safety Guarantees

1. **LLM never invents fertilizer quantities** - All kg/ha come from the deterministic Nutrient Ledger
2. **Yield model is read-only** - It predicts yield given a plan; it never modifies the plan
3. **OCR requires farmer confirmation** - No OCR value is written to the Digital Twin without explicit confirmation
4. **System abstains gracefully** - When data is insufficient or confidence is too low
5. **Proof-carrying** - Every recommendation answers: WHAT / HOW MUCH / WHEN / WHY / BASED ON WHAT / HOW SURE ARE WE

## Testing

```bash
cd agrotwin_api
python -m pytest tests/ -v
```

## Documentation

- [Model Card](agrotwin_api/ml/model_card.md) - Honest limitations of the yield model
- [OCR Fields](docs/OCR_FIELDS.md) - Which fields are extracted vs manual
- [Architecture Decision Record](docs/ADR.md) - Why quantities stay deterministic
- [Demo Script](scripts/demo_e2e.py) - One-command end-to-end demo

## Remaining External Items

The following require team/external resources and are NOT blockers for the demo:

1. **Real Soil Health Cards** - Actual farmer SHC images for OCR validation
2. **Production DATABASE_URL** - Managed Postgres (e.g., Neon) for production deployment
3. **Real historical yield data** - For retraining the yield model with real farm data
4. **Fertilizer price data** - For cost-aware optimization (currently weight-minimization)
