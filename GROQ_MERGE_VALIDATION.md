# Groq integration merged with yield inference

Source branch: `origin/feat/groq-llm-integration` at `9a8c3e3`.
Target before merge: `main` at `ca8c0ee`.

The source includes backend-v1, real OCR, Groq/xAI text generation, frontend,
PostgreSQL, and phosphorus-unit changes. Git merged without textual conflicts;
the following runtime integration fixes were applied before committing:

- Retained the trained yield bundle and endpoint. Adapted district lookup to
  named PostgreSQL rows and converted Decimal soil values to JSON-native floats.
- Updated the yield demo for the new seeder's active crop assignments, avoiding
  duplicates. Its SQLite connection follows the runtime database path and stays
  independent of any configured production DATABASE_URL.
- Preserved the branch's P-to-P2O5 ledger conversion. The yield model's trained
  feature engineering remains unchanged, with an explicit feature/proxy caveat.
  Therefore demo fertilizer/yield numbers differ from the pre-merge example.
- Fixed PostgreSQL boolean SQL for crop updates and dictionary-row handling in
  the seeder. The optional LP comparison now uses the active-crop view.
- Added native GROQ_API_KEY configuration, retained legacy Groq keys in
  XAI_API_KEY, corrected the xAI URL, made model IDs configurable, and added a
  10-second timeout/no retries. Optional failures return empty narrative text.
- Connected the existing report narrative to finalized recommendation responses
  without changing plan quantities. Added container environment wiring and
  documented configuration.
- Prevented OCR fallback from interpreting compressed binary bytes as text.
  OCR confidence is taken from actual matched blocks, including multiline
  tables; LLM suggestions stay below the farmer-review threshold and reject
  negative/nonfinite values and invalid pH/OC.
- Corrected the real-card test's assumption that every correct recognition has
  confidence >=0.85. All six expected numeric values remain asserted; the test
  now verifies low-confidence fields remain flagged for review. No OCR scores
  were increased to satisfy a test.
- Fixed the what-if endpoint to avoid persisting a simulated recommendation or
  emitting plan events, and removed stale narratives after scaling quantities.
- Replaced frontend `any` types with response types, fixed error handling, and
  cancelled obsolete field-load requests. Lint and the production build pass.

The real card yielded N=198, P=18.5, K=312 kg/ha, pH=7.8, OC=0.48%, EC=0.42.
The merged SYN-003 yield demo returned OK and 84087.2 kg/ha for explicit example
rainfall 1100 mm (synthetic model; not validated farm accuracy).

Full backend output: `merge_validation.txt`. New regression coverage includes
provider selection, missing credentials, provider failure, narrative/quantity
separation, binary OCR failures, LLM review flags, PostgreSQL-style dict/Decimal
inputs, one active crop per seeded field, multiline OCR confidence, and
non-persisting what-if requests.

External-service limits: provider calls were tested with mocks, not live paid
credentials. PostgreSQL row/type compatibility was regression-tested locally;
no live Neon/PostgreSQL database was modified or used for validation. Real
EasyOCR image inference and real XGBoost yield inference were executed. The
existing XGBoost serialization warning remains documented in `agrotwin_api/ml/README.md`.
