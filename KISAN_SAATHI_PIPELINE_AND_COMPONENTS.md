# Kisan Saathi — Pipeline Working Document
### Input → Output trace, every interconversion, and a background primer on every underlying technology

**Branch verified:** `FINAL_V1`, commit `7e215c8`
**Purpose of this document:** trace one request through the entire system, showing exactly what data shape exists at every hop and how each component converts its input into its output, then give real background on every named technology (EasyOCR, BM25, dense embeddings/FAISS, XGBoost, SciPy `linprog`/HiGHS) so a reader understands not just *that* it's used, but *how it actually works* and *why it was chosen*.

---

## Table of contents

1. How to read this document
2. The two entry points: a soil card photo, and a recommendation request
3. Master data-flow diagram
4. Stage-by-stage trace with exact data shapes
   - 4.1 OCR ingestion (photo → structured soil values)
   - 4.2 Soil Agent
   - 4.3 Crop Agent and dynamic stage resolution
   - 4.4 Weather Agent
   - 4.5 The Nutrient Ledger (the core conversion chain)
   - 4.6 The Optimizer (heuristic and LP)
   - 4.7 Validation / Rule Engine
   - 4.8 Knowledge Agent (RAG retrieval)
   - 4.9 Confidence assembly
   - 4.10 Proof assembly and persistence
   - 4.11 The Yield Model (parallel, read-only branch)
   - 4.12 Monitoring Agent and event-driven replanning
5. Component background primers
   - 5.1 EasyOCR — what it is, how it recognises text, why it was chosen here
   - 5.2 pypdf — direct text extraction
   - 5.3 BM25 — keyword retrieval, the math behind the score
   - 5.4 Sentence-transformers + FAISS — dense/semantic retrieval
   - 5.5 Reciprocal Rank Fusion — merging two rankings
   - 5.6 XGBoost — gradient-boosted trees, and what this model was actually trained on
   - 5.7 SciPy `linprog` and the HiGHS solver — linear programming in one page
   - 5.8 FastAPI, SQLite/PostgreSQL, the event bus — the software substrate
6. Every unit conversion and formula used anywhere in the pipeline, in one table
7. Two fully worked examples end to end

---

## 1. How to read this document

Section 4 is the **spine**: it follows one field's data from raw inputs to a finished recommendation, one hop at a time, showing the literal shape of the data before and after each component. Section 5 is the **background**: for every named library or algorithm, a short, self-contained explanation of the underlying technique, written for someone who has heard the name but not studied it. Section 6 is a **quick-reference table** of every formula so you don't have to hunt through Section 4 mid-conversation. Section 7 gives two complete numeric walkthroughs.

Evidence tags: **[RAN]** executed and observed this session on `FINAL_V1`; **[CODE]** read from source, not executed; **[BG]** general background knowledge about the technique, not specific to this codebase.

---

## 2. The two entry points

Almost everything the system does starts from one of two triggers:

**Entry point A — a farmer uploads a Soil Health Card.** Input: an image or PDF file. Output, several hops later: a confirmed row in the `soil_tests` table. This is Section 4.1.

**Entry point B — a recommendation is requested** (`POST /fields/{id}/recommend`, either called directly, or automatically re-triggered by the Monitoring Agent after an event). Input: a field ID and optional overrides (mock weather, an optimizer choice, farmer-confirmed inputs). Output: a full proof-carrying recommendation object, persisted to the database and returned as JSON. This is the spine of Sections 4.2 through 4.10.

Both entry points feed the same downstream machinery — a confirmed soil report from entry point A becomes the `soil_test` that entry point B's Ledger step reads.

---

## 3. Master data-flow diagram

```
┌─────────────────────┐        ┌──────────────────────┐
│ Soil Health Card     │        │ POST /recommend       │
│ (photo or PDF)       │        │ {field_id, options}   │
└──────────┬───────────┘        └──────────┬────────────┘
           │                                │
           ▼                                ▼
   ┌───────────────┐              ┌──────────────────────┐
   │ OCR INGESTION │              │  1. INPUT VALIDATION  │
   │ pypdf│EasyOCR │              │  (crop? rec_type?     │
   │ →regex→confid.│              │   soil test exists?)  │
   └───────┬───────┘              └──────────┬────────────┘
           │ low-conf → human review          │ pass
           ▼                                  ▼
   ┌───────────────┐              ┌──────────────────────┐
   │ soil_tests row │◄─────────────┤  2. SOIL AGENT        │
   │ (DB, confirmed)│  read        │  latest test + staleness│
   └────────────────┘              └──────────┬────────────┘
                                               ▼
                                    ┌──────────────────────┐
                                    │  3. CROP AGENT        │
                                    │  stage from days-     │
                                    │  after-planting        │
                                    └──────────┬────────────┘
                                               ▼
                                    ┌──────────────────────┐
                                    │  4. WEATHER AGENT     │
                                    │  Open-Meteo 7-day     │
                                    │  forecast or mock      │
                                    └──────────┬────────────┘
                                               ▼
                          ┌────────────────────────────────────┐
                          │  5. NUTRIENT LEDGER                 │
                          │  RDF lookup → P/K unit conversion   │
                          │  → gap = max(0, required-available) │
                          └──────────────┬───────────────────────┘
                                         ▼
                          ┌────────────────────────────────────┐
                          │  6. OPTIMIZER                        │
                          │  heuristic (DAP→Urea→MOP) or         │
                          │  LP (scipy.optimize.linprog/HiGHS)   │
                          └──────────────┬───────────────────────┘
                                         ▼
                          ┌────────────────────────────────────┐
                          │  7. VALIDATION / RULE ENGINE         │
                          │  pH, EC, staleness, weather-window,  │
                          │  max-rate checks                     │
                          └──────────────┬───────────────────────┘
                                         ▼
                          ┌────────────────────────────────────┐
                          │  8. KNOWLEDGE AGENT (RAG)            │
                          │  BM25 + dense(FAISS) → RRF fusion    │
                          │  → cited evidence chunks             │
                          └──────────────┬───────────────────────┘
                                         ▼
                          ┌────────────────────────────────────┐
                          │  9. CONFIDENCE ASSEMBLY              │
                          │  de-dup flags → HIGH/MEDIUM/LOW/     │
                          │  ABSTAIN                             │
                          └──────────────┬───────────────────────┘
                                         ▼
                          ┌────────────────────────────────────┐
                          │ 10. PROOF ASSEMBLY + PERSIST         │
                          │  the 6-question object → DB →        │
                          │  publish PLAN_CREATED event          │
                          └──────────────┬───────────────────────┘
                                         │
                     ┌───────────────────┼─────────────────────────┐
                     ▼                                             ▼
        ┌───────────────────────┐                    ┌──────────────────────────┐
        │ 11. YIELD MODEL         │                    │ 12. MONITORING AGENT      │
        │ (optional, read-only)  │                    │ listens for the NEXT      │
        │ XGBoost per crop        │                    │ event (rain, new soil     │
        │ → annotation only       │                    │ test, applied fertilizer) │
        └───────────────────────┘                    └─────────────┬──────────────┘
                                                                     │ event fires
                                                                     ▼
                                                      selective re-entry into steps
                                                      3-10 (only the affected agents)
                                                                     │
                                                                     ▼
                                                          new proof object,
                                                          old one marked SUPERSEDED
```

---

## 4. Stage-by-stage trace with exact data shapes

### 4.1 OCR ingestion — photo → structured soil values

**Input:** raw file bytes (JPEG/PNG image, or PDF) uploaded to `POST /fields/{id}/soil-report/upload`.

**Conversion chain:**

```
raw bytes
   │
   ├─ is it a PDF with a real text layer? ──yes──► pypdf.PdfReader → plain text
   │                                        no
   ▼
   image preprocessing (grayscale, contrast normalisation)
   ▼
   EasyOCR reader.readtext() → list of (bounding_box, recognised_text, confidence) tuples
   ▼
   regex key-value matching against known Indian SHC label patterns
   ("Available N", "Avail. P (kg/ha)", "pH", "OC%", "EC", ...)
   ▼
   { "n_kg_ha": {"value": 258.7, "confidence": 0.91},
     "p_kg_ha": {"value": 2.33,  "confidence": 0.62},   ← below 0.85 threshold
     "k_kg_ha": {"value": 69.26, "confidence": 0.94},
     "ph":      {"value": 6.26,  "confidence": 0.88} }
   ▼
   fields with confidence < 0.85 → fields_needing_review list
   (optionally, an LLM is asked to propose a value for those fields; any
    LLM-proposed value is stamped confidence 0.80, which stays under the
    threshold, so it STILL requires human confirmation)
   ▼
   farmer/agronomist reviews and confirms final values via the UI
   ▼
POST /fields/{id}/soil-report/confirm
   ▼
   INSERT INTO soil_tests (field_id, n_kg_ha, p_kg_ha, k_kg_ha, ph,
                            oc_percent, test_date, source='OCR_CONFIRMED')
   ▼
   publish event SOIL_REPORT_UPDATED → triggers a selective replan (Section 4.12)
```

**Output:** a confirmed row in `soil_tests`. This is the only way OCR output can reach the rest of the pipeline — nothing below a human confirmation ever reaches the Ledger.

### 4.2 Soil Agent

**Input:** `field_id`. **Reads:** the newest row in `soil_tests` for that field.
**Conversion:** compares `test_date` to today; if the gap exceeds a configured threshold (180 days), attaches a `STALE_SOIL_DATA` flag with the exact day-count and the threshold's source label.
**Output:** a `SoilContext` object — `{n_kg_ha, p_kg_ha, k_kg_ha, ph, oc_percent, is_stale, days_since_test, flags}` — written into the shared pipeline state (`TwinState`).

### 4.3 Crop Agent and dynamic stage resolution

**Input:** `field_id` → the active row in `field_crops` (crop, sowing date, stored stage, recommendation type).
**Conversion:**
```
days_after_planting = today - sowing_date
resolved_stage = the crop_calendars row whose [days_min, days_max] range contains
                  days_after_planting, for this crop
```
If `days_after_planting` falls outside every defined range (e.g. far beyond the last calendar stage), the stored stage is kept unchanged and a `STAGE_NOT_IN_CALENDAR`-type flag may be attached, rather than the engine inventing a stage.
**Output:** a `CropContext` — `{crop_code, current_stage, recommendation_type, calendar_entries, stage_valid, flags}`.

**Important interconversion boundary:** the resolved stage is *displayed and validated*, but it is **not** an input to the RDF lookup in the next stage — the Ledger keys its lookup on `(crop_code, recommendation_type)` only, not on stage. The stage exists for transparency and future extension, not as a live multiplier on the dose today.

### 4.4 Weather Agent

**Input:** the field's `(lat, lon)`.
**Conversion:**
```
GET https://api.open-meteo.com/v1/forecast?latitude=..&longitude=..
    &daily=precipitation_sum,precipitation_probability_max&forecast_days=7
   ▼
rainfall_mm_next_7d   = sum(daily precipitation_sum)
rainfall_probability  = max(daily precipitation_probability_max)
   ▼
heavy_rain_alert = (rainfall_probability ≥ 70%) AND (rainfall_mm_next_7d ≥ 50 mm)
```
On network failure, or when the field has no coordinates, this step degrades gracefully: it reuses the last cached/stored snapshot if one exists, attaches a flag (`WEATHER_FETCH_ERROR` or `NO_COORDINATES`), and never fabricates a forecast. A `mock_weather` object in the request body can substitute for a real fetch — this is how demos and automated tests deterministically produce a specific weather outcome.
**Output:** a `WeatherContext` — `{rainfall_mm_next_7d, rainfall_probability, heavy_rain_alert, snapshot, flags}`.

### 4.5 The Nutrient Ledger — the core conversion chain

This is the single most important stage; every number here is arithmetic, not inference.

**Input:** `SoilContext` + `CropContext` (specifically `crop_code` and `recommendation_type`).

**Conversion, in order:**

```
STEP A — RDF lookup (a database read, not a computation):
   Required_N, Required_P2O5, Required_K2O
       ← SELECT n_kg_ha, p2o5_kg_ha, k2o_kg_ha
         FROM fertilizer_recommendations
         WHERE crop_id = ? AND recommendation_type = ?

STEP B — unit interconversion (elemental → oxide):
   Available_P2O5 = soil_p_kg_ha × 2.2919
   Available_K2O  = soil_k_kg_ha × 1.2046
   Available_N    = soil_n_kg_ha              (nitrogen has no elemental/oxide split)

STEP C — the gap (this is the literal answer to "WHY" in the proof object):
   Gap_N    = max(0, Required_N    − Available_N)
   Gap_P2O5 = max(0, Required_P2O5 − Available_P2O5)
   Gap_K2O  = max(0, Required_K2O  − Available_K2O)

STEP D — hand off to the Optimizer stage (Section 4.6) for the gap → product conversion
```

**Output:** a `LedgerResult` — `{status, required{}, available{}, gap{}, flags, citation}` — persisted immediately as a row in `nutrient_ledger_entries`, independent of whether the rest of the pipeline succeeds, so the gap calculation itself is always auditable even if a later step fails.

**Abstain conditions at this stage [CODE]:** no RDF row for the crop/type combination; no soil test at all; an unresolved residual-credit situation (an application logged after the soil sample with no sourced retention policy configured).

### 4.6 The Optimizer — gap → physical product quantities

**Input:** `LedgerResult.gap` (three numbers: Gap_N, Gap_P2O5, Gap_K2O) and the `fertilizer_products` table (each product's guaranteed N/P2O5/K2O percentage per the Fertilizer Control Order).

**Path A — default heuristic** (see Section 5.7's neighbour, but the logic itself is pure arithmetic, not an LP):
```
DAP_kg_ha    = Gap_P2O5 / 0.46
N_from_DAP   = DAP_kg_ha × 0.18
remaining_N  = max(0, Gap_N − N_from_DAP)
Urea_kg_ha   = remaining_N / 0.46
MOP_kg_ha    = Gap_K2O / 0.60
```

**Path B — opt-in linear program** (triggered by `{"optimizer": "scipy_linprog"}` in the request body): the same three gap numbers become the right-hand side of three inequality constraints; `scipy.optimize.linprog` searches over nine possible products for the combination that satisfies all three constraints while minimizing total kilograms (full mechanics in Section 5.7).

**Interconversion safety check:** in the default path, the optimizer's own DAP/Urea/MOP numbers are compared against the Ledger's `convert_gap_to_products()` output computed independently; if they differ, the Ledger's numbers are what get used, and an `OPTIMIZER_LEDGER_MISMATCH` flag is recorded. This means the *only* number that ever reaches a farmer on the default path has been computed twice, by two independent code paths, and reconciled.

**Output:** `plan_kg_ha` — e.g. `{"DAP_kg_ha": 358.0, "UREA_kg_ha": 36.7, "MOP_kg_ha": 144.3}` — plus, on the LP path, `total_kg_ha`, `gap_met`, and a comparison against what the heuristic would have produced.

### 4.7 Validation / Rule Engine

**Input:** `plan_kg_ha` + `SoilContext` + `WeatherContext`.
**Conversion:** each rule in `core/rules.py` is evaluated independently and returns a pass/fail plus a severity (HARD or SOFT). A HARD failure (e.g. an active heavy-rain alert conflicting with the planned application window) blocks the plan from proceeding in its current form and forces a safer state (a deferred window). A SOFT failure (e.g. pH outside 5.5–8.0) adds a warning flag but lets the plan through unchanged.
**Output:** `{is_valid, warnings[], blocking_issues[], flags_added[], violations[]}`, merged into the shared flag list that Section 4.9 will later consume.

### 4.8 Knowledge Agent (RAG) — evidence retrieval, never numbers

**Input:** `crop_code`, `recommendation_type`, and implicitly the field's region.
**Conversion chain** (full mechanics in Sections 5.3–5.5):
```
build a natural-language query string
   e.g. "Pre-seasonal fertilizer recommendation for SUGARCANE in Kolhapur"
   ▼
apply hard metadata filters (region, crop) to the 76-chunk corpus
   ▼
rank the filtered candidates by BM25 keyword score
   ▼
rank the same candidates by dense cosine similarity (if the embedding
model is available; otherwise this branch is skipped entirely)
   ▼
fuse the two ranked lists with Reciprocal Rank Fusion
   ▼
take the top-k chunks
```
**Output:** an `EvidencePack` — `{query, chunks[{text, metadata, score, citation}], confidence, flags, summary}`. The `summary` field is the one and only place an LLM call happens in this stage, and it summarises the retrieved *text*, nothing numeric. This output is attached to the final proof object for display; it never feeds back into `plan_kg_ha`.

### 4.9 Confidence assembly

**Input:** the complete accumulated flag list from every prior stage (soil staleness, unit-normalization notices, rule violations, weather fetch errors, optimizer reconciliation notices, RAG coverage).
**Conversion:**
```
if any flag contains "ABSTAIN":       confidence = "ABSTAIN"     (short-circuit)
else:
   material_flags = flags minus a small ignore-list
                    (OPTIMIZER_*, NO_COORDINATES, WEATHER_FETCH_ERROR,
                     STAGE_NOT_IN_CALENDAR — these are informational, not
                     evidence of numeric uncertainty)
   0 material flags  → "HIGH"
   1 material flag   → "MEDIUM"
   2+ material flags → "LOW"
```
**Output:** a single confidence string, attached to the final proof object.

### 4.10 Proof assembly and persistence

**Input:** everything produced by Sections 4.5–4.9.
**Conversion:** the six-question object is assembled — `what` (product names), `how_much` (copied verbatim from `plan_kg_ha`, never recomputed here), `when` (a label derived from the weather state — see the master knowledge document for the exact three cases), `why` (the full `required`/`available`/`gap` breakdown), `based_on` (farm data references plus the `EvidencePack`), and `confidence` (from Section 4.9).
**Output:** the JSON object returned to the caller, simultaneously written to the `recommendations` table with `status = PROPOSED`, and a `PLAN_CREATED` event published on the event bus.

### 4.11 The Yield Model — a parallel, read-only branch

**Input:** the *finished* `LedgerResult` (required/available/gap and the final `plan_kg_ha`), plus `SoilContext` and a caller-supplied seasonal rainfall total.
**Conversion:** the inputs are assembled into a fixed 27-feature vector (raw soil values, the applied plan, engineered sufficiency ratios, one-hot crop/district/irrigation columns — see Section 5.6 for the exact list) and passed to the crop-specific XGBoost regressor, running in an isolated subprocess with a 15-second timeout.
**Output:** `{predicted_yield_kg_ha, yield_band, confidence, extrapolation, caveats}` — attached to the API response as an annotation. **This output has no path back into the Ledger, the Optimizer, or the confidence calculation in Section 4.9** — it is a dead-end branch by design.

### 4.12 Monitoring Agent and event-driven replanning

**Input:** any published event (`HEAVY_RAIN_ALERT`, `SOIL_REPORT_UPDATED`, `CROP_STAGE_CHANGED`, `FERTILIZER_APPLIED`, `WEATHER_FORECAST_CHANGED`).
**Conversion:** the event type is looked up in a fixed map that names exactly which agents from Sections 4.2–4.8 need to re-run:
```
HEAVY_RAIN_ALERT          → re-enter at: weather → optimizer → validation
SOIL_REPORT_UPDATED       → re-enter at: soil → ledger → optimizer → validation
CROP_STAGE_CHANGED        → re-enter at: crop → ledger → optimizer → validation
FERTILIZER_APPLIED        → re-enter at: ledger → optimizer → validation
every case always finishes with: knowledge → confidence → persist
```
Any stage not listed simply reuses its previous output from the currently active plan, rather than recomputing it.
**Output:** the previous `recommendations` row is updated to `status = SUPERSEDED`; a new row is inserted with `status = PLAN_REVISED`; a `PLAN_INVALIDATED` alert is recorded.

---

## 5. Component background primers

### 5.1 EasyOCR — what it is, how it recognises text, background

**[BG]** Optical Character Recognition (OCR) is the general problem of turning an image containing text into machine-readable characters. It has two sub-problems: **detection** (where in the image is text located — drawing bounding boxes around words or lines) and **recognition** (given a cropped region that's believed to contain text, what characters does it say).

**EasyOCR** is an open-source Python OCR library (from the JaidedAI team) built on deep learning rather than the older, hand-engineered approach (classical OCR engines like early Tesseract relied heavily on pixel-pattern matching and struggled with skewed, low-quality, or handwritten text). EasyOCR's pipeline is, at a high level:

1. **Text detection** using a CRAFT-style (Character Region Awareness For Text detection) convolutional neural network, which produces a heatmap of "how likely is each pixel to be part of a character" and groups nearby high-likelihood regions into bounding boxes around words or lines.
2. **Text recognition** using a CRNN (Convolutional Recurrent Neural Network) architecture: a convolutional backbone extracts visual features from each cropped text region, a recurrent layer (typically an LSTM) reads those features left-to-right the way a person reads a line, and a CTC (Connectionist Temporal Classification) decoding layer converts that sequence of feature predictions into the actual output string, correctly handling the fact that a printed character can span a variable number of pixel columns.
3. Each recognised piece of text comes with a confidence score derived from how certain the recognition network was at each decoding step.

**How Kisan Saathi uses it specifically [CODE]:** `core/ocr.py` lazily initialises a single shared `easyocr.Reader(["en"], gpu=use_gpu)` instance (English-only, GPU used if available, otherwise CPU) the first time OCR is needed, caching its downloaded recognition model weights locally so subsequent calls don't re-download anything. It's called via `reader.readtext(image_path, detail=1)`, which returns exactly the `(bounding_box, text, confidence)` triples described above. This is the second pass in a **dual-pass strategy**: `pypdf` is tried first for digitally-generated PDFs (which have an actual embedded text layer and need no OCR at all — this is faster and more accurate whenever it applies), and EasyOCR is the fallback for scanned images, photographs of paper cards, or PDFs that turn out to be scanned-image-only with no text layer.

**Why this choice, and its real limits:** EasyOCR was chosen because it needs no separate installation of an external OCR engine binary (it's pure Python plus PyTorch), supports the mixed English/regional-script text often seen on Indian agricultural documents by simply changing the language list, and ships pretrained weights that work reasonably well out of the box without requiring the team to train a custom recognition model from scratch — which would have needed a large labeled dataset of soil health cards that doesn't exist. Its real limits, honestly: recognition confidence genuinely drops on poor handwriting, low-contrast photocopies, and skewed phone photos, which is exactly why the system never trusts a raw OCR output directly — it's always gated by the 0.85 confidence threshold and human review described in Section 4.1.

### 5.2 pypdf — direct text extraction

**[BG]** Many PDFs are not scanned images at all — they were generated directly from a word processor, a form-filling tool, or a government e-portal, and the actual character data is embedded in the file's internal structure (a sequence of drawing commands specifying which font, at which position, draws which glyph). `pypdf` is a pure-Python library that parses this internal PDF structure directly and reconstructs the text without needing any image analysis or machine learning at all — it is exact and essentially free computationally when it applies, but it produces nothing useful for a photographed or scanned document, since those PDFs contain only an embedded image, not real character data. That's exactly why the system tries `pypdf` first and only falls back to the much more expensive EasyOCR path when `pypdf` returns no usable text.

### 5.3 BM25 — keyword retrieval, the math behind the score

**[BG]** BM25 (Best Match 25) is a classic information-retrieval ranking function, a refinement of the older TF-IDF (term frequency–inverse document frequency) idea. Given a query and a document (here, a chunk of agronomic text), it scores how relevant that document is to the query using two ideas balanced against each other:

- **Term frequency (TF):** a query word that appears more often in a document is (up to a point of diminishing returns) more likely to be about that topic. BM25 deliberately *saturates* this — the 10th occurrence of a word adds much less score than the 2nd, which prevents a document from gaming the ranking by simply repeating a keyword many times.
- **Inverse document frequency (IDF):** a query word that appears in almost every document in the corpus (like "fertilizer" in an agronomy corpus) carries less discriminating power than a rare word (like "tillering"), so rare, specific words are weighted more heavily.

The formula, in outline:
```
score(query, doc) = Σ over each query term t [ IDF(t) × ( f(t,doc) × (k1+1) )
                                                 / ( f(t,doc) + k1 × (1 − b + b × |doc|/avgdoclen) ) ]
```
where `f(t,doc)` is how many times term t appears in the document, `k1` controls how quickly term-frequency saturates, and `b` controls how much a document's length is penalised (a longer document naturally contains more words, so raw counts alone would unfairly favour it). BM25 needs no training, no GPU, and no external model download — it's pure counting and arithmetic over the text already in the corpus — which is why it's the retrieval method that "always works" in this system, with no fallback needed.

**How it's used here [CODE]:** the `rank_bm25` Python package's `BM25Okapi` implementation is built once, at startup, over all 76 chunks from the four source documents, tokenised by simple lowercased whitespace splitting.

### 5.4 Sentence-transformers + FAISS — dense/semantic retrieval

**[BG]** BM25's weakness is that it only matches literal words. A query for "how much nitrogen should I apply during tillering" would score poorly against a document chunk that discusses "the critical N top-dress window for young rice" even though they mean nearly the same thing agronomically — none of the important words match exactly.

**Dense (semantic) retrieval** solves this by first converting both the query and every document chunk into a fixed-length numeric vector — an **embedding** — using a neural network trained so that pieces of text with similar *meaning* end up close together in that vector space, regardless of exact wording. `sentence-transformers` is a library built on top of transformer models (the same family of architecture behind large language models, but here used purely to produce embeddings, not to generate text) specifically fine-tuned so that whole-sentence similarity is meaningful, not just word-by-word similarity. The specific model named in this project, `all-MiniLM-L6-v2`, produces a 384-dimensional vector for any input text; it's a distilled ("Mini") model with 6 transformer layers (hence "L6"), chosen because it's small and fast enough to run on ordinary CPU hardware while still producing good general-purpose sentence embeddings, rather than needing a GPU-hosted large model.

Once every chunk has an embedding, finding the most semantically similar chunks to a query embedding is a nearest-neighbour search problem. **FAISS** (Facebook AI Similarity Search) is a library purpose-built for this: for a corpus this small (76 chunks), it uses a simple exact "flat" index (`IndexFlatIP` — inner product), and after L2-normalising every vector, the inner product between two normalised vectors is mathematically identical to their cosine similarity — a standard measure of how aligned two vectors' directions are, ranging from -1 (opposite meaning) to 1 (identical meaning).

**How it's used here, including a real observed limitation [RAN]:** this dense path is entirely optional. If `sentence-transformers` and `faiss` are not importable, or if the `all-MiniLM-L6-v2` model weights cannot be downloaded from Hugging Face (its model hub) on first use, the system logs the failure and falls back to BM25-only mode with no crash. This was directly observed during verification of this project: in a network-restricted environment, the download to Hugging Face returned a 403 Forbidden, the log explicitly printed "Dense index failed — BM25-only mode," and retrieval continued to function correctly using BM25 alone.

### 5.5 Reciprocal Rank Fusion (RRF) — merging two rankings

**[BG]** BM25 scores and cosine similarity scores live on completely different, non-comparable numeric scales — a BM25 score might be 8.3, a cosine similarity is always between -1 and 1 — so you cannot just average them together meaningfully. RRF sidesteps this by throwing away the raw scores entirely and working only with each chunk's **rank position** in each list:
```
RRF_score(chunk) = Σ over every ranked list containing this chunk [ 1 / (k + rank_in_that_list) ]
```
with `k` conventionally set to 60. A chunk that appears near the top of *both* the BM25 ranking and the dense ranking accumulates a meaningfully larger combined score than one that only one method ranked highly, and because it only ever uses rank position (1st, 2nd, 3rd, ...), it needs no scale-normalisation and no manually-tuned weighting between the two retrieval methods — a real practical advantage when you don't have labeled relevance data to tune such weights against.

### 5.6 XGBoost — gradient-boosted trees, and what this specific model was trained on

**[BG]** XGBoost ("Extreme Gradient Boosting") is one of the most widely used algorithms for structured/tabular data prediction. It builds a **gradient-boosted ensemble of decision trees**: rather than fitting one large tree, it fits a small tree to the data, looks at the *errors* that tree still makes (the residuals), fits a second small tree specifically to correct those residual errors, then a third tree to correct what's still wrong after the first two, and so on — each new tree is trained on the *gradient* of the loss function with respect to the current combined prediction (hence "gradient boosting"). The final prediction is the sum of every tree's small contribution. This tends to outperform a single decision tree substantially while remaining much faster to train and easier to interpret than a deep neural network, which is why it's a standard choice for tabular regression problems with a moderate number of engineered features, exactly the situation here.

**Exactly what was trained here [CODE, verified from the training script]:**
- One separate `XGBRegressor` per crop — Banana, Sugarcane, Cotton, Soybean — four models total, each predicting that crop's yield in kg/ha.
- Hyperparameters: `n_estimators=200` (200 trees in the ensemble), `max_depth=5` (each tree is shallow, limiting how complex a single tree's decision boundary can be, which helps prevent overfitting on a modest dataset), `learning_rate=0.05` (each tree's correction is scaled down by 5%, so many small, cautious corrections are preferred over a few large, potentially overfit ones), `subsample=0.8` and `colsample_bytree=0.8` (each tree is trained on a random 80% of the rows and 80% of the feature columns, which — much like a random forest — reduces overfitting by preventing any single tree from seeing the exact same data), `reg_lambda=1.0` (L2 regularisation, penalising overly large tree-leaf weights), and `min_child_weight=3` (a tree split is only allowed if the resulting branches would each contain a reasonably-sized group of samples, preventing the tree from creating tiny, noise-fitting splits).
- 27 input features per model: five raw soil values (N, P, K, pH, organic carbon), the seasonal rainfall total, the actual applied N/P2O5/K2O from that recommendation's plan, three engineered "percent of RDF" ratios, three engineered sufficiency proxies, and one-hot encoded categorical columns for crop, district (Kolhapur/Jalgaon), and irrigation type.
- Data was split 80/20 (`train_test_split(..., test_size=0.2, random_state=42)`) into training and a held-out test set, with the fixed `random_state` making the split reproducible.

**The honesty mechanisms layered on top of a standard model [CODE]:** scope restriction to exactly the four trained crops and two trained districts (anything else returns `ABSTAIN`), an `extrapolation` flag when the fertilizer plan being evaluated falls well outside the range of plans the model saw during training (roughly 40–130% of RDF), and coarse confidence bands tied to each crop model's own validation R² rather than reporting an artificially precise number — all covered in more depth in the master knowledge document.

### 5.7 SciPy `linprog` and the HiGHS solver — linear programming in one page

**[BG]** A **linear program (LP)** is an optimization problem where you're looking for the values of some decision variables that minimize (or maximize) a linear objective function, subject to a set of linear inequality or equality constraints. The classic textbook framing: "given a budget and per-unit costs, and minimum requirements you must meet, find the cheapest combination that satisfies every requirement." This is exactly the shape of the fertilizer product-mix problem: the decision variables are "how many kilograms of each of the 9 products to use," the objective is "minimize the total kilograms," and the constraints are "the combined N, P2O5, and K2O supplied must each be at least the computed gap."

`scipy.optimize.linprog` is SciPy's general-purpose LP solver interface. **HiGHS** (High performance Optimization Software) is the specific solving algorithm selected here (`method="highs"`) — an open-source, actively maintained implementation of the two classical families of LP algorithm: the **simplex method** (which walks along the edges of the geometric solution space — a high-dimensional polyhedron defined by the constraints — from vertex to vertex, always moving to an adjacent vertex that improves the objective, until no further improvement is possible) and **interior-point methods** (which instead move through the *interior* of that feasible region along a path that converges to the optimal corner, often faster for larger problems). HiGHS automatically picks an appropriate strategy and is widely regarded as one of the strongest open-source LP solvers available, which is why it was chosen over writing a custom solver or depending on a commercial one.

**Why minimise weight and not cost [CODE + reasoning]:** the objective function's coefficients (the "cost" of using one more kilogram of each product) are currently all set to 1, meaning the true objective is "minimise total kilograms of product applied," not currency. This is explicitly because no sourced, citable fertilizer price table exists for the pilot region — inventing prices would produce a plausible-looking number nobody could verify, exactly the failure mode the whole system exists to avoid. The constraint structure would not need to change at all if a sourced price table became available later: the coefficient vector would simply change from `[1, 1, 1, ...]` to `[price_urea, price_dap, price_mop, ...]`.

**What happens when the LP has no valid solution [CODE]:** if the constraints are somehow infeasible (which should not normally happen given how the gaps are constructed, but is checked defensively) or the solver reports any non-success status, the code automatically falls back to the deterministic heuristic plan from Section 4.6's Path A, attaching an `OPTIMIZER_FALLBACK` flag, rather than surfacing a solver error to the end user.

### 5.8 FastAPI, SQLite/PostgreSQL, the event bus — the software substrate

**[BG + CODE]** **FastAPI** is a modern Python web framework that uses type hints (via the Pydantic library) to automatically validate incoming request data and generate API documentation, and that is built on `asyncio`, Python's native asynchronous I/O model, allowing the server to handle many concurrent requests without needing a thread per request. **SQLite** is a serverless, file-based relational database — the entire database lives in one file on disk, needs no separate server process, and is ideal for local development and small-to-medium deployments; **PostgreSQL** is a full client-server relational database used for production/cloud deployment. This project's `app/db.py` provides one connection abstraction so the same application code works against either backend, selected purely by which environment variable is set (`AGROTWIN_DB` for a SQLite file path, or `DATABASE_URL` for a Postgres connection string). The **event bus** (`core/event_bus.py`) is a simple in-process publish/subscribe mechanism: components call `publish(event)`, and any component that previously called `subscribe(event_type, handler_function)` for that event type gets its handler invoked synchronously, in the same request — it is not a separate message-queue service, which is an honest scaling limitation worth knowing (see the roadmap in the master knowledge document).

---

## 6. Every unit conversion and formula used anywhere in the pipeline

| Conversion / formula | Formula | Source |
|---|---|---|
| Elemental phosphorus → P₂O₅ | `P2O5 = P × 2.2919` | FAO, Appendix Table 16 (141.94/61.98 molar mass ratio) |
| Elemental potassium → K₂O | `K2O = K × 1.2046` | FAO, Appendix Table 16 (94.20/78.20 molar mass ratio) |
| Nutrient gap | `gap = max(0, required − available − residual_credit)` | Ledger core rule |
| DAP quantity (heuristic) | `DAP_kg_ha = Gap_P2O5 / 0.46` | DAP is 46% P2O5 (FCO) |
| Nitrogen credited from DAP | `N_from_DAP = DAP_kg_ha × 0.18` | DAP is 18% N (FCO) |
| Urea quantity (heuristic) | `Urea_kg_ha = max(0, Gap_N − N_from_DAP) / 0.46` | Urea is 46% N (FCO) |
| MOP quantity (heuristic) | `MOP_kg_ha = Gap_K2O / 0.60` | MOP is 60% K2O (FCO) |
| LP objective | `minimize Σ x_i` subject to `Σ (x_i × nutrient%_i/100) ≥ gap` for N, P2O5, K2O | `scipy.optimize.linprog`, HiGHS |
| Heavy-rain trigger | `probability ≥ 70% AND rainfall_7d ≥ 50 mm` | `region_config.py`, engineering default |
| Soil staleness | `today − test_date > 180 days` | `region_config.py`, engineering default |
| pH safe window | `5.5 ≤ pH ≤ 8.0` | `region_config.py`, engineering default |
| EC safe limit | `EC ≤ 4 dS/m` | `region_config.py`, engineering default |
| Confidence tiering | `0 material flags → HIGH; 1 → MEDIUM; 2+ → LOW; any ABSTAIN flag → ABSTAIN` | `twin_state.compute_confidence` |
| RRF fusion score | `Σ over rank lists [ 1 / (60 + rank) ]` | Standard RRF, k=60 |
| BM25 score | `Σ_t IDF(t) × f(t,d)(k1+1) / (f(t,d)+k1(1−b+b·|d|/avgdl))` | Okapi BM25, `rank_bm25` defaults |
| OCR review gate | `confidence < 0.85 → mandatory human review` | `core/ocr.py` |

---

## 7. Two fully worked examples end to end

### Example 1 — a normal recommendation, dry weather [RAN on FINAL_V1]

```
INPUT   field REAL-001, Sugarcane, recommendation_type PRE_SEASONAL
        soil_test: N=258.7, P=2.33, K=69.26 kg/ha (elemental), pH=6.26

Soil Agent   → test is 3,650 days old → STALE_SOIL_DATA flag
Crop Agent   → stage resolved from sowing date; no calendar-range match issue
Weather      → mock: no heavy rain

Ledger:
  Required   N=340, P2O5=170, K2O=170          (RDF lookup)
  Available  P2O5 = 2.33 × 2.2919 = 5.34
             K2O  = 69.26 × 1.2046 = 83.43
  Gap        N=81.3, P2O5=164.66, K2O=86.57

Optimizer (heuristic):
  DAP  = 164.66 / 0.46           = 358.0 kg/ha
  N_from_DAP = 358.0 × 0.18      = 64.4
  remaining_N = 81.3 − 64.4      = 16.9
  Urea = 16.9 / 0.46             = 36.7 kg/ha
  MOP  = 86.57 / 0.60            = 144.3 kg/ha

Validation   → no hard violations (no rain conflict, pH in window)
Knowledge    → 4 BM25-ranked chunks from mpkv_icar_rdf.md
Confidence   → 2 material flags (STALE_SOIL_DATA, NUTRIENTS_NORMALIZED) → LOW

OUTPUT  {"DAP_kg_ha": 358.0, "UREA_kg_ha": 36.7, "MOP_kg_ha": 144.3},
        confidence LOW, citations attached, status PLAN_GENERATED
```

### Example 2 — the same field, a heavy-rain event arrives afterward [RAN on FINAL_V1]

```
EVENT   POST /events {type: HEAVY_RAIN_ALERT, field_id: 1,
                       payload: {rainfall_probability: 90, rainfall_mm_next_7d: 80}}

Monitoring Agent looks up HEAVY_RAIN_ALERT → re-enter at: weather, optimizer, validation
  (soil and crop are NOT re-read — nothing about the field's chemistry changed)

Weather (re-run)  → heavy_rain_alert = (90% ≥ 70%) AND (80mm ≥ 50mm) = True
Ledger            → REUSED from the previous plan, unchanged: same gap as Example 1
Optimizer         → REUSED: same DAP/Urea/MOP quantities as Example 1
Validation (re-run) → WEATHER_WINDOW_HEAVY_RAIN rule fires (HARD) → window must defer
Knowledge, Confidence, Persist all re-run per the fixed replan tail

OUTPUT  same plan_kg_ha as before (quantities unchanged — correctly, since rain
        doesn't change soil chemistry), but "when" now reads a deferral instruction,
        status PLAN_REVISED, previous recommendation row marked SUPERSEDED,
        an alert of type HEAVY_RAIN_ALERT recorded for follow-up.
```
