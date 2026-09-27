# AgroTwin AI

An Agentic, Evidence-Grounded Digital Twin for Continuous Farm Nutrient Monitoring and Sustainable Fertilizer Optimization.

## Repository Layout
- `agrotwin_api/`: Canonical running backend (FastAPI, SQLite / NeonDB PostgreSQL support, deterministic rules, optimizer, event bus, soil OCR confirmation, hybrid RAG).
- `agrotwin_frontend/`: Minimalist, high-contrast, mobile-first Next.js web application.
- `backend/`: Advanced RAG and ingestion engine (merged into `agrotwin_api` knowledge layer).
- `archive/agrotwin_prototype/`: Superseded prototype folder moved to archive (preserved for reference).
- `docs/`: Complete architectural specifications, schema, UX principles, and implementation notes.
