# AgroTwin AI

An Agentic, Evidence-Grounded Digital Twin for Continuous Farm Nutrient Monitoring and Sustainable Fertilizer Optimization.

## Repository Layout
- `agrotwin_api/`: Canonical running backend (FastAPI, SQLite / NeonDB PostgreSQL support, deterministic rules, optimizer, event bus, soil OCR confirmation, hybrid RAG).
- `agrotwin_frontend/`: Minimalist, high-contrast, mobile-first Next.js web application.
- `backend/`: Advanced RAG and ingestion engine (merged into `agrotwin_api` knowledge layer).
- `archive/agrotwin_prototype/`: Superseded prototype folder moved to archive (preserved for reference).
- `docs/`: Complete architectural specifications, schema, UX principles, and implementation notes.

## Run the merged application

Install Python dependencies from `agrotwin_api/requirements.txt` (a virtual
environment is recommended). For a disposable demo database with all eight
synthetic fields, start the API from `agrotwin_api`:

```text
python scripts/demo_yield.py --serve
```

Then in `agrotwin_frontend`, run `npm ci` followed by `npm run dev`.
The dashboard is at `http://localhost:3000`; API documentation is at
`http://127.0.0.1:8000/docs`. The yield endpoint remains available at
`/fields/SYN-003/yield-estimate?rainfall_mm_season=1100`.

For a persistent local deployment, seed a **new/disposable** database with
`python seed_data.py` from `agrotwin_api`, then run `uvicorn app.main:app`.
The seeder resets its target database; do not use it on existing farm data.
Database files are no longer tracked in Git. Initialize the local SQLite file
before using the Docker Compose file's database bind mount.

Optional LLM narratives and OCR suggestions use `GROQ_API_KEY` / `GROQ_MODEL`
or `XAI_API_KEY` / `XAI_MODEL`, exported in the API process environment.
For uvicorn, `--env-file ../.env` loads a local configuration file; copying
`.env.example` alone does not load variables. Compose passes these variables
to the API container. No key is needed for deterministic recommendations,
yield inference, OCR, or local RAG retrieval. Provider failures leave narrative
text empty. Requests have a 10-second timeout and no retries. Groq keys in the
legacy `XAI_API_KEY` variable remain supported.

Default models are configurable: [Groq Llama 3.3 70B](https://console.groq.com/docs/model/llama-3.3-70b-versatile)
and [xAI Grok 4.3](https://docs.x.ai/developers/migration/may-15-retirement).
Credentials are server-side only. EasyOCR downloads its weights on first use
into `agrotwin_api/.cache/easyocr`; override with `AGROTWIN_OCR_MODELS` if needed.
Low-confidence OCR and LLM-assisted values remain flagged for farmer confirmation.

## Validation

```text
python -m pytest agrotwin_api/tests backend/tests -q
cd agrotwin_frontend
npm run lint
npm run build
```

See `GROQ_MERGE_VALIDATION.md` for merge fixes and verification limits.
