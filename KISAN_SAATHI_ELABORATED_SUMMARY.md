# Kisan Saathi (AgroTwin AI) — Elaborated Technical & Conceptual Summary

**Team:** Caesar Cipher (IH26-T036) — Yachna Sharma, Lavesh Sachdev, Jatin Lachhani, Krishna Shiringi
**Branch verified:** `FINAL_V1`, commit `7e215c8` (2026-09-29)
**Problem statement:** PSAI01 — *Sustainable Fertilizer Usage Optimizer for Higher Yield*

> Excessive and improper fertilizer use degrades soil and reduces productivity, hurting farmer income. The brief asks for a data-driven application that reads soil health, crop type and weather to recommend the right fertilizer type and quantity — a simple schedule of what, how much and when to apply — while flagging the risk of over-application, so farmers spend less, protect their soil, and raise yield.

This document explains, end to end, how Kisan Saathi answers that brief: the agronomy behind it, the retrieval and optimization systems, the software architecture, and the exact chain of computation that turns a soil test into a bag of fertilizer. It is written so that a reader with no prior context — including a technical judge or a new teammate — finishes it able to explain and defend every number the system produces.

**How to use this document.** Read Sections 1–3 first if you are short on time — they carry the load-bearing ideas (fertilizer arithmetic, and the rule that the Ledger alone produces kg/ha). Sections 4–8 go progressively deeper into retrieval, models, and rule enforcement. Section 9 is the honest state of the system: what is verified, what is not, and where an earlier internal draft slightly overstated the code.

---

## Table of contents

1. The agronomy the software encodes
2. The three-layer trust boundary (why an LLM can never set a dose)
3. The Nutrient Ledger — the one place a kilogram is born
4. Turning a gap into bags: the optimizer (heuristic and linear-programming)
5. The Agentic RAG pipeline (retrieval, fusion, evidence)
6. The XGBoost yield model — a read-only annotation
7. The full pipeline: eleven steps, in order
8. Continuous monitoring and event-driven replanning
9. Rules, thresholds, and the honesty of "abstain"
10. Frontend, OCR, and the human-in-the-loop
11. System architecture and technology stack
12. What was actually verified in this session
13. Glossary

---

## 1. The agronomy the software encodes

### 1.1 Why fertilizer is a decision problem, not a lookup

A crop's yield depends on how well its nutrient needs are met across the season. Two nutrients matter for almost every decision AgroTwin/Kisan Saathi makes:

- **Nitrogen (N)** drives leaf and stem growth. It is the most mobile nutrient in soil — heavy rain leaches it below the root zone, and surface urea can be lost to the air as ammonia gas in hot, alkaline conditions. This is *why weather matters to fertilizer timing*.
- **Phosphorus and potassium** are reported by soil labs as the elements P and K, but every recommended dose and every fertilizer bag label speaks in **oxide** form: P₂O₅ and K₂O. This single unit mismatch is the most common source of real-world fertilizer miscalculation, and it is the first thing the system corrects.

The blanket advice farmers usually get ("two bags of urea per acre") ignores all field-specific information: what the soil test already shows, what growth stage the crop is at, and what the sky is about to do. Kisan Saathi's job is to replace that blanket number with an auditable, field-specific one.

### 1.2 The unit conversion that everything rests on

Soil test lab reports give elemental P and K in kg/ha. Recommended doses (RDF) and fertilizer percentages are in oxide form. The conversion is chemistry, not opinion — it comes from the molecular weight ratio between an element and its oxide:

```
P2O5 (kg/ha) = P (kg/ha) × 2.2919      (141.94 / 61.98, oxide/element molar mass ratio)
K2O  (kg/ha) = K (kg/ha) × 1.2046      (94.20 / 78.20)
```

Source: FAO, *Fertilizer use by crop*, Appendix Table 16. This conversion is a **stoichiometric equivalence**, not an "availability factor" — it does not claim the soil will release 100% of that P to the plant, it only expresses the same physical quantity of phosphorus in the units the rest of the system uses. Skipping it, or worse, treating a soil test's raw P number as directly comparable to a P₂O₅ requirement, is the single most common real-world fertilizer calculation error, and it's the first thing the Ledger corrects.

### 1.3 Recommended Dose of Fertilizer (RDF)

An RDF is a government or university-published total nutrient requirement — kg/ha of N, P₂O₅, K₂O — for a crop across a season or defined phase, sourced from bodies such as **MPKV Rahuri** (Mahatma Phule Krishi Vidyapeeth) and **ICAR** (Indian Council of Agricultural Research). It is the target the Ledger subtracts the soil's existing supply from. RDFs are whole-crop totals: they say "this crop needs this much nitrogen across its life," not "apply this much today." Turning an RDF into a today's-dose schedule needs the crop calendar (Section 1.4) and the residual-credit accounting (Section 3.4) — both of which exist in the system but with real limits documented in Section 9.

### 1.4 Growth stages and why timing matters

Nutrient demand is not uniform across a crop's life. Sugarcane, for instance, needs heavy nitrogen and potassium during its "grand growth" phase (roughly 120–240 days after planting) but essentially nothing at harvest. Applying the right total at the wrong time wastes it — a urea dose two weeks before harvest does not turn into yield, it turns into runoff. Kisan Saathi's Crop Agent tracks each field's growth stage dynamically from its sowing date and a growth-stage calendar (ICAR-style stage boundaries in days-after-planting), rather than trusting a stage that was entered once at onboarding and never updated.

### 1.5 From a nutrient gap to a bag of fertilizer

A **nutrient gap** — say, 164.7 kg/ha of P₂O₅ still needed — is not something a farmer buys. Farmers buy **products**: Urea (46% N), DAP (18% N, 46% P₂O₅), MOP (60% K₂O), SSP, SOP, and several NPK complexes, each with a nutrient percentage fixed by India's **Fertilizer Control Order (FCO)**, a legal specification, not a guess. Converting a gap to product weight is one division: `kg product = kg nutrient needed ÷ (product's nutrient % ÷ 100)`. Because DAP supplies both phosphorus and a meaningful amount of nitrogen as a side effect, a sensible calculation order allocates DAP to the phosphorus gap first, credits the nitrogen it brings along, and only tops up the remaining nitrogen shortfall with urea. That ordering — DAP → credit N → Urea → MOP — is exactly what the system's default heuristic does (Section 4.1), and it mirrors how an agronomist would do it by hand.

---

## 2. The three-layer trust boundary — why an LLM can never set a dose

### 2.1 The single most important design rule

> **Fertilizer quantities (kg/ha) are born in exactly one place — the Nutrient Ledger — and nowhere else.**

Every other component — retrieval, the yield model, the LLM, the optimizer's product-mix choice — is either **read-only** or **advisory**. This isn't a policy statement layered on top of the code; it is a structural property you can verify by reading a small number of files.

| Component | Role | Can it ever produce a kg/ha figure? |
|---|---|---|
| Nutrient Ledger | Deterministic gap computation | **Yes — the sole authority** |
| RAG / Knowledge Agent | Text evidence and citations | No |
| XGBoost yield model | Directional yield estimate | No |
| LP Optimizer | Product-mix selection | Opt-in only; on the default path the Ledger still overrides it if they disagree |
| LLM (Groq/xAI) | Summarise evidence text, write narrative | No |
| Validation Agent | Rule checks, warnings | No |

### 2.2 Why this matters more than any single feature

Generative language models are excellent at producing *plausible-sounding* numbers that are not grounded in any actual calculation — the "hallucination" problem. In a domestic agriculture context this is not a cosmetic flaw: a hallucinated "apply 90 kg/ha of urea" looks exactly as confident as a correctly computed one, but an agronomist has no way to tell them apart just by reading the output. Institutional users — state agriculture departments, cooperatives, extension officers — will not adopt a system whose core numbers cannot be traced back to a rule, a table, and a formula. That is the **trust deficit** the problem statement is implicitly asking to be solved, and it is why the architecture keeps a hard wall between "things that compute numbers" and "things that use language."

### 2.3 How the wall is actually built

1. **The proof object's `how_much` field is copied, not generated.** The code that assembles the final six-question answer (`core/proof.py`) takes the quantity dictionary directly from the optimizer's `plan_kg_ha` or the Ledger's `plan_kg_ha` — there is no step where an LLM call's output is written into this field.
2. **The LLM client (`core/llm.py`) is called in exactly three places**, and none of them touch quantities: (a) the narrative explanation attached to a finished recommendation, (b) an optional evidence summary that the main pipeline does not even use by default, and (c) OCR field-value suggestion when handwriting recognition is too uncertain. Every call is wrapped so that any failure — missing API key, network error, malformed response — returns an empty string rather than propagating an exception or a guessed number.
3. **The one legitimate nuance**: OCR's LLM assist can *propose* a soil N/P/K/pH value when the regex-based extraction from a scanned card is low-confidence. This is an *input* to the Ledger, not an output of it, and it is deliberately stamped with confidence 0.80 — below the system's 0.85 human-review threshold — so any LLM-suggested soil value is always routed to a person for confirmation before it can influence a calculation. This is a second, independent trust boundary, not a leak in the first one.

### 2.4 The four layers of intelligence

| Layer | Responsibility | Technology | LLM permitted? |
|---|---|---|---|
| Deterministic rules & tables | Nutrient requirements, hard safety limits, compatibility, stage calendars | Pure Python + data tables | No |
| Optimization | Turning a nutrient gap into a product mix | SciPy linear programming, or a fixed heuristic | No |
| Machine learning | Yield / response annotation only, where real training data exists | XGBoost | No, for numbers |
| LLM + retrieval | Evidence retrieval, explanation, orchestration/OCR assist | Hybrid RAG + an OpenAI-compatible chat client | Yes — explanation and retrieval only |

---

## 3. The Nutrient Ledger — the one place a kilogram is born

### 3.1 What it is

The Ledger (`agrotwin_api/ledger.py`, adapted for the live API by `app/ledger.py`) is not a machine-learning model. It is a small, deterministic, fully auditable calculator: a handful of pure functions with no randomness, no external calls, and no hidden state. Given the same soil test, crop, and RDF row, it always returns the same answer, and every intermediate number is visible in the output.

### 3.2 Its exact inputs

```python
{
  "field_id": "F-001",
  "crop_code": "SUGARCANE",
  "recommendation_type": "PRE_SEASONAL",   # which RDF row to use
  "current_stage": "GRAND_GROWTH",
  "soil_test": {
      "n_kg_ha": 258.7,     # available elemental N
      "p_kg_ha": 2.33,      # available elemental P
      "k_kg_ha": 69.26,     # available elemental K
      "ph": 6.26,
      "oc_percent": 1.10
  }
}
```

### 3.3 Its computation, step by step

**Step 1 — Look up the requirement.** The RDF table (sourced from MPKV/ICAR, one row per crop and recommendation type) is queried for the total season target:

```
Required_N, Required_P2O5, Required_K2O  ←  RDF[crop][recommendation_type]
```

If no RDF row exists for the crop/type combination, the Ledger **abstains** rather than inventing a number (see Section 9).

**Step 2 — Convert the soil baseline to the same units.**

```
Available_P2O5 = soil_P × 2.2919
Available_K2O  = soil_K × 1.2046
```

**Step 3 — Compute the net gap**, the actionable shortfall the farmer needs to make up:

```
Gap_N    = max(0, Required_N    − Available_N)
Gap_P2O5 = max(0, Required_P2O5 − Available_P2O5)
Gap_K2O  = max(0, Required_K2O  − Available_K2O)
```

`max(0, …)` matters agronomically as well as arithmetically: if the soil already supplies more than the crop needs, the gap is zero, not negative. A negative gap would imply "remove fertilizer from the soil," which is meaningless — the system correctly reports `NO_FERTILIZER_NEEDED` in that case, rather than a negative quantity.

**Step 4 — Convert the gap into product quantities** using the default DAP → Urea → MOP heuristic (the full mechanics are in Section 4.1).

### 3.4 What the Ledger deliberately excludes, and why

- **Nutrient losses** (leaching, volatilisation) are not subtracted from the gap, because no sourced, citable loss-factor table exists for the pilot region. The code treats this as a conservative simplification — it may slightly overstate the dose needed rather than understate it, which is the safer direction to err on.
- **Residual credit from past fertilizer applications** is handled by a separate module (`core/application_history.py`) with a strict rule: an application logged *before* the soil sample is assumed to already be reflected in that soil test and is not double-credited; an application logged *after* the soil sample can only be credited if a sourced "residual policy" (what fraction of a past application is still available, and for how long) is supplied via configuration. Without that policy, a field with a post-sample application **abstains** rather than guessing at how much of the old fertilizer is still in the soil. This is a genuine, deliberate gap-vs-guess tradeoff: the system would rather say "I don't have enough information" than quietly assume a number nobody sourced.
- **Loss adjustments and split-dose scheduling** (e.g. "never apply more than 50 kg N/ha in one dose," a rule stated in the underlying FCO/ICAR text) are retrievable through the evidence layer as guidance, but are not yet enforced as a hard rule in the calculation. This is an honest, documented limitation rather than a hidden one (Section 9).

### 3.5 Its output — the audit trail in one object

```python
{
  "status": "PLAN_GENERATED",              # or "NO_FERTILIZER_NEEDED" or "ABSTAIN"
  "required":  {"N": 340.0, "P2O5": 170.0, "K2O": 170.0},
  "available": {"N": 258.7, "P2O5": 5.34,  "K2O": 83.4},
  "gap":       {"N": 81.3,  "P2O5": 164.7, "K2O": 86.6},
  "plan_kg_ha": {"DAP_kg_ha": 358.0, "UREA_kg_ha": 36.7, "MOP_kg_ha": 144.3},
  "flags": ["NUTRIENTS_NORMALIZED (FAO aq348e, Appendix Table 16; P×2.2919, K×1.2046)"],
  "cost_estimate_inr": 12772   # advisory only — never a constraint on the plan
}
```

Every run also writes a row to `nutrient_ledger_entries`, so any number shown to a farmer or agronomist can later be traced back to the exact soil test, RDF row, and formula that produced it.

### 3.6 What the Ledger must never do

Stated as hard rules, verified structurally in the code: it never reads from the RAG/evidence layer; it never adjusts its output based on the yield model's prediction; and it never invents a requirement that isn't present in the RDF table. If any of those inputs is missing, the answer is abstention, not estimation.

---

## 4. Turning a gap into bags: the optimizer

### 4.1 The default heuristic (DAP → Urea → MOP)

This is the path used on every `/recommend` call unless a different optimizer is explicitly requested. It mirrors exactly how an agronomist allocates fertilizer by hand:

```
Step 1 — Use DAP to satisfy the entire P2O5 gap:
         DAP_kg_ha = Gap_P2O5 / 0.46                (DAP is 46% P2O5)

Step 2 — Credit the nitrogen DAP brings along as a side effect:
         N_from_DAP = DAP_kg_ha × 0.18               (DAP is also 18% N)
         remaining_N = max(0, Gap_N − N_from_DAP)

Step 3 — Use Urea to cover whatever nitrogen is still needed:
         Urea_kg_ha = remaining_N / 0.46              (Urea is 46% N)

Step 4 — Use MOP to satisfy the potassium gap:
         MOP_kg_ha = Gap_K2O / 0.60                   (MOP is 60% K2O)
```

Every number in this chain traces to an FCO-fixed composition percentage and the gap computed by the Ledger — there is nothing left to the optimizer's discretion in this path. As a safety measure, even on this default path, if a different optimizer's numbers were to disagree with what this heuristic/Ledger calculation produces, the **Ledger's numbers win** and an `OPTIMIZER_LEDGER_MISMATCH` flag is recorded — the optimizer is never allowed to silently overrule the Ledger on the default path.

### 4.2 The opt-in linear program

Triggered by passing `{"optimizer": "scipy_linprog"}` (or `linprog`) to `/recommend`. This formulates the same problem as a proper linear program and asks `scipy.optimize.linprog` (using the HiGHS solver) to solve it:

```
Decision variables:  x_i ≥ 0   for each of 9 fertilizer products
                      (Urea, DAP, MOP, SSP, SOP, Ammonium Sulphate,
                       19-19-19, 12-32-16, 10-26-26)

Objective:   minimize  Σ x_i                     (total kg/ha applied)

Subject to:  Σ (x_i × N%_i    / 100)  ≥  Gap_N
             Σ (x_i × P2O5%_i / 100)  ≥  Gap_P2O5
             Σ (x_i × K2O%_i  / 100)  ≥  Gap_K2O
             x_i ≥ 0
```

**Why minimize total weight rather than cost?** No authoritative, sourced fertilizer price table exists for the pilot region. Inventing prices would produce numbers that look precise but are not verifiable, exactly the kind of "plausible but unsourced" figure the whole architecture is built to avoid. Minimizing total physical weight is a real, defensible objective on its own — less product to transport, handle and apply also means less logistics cost and lower over-application risk — and the code is structured so that swapping in a sourced price vector later is a one-line change, not a redesign.

**Real comparison observed on a live field:** heuristic gave Urea 36.7 / DAP 358.0 / MOP 144.3 kg/ha; the LP gave Urea 36.6 / DAP 358.0 / MOP 144.3 — a rounding-level difference, not a disagreement in agronomic substance, for this particular case. If the solver fails (infeasible constraints, numerical error), the code falls back automatically to the heuristic plan with an `OPTIMIZER_FALLBACK` flag rather than returning an error to the user.

### 4.3 Who is allowed to decide what

| Decision | Decided by | Cannot be decided by |
|---|---|---|
| Required N/P2O5/K2O | Crop Agent + RDF lookup | Anyone else |
| Available N/P2O5/K2O | Soil Agent, from the DB | Anyone else |
| Nutrient gap | The Ledger (required − available) | Anyone else |
| Product quantities, default path | **The Ledger** | Optimizer, ML model, LLM |
| Product quantities, LP path | The LP optimizer | The Ledger (it checks for gross disagreement but does not silently override an opt-in choice) |
| Agronomic rule checks | Validation Agent + Rule Engine | Any upstream step |
| Evidence citations | Knowledge Agent (RAG) | Any other agent |
| Yield estimate | The XGBoost model | Ledger, Validation, RAG |

---

## 5. The Agentic RAG pipeline

### 5.1 Purpose and boundary

RAG (Retrieval-Augmented Generation) here means exactly one thing: **retrieving real text passages from curated agronomic documents and attaching them as citable evidence.** It is explicitly *not* allowed to calculate a quantity, invent a threshold, or override the Ledger's numbers. Its documents are MPKV/ICAR RDF guidelines, the FCO product-composition specification, and ICAR-style crop calendars — about 17 KB of markdown split into 76 chunks.

### 5.2 Ingestion

```
Markdown documents (rag/docs/*.md)
   → read raw file, parse YAML frontmatter (document_type, issuing_authority,
     publication_date, region, crops, nutrients, source)
   → split body into paragraphs (roughly 60–1200 characters, splitting long
     paragraphs at sentence boundaries)
   → extract any inline metadata inside a paragraph (e.g. "**crop**: rice",
     "**region**: kolhapur") — inline metadata overrides the document-level default
   → assign each chunk a citation like "mpkv_icar_rdf.md#para-12"
   → store in an in-memory ChunkStore
```

A chunk with no crop/region metadata is still stored but will not surface for a region- or crop-filtered query — it is effectively invisible to targeted retrieval, which is a deliberate precision choice.

### 5.3 Hybrid retrieval: BM25 + dense embeddings, fused by RRF

**BM25** (`rank_bm25`) is classic keyword search: it scores a chunk by term frequency weighted by how rare that term is across the whole corpus. It needs no GPU, never fails, and is strong on exact agronomic vocabulary ("urea nitrogen tillering").

**Dense retrieval** (optional; needs `sentence-transformers` and `faiss` installed, plus the ability to download the `all-MiniLM-L6-v2` embedding model) converts each chunk and the query into a 384-dimensional vector and ranks chunks by cosine similarity, computed efficiently via FAISS's inner-product index on L2-normalized vectors. This catches paraphrases and related concepts that share no exact words with the query.

**Reciprocal Rank Fusion (RRF)** merges the two ranked lists into one score without needing to reconcile their very different scales (BM25 scores and cosine similarities are not directly comparable):

```
RRF_score(chunk) = Σ over each ranked list [ 1 / (k + rank_in_that_list) ],   k = 60
```

A chunk ranked highly by *both* methods gets a meaningfully higher fused score than one that only one method liked, without any manual weight-tuning between the two signals.

**A concrete, verified detail worth knowing:** in this sandboxed test environment, the dense retrieval libraries are installed, but the one-time download of the embedding model from Hugging Face is blocked by network restrictions. The system's designed fallback behaviour worked exactly as intended: it logged the failure, fell back to BM25-only mode, and continued serving retrieval with **no crash and no degraded correctness guarantee** — RRF scores in BM25-only mode are simply based on one ranked list instead of two. This is a real demonstration of the "gracefully degrade rather than break" design principle applied outside the core fertilizer maths.

### 5.4 Hard metadata filtering — a safety feature, not just a precision feature

Before any ranking happens, the candidate chunk set is filtered by hard constraints (typically region and crop, e.g. `{"region": "kolhapur", "crop": "sugarcane"}`). This is deliberate: it stops the system from ever surfacing a genuinely correct-sounding but wrong-context passage — say, a rice recommendation being cited to support a sugarcane plan just because the words matched well. If strict filtering returns nothing, the Knowledge Agent retries without the filter and attaches a `RAG_NO_EVIDENCE`-style flag rather than silently returning irrelevant chunks or silently returning nothing at all.

### 5.5 The Knowledge Agent and its output contract

Called after the Ledger/optimizer has already produced a candidate plan (never before), it builds a natural-language query such as *"Pre-seasonal fertilizer recommendation for SUGARCANE in Kolhapur"* and returns an `EvidencePack`:

```python
EvidencePack:
    query: str
    chunks: list[EvidenceChunk]        # each with text, metadata, score, citation
    applicability_notes: str
    confidence: "HIGH" | "MEDIUM" | "LOW" | "NO_EVIDENCE"
    flags: list[str]
    summary: str                       # LLM-written synthesis of the chunk TEXT only
```

Confidence here is based purely on how many chunks were retrieved (roughly: 3+ chunks → HIGH, 1–2 → MEDIUM, 0 → NO_EVIDENCE) — it says something about *evidence coverage*, not about how correct the fertilizer number is. This is a subtlety worth being precise about in a presentation: "RAG confidence" and "recommendation confidence" (Section 9) are two different numbers computed two different ways, and conflating them overstates what either one means.

**A validation step afterward** checks that the retrieved evidence actually matches the query's region and crop, flagging `RAG_REGION_MISMATCH` or `RAG_CROP_MISMATCH` if something slipped through. Crucially, **`RAG_NO_EVIDENCE` never blocks a recommendation** — the Ledger's plan is persisted and shown regardless of whether supporting citations were found, because evidence is context for trust, not a prerequisite for the calculation to be valid.

### 5.6 Where the LLM enters, and where it is stopped

When chunks are found, an LLM call is used *only* to write a plain-English summary of the retrieved excerpts. That summary is attached to `EvidencePack.summary` for display and is never read back into anything that could affect `plan_kg_ha`. This is the second of the three narrow, text-only LLM call sites described in Section 2.3.

---

## 6. The XGBoost yield model — a read-only annotation

### 6.1 What problem it answers

After the Ledger has already finalized a fertilizer plan, the yield model answers a strictly secondary question: *"if the farmer follows this exact plan, what yield might realistically follow?"* It never runs before the plan exists, and it never changes the plan.

### 6.2 What it is, concretely

One XGBoost gradient-boosted-tree regressor per crop (Banana, Sugarcane, Cotton, Soybean — four models total), each trained on about 20 features: soil NPK/pH/organic carbon, the nutrients actually being applied, sufficiency ratios (applied vs required), a one-hot district encoding, and irrigation type. It is scoped to two districts, Kolhapur and Jalgaon.

### 6.3 Its honesty mechanisms

- **Scope discipline.** Outside its four supported crops or two supported districts, it returns `ABSTAIN` with a null prediction rather than extrapolating a number it has no basis for.
- **Extrapolation flag.** If the fertilizer plan being evaluated falls outside roughly 40–130% of the RDF target, the response is marked `extrapolation: true`, warning that the model is being asked about a regime its training data barely covers.
- **Coarse, honest confidence bands.** Rather than reporting a spuriously precise confidence number, the model reports one of three coarse bands (0.75 / 0.55 / 0.35) tied to how well that crop's model performed on held-out data during training.
- **Documented caveats travel with every prediction**, including an explicit statement (verified in the model card) that reported accuracy metrics were computed on a synthetic hold-out set calibrated to real regional averages, and that farm-level accuracy has not been independently validated. This is the kind of caveat that is easy to omit in a demo and important to keep, because overstating a secondary model's reliability is exactly the trust problem the whole system exists to avoid.

### 6.4 Process isolation

The model runs in a separate subprocess with a hard 15-second timeout, and no more than two such subprocesses run concurrently (enforced by a semaphore). This means a slow or crashing yield prediction can never block or take down the main recommendation API — a reasonable defensive engineering choice for a component whose output is, by design, optional annotation rather than a required part of the answer.

### 6.5 The one-way boundary

```
Ledger plan ──────────────► Yield estimate
                                 │
                                 ✗ blocked: never flows back into plan_kg_ha,
                                   Ledger confidence, or any plan revision
```

---

## 7. The full pipeline: eleven steps, in order

`RecommendationPipeline.run()` executes these steps in sequence for a full run; a partial replan (Section 8) runs only a relevant subset plus a fixed tail.

| # | Step | What happens | Can this step alone cause ABSTAIN? |
|---|---|---|---|
| 1 | `input_validation` | Confirms the field has an active crop, a recommendation type, and at least one soil test | Yes |
| 2 | `twin_update` | Applies any newly confirmed farmer input to the persistent digital twin | No |
| 3 | `soil` | Loads the latest soil test; flags it stale if older than 180 days | No (only adds a flag) |
| 4 | `crop` | Loads the crop, its calendar, resolves the dynamic growth stage | No |
| 5 | `weather` | Fetches (or reuses cached/mocked) forecast; evaluates the heavy-rain rule | No (falls back gracefully) |
| 6 | `ledger` | **The only step that computes a nutrient gap** | Yes, if the RDF row or soil data is missing |
| 7 | `optimizer` | Converts the gap into a product mix | No |
| 8 | `validation` | Runs the rule engine over the plan | Can block (HARD violations) |
| 9 | `knowledge` | Retrieves supporting evidence citations | No |
| 10 | `confidence` | De-duplicates flags, computes the final confidence rating, can trigger a late ABSTAIN | Yes |
| 11 | `persist` | Writes the proof-carrying object to the database and publishes an event | No |

Each step reads from and writes into a shared, typed state object (`TwinState`) that flows through the whole pipeline — soil, crop, weather, history, the current plan, accumulated flags, confidence, and retrieved evidence all live in one place, which is what makes it straightforward to reconstruct exactly why a given recommendation looked the way it did.

---

## 8. Continuous monitoring and event-driven replanning

### 8.1 The core differentiator

Most fertilizer recommenders stop at "here is your number." Kisan Saathi is built around a second, harder question: *what happens after the farmer has the first recommendation, and the world changes underneath it?* A plan is stored as the field's **active plan**. When a relevant condition changes, the system reacts on its own — nobody has to come back and ask it anything.

### 8.2 The mechanism

An event (e.g. a heavy-rain forecast, a newly confirmed soil report, a crop-stage change, a logged fertilizer application) is published on an event bus. A Monitoring Agent checks whether the event conflicts with the currently active plan; if it does, the old plan is marked **superseded**, and a **selective partial replan** runs — deliberately re-executing only the agents that the specific event could actually have affected, not the whole pipeline:

```
HEAVY_RAIN_ALERT          → re-run: weather, optimizer, validation
WEATHER_FORECAST_CHANGED  → re-run: weather, validation
SOIL_REPORT_UPDATED       → re-run: soil, ledger, optimizer, validation
CROP_STAGE_CHANGED        → re-run: crop, ledger, optimizer, validation
FERTILIZER_APPLIED        → re-run: ledger, optimizer, validation

Every partial replan always finishes with:  knowledge → confidence → persist
```

This selective design has a real efficiency justification, not just a tidiness one: a heavy-rain event doesn't change the soil chemistry, so there is no reason to re-run the Ledger and no reason to re-fetch a soil test — only the timing and validity of the *existing* plan needs re-checking.

### 8.3 What was actually observed live

Injecting a heavy-rain event against a live field produced exactly the documented behaviour: the previously active plan was marked invalidated, a partial replan executed only `weather → optimizer → validation → knowledge → confidence → persist`, the fertilizer quantities were **unchanged** (correctly — rain does not change the soil's nutrient chemistry), and the timing guidance changed to an explicit deferral instruction telling the user to recheck the local forecast before choosing an application date. An alert was recorded for follow-up.

### 8.4 An honest limitation

Nothing in the current system polls the outside world by itself. There is no background scheduler that periodically checks weather and raises events unprompted — events currently arrive through an explicit API call (`POST /events`), which in production would be wired to an actual scheduled weather-polling job or a webhook. The *reaction* to an event — invalidate, selectively replan, notify — is real and fully implemented; the *autonomous generation* of that first trigger, and delivery of a notification to a farmer's phone, are the next engineering steps, not yet built. This is worth stating plainly in any technical Q&A rather than implying a fully autonomous background loop already exists.

---

## 9. Rules, thresholds, and the honesty of "abstain"

### 9.1 The Rule Engine

Run by the Validation Agent after a plan exists, checking it against a set of agronomic constraints, each carrying a severity:

| Category | Example check | Severity |
|---|---|---|
| Maximum application rates | Applied nutrient meaningfully exceeds the RDF ceiling | Hard (blocks) or soft (warns), depending on the nutrient |
| Product compatibility | Urea and SSP mixed in the same application | Soft (warns) |
| Weather window | An active heavy-rain alert conflicts with the planned application timing | Hard (blocks the current window, triggers a deferral) |
| Soil pH window | pH outside roughly 5.5–8.0 | Soft (warns; nutrient availability drops outside this range) |
| Soil EC window | Electrical conductivity above 4 dS/m | Soft (warns of salinity stress) |
| Soil data freshness | Soil test older than 180 days | Soft (lowers confidence, does not block) |

A **HARD** violation blocks the plan from proceeding as-is (forcing a safer state, such as deferring the application window); a **SOFT** violation adds a flag and a warning but lets the plan through. All thresholds are loaded from a configuration module, not hard-coded inline — which is what makes it possible to say plainly, in an honest presentation, that some of these thresholds (pH window, EC limit, staleness cutoff, rain-alert trigger) are currently *engineering defaults* rather than every single one being individually sourced to a specific published guideline, while the RDF figures and FCO product percentages genuinely are sourced. Being precise about which numbers are sourced and which are reasonable engineering defaults is itself part of the trust story: the system does not claim more citation-backing than it has.

### 9.2 Confidence: assembled from flags, not asserted

Confidence is not a subjective label. It's computed from the accumulated list of flags raised anywhere in the pipeline:

```
Any flag containing "ABSTAIN"        →  confidence = ABSTAIN  (short-circuits everything else)
0 "material" flags remaining          →  HIGH
1 material flag                       →  MEDIUM
2 or more material flags              →  LOW
```

A small number of flags are deliberately excluded from this count because they are purely informational rather than a sign of numeric uncertainty — for instance, a flag simply noting which optimizer path was used, or a flag noting that weather coordinates weren't available (which already degrades the *timing* guidance on its own, without needing to double-penalize overall confidence).

### 9.3 Abstaining rather than guessing

At several points, the system will explicitly refuse to produce a number rather than estimate one without a defensible basis:

```json
{
  "status": "ABSTAIN",
  "reason": "No soil test found for this field (required for gap calculation).",
  "required_actions": ["Upload a recent soil test result for this field before requesting a recommendation."],
  "flags": ["NO_SOIL_TEST"]
}
```

This was verified live: requesting a recommendation for a field with no soil test returns a normal HTTP 200 response carrying this exact shape — a clear reason and a concrete next action, never a silent failure and never a guessed number. The same discipline applies to the yield model (Section 6.3) and to residual-credit accounting (Section 3.4): missing information produces an explicit "I don't know," not a plausible-looking placeholder.

---

## 10. Frontend, OCR, and the human-in-the-loop

### 10.1 Getting real data in: the Soil Health Card pipeline

Most Indian farmers hold their soil test as a paper Soil Health Card, sometimes photographed rather than scanned. The ingestion pipeline runs a **dual-pass extraction**: native PDF text extraction (`pypdf`) first, falling back to computer-vision OCR (`EasyOCR`) for scanned images or unreadable PDFs, followed by regex-based key-value parsing tuned to how Indian state labs typically lay out N, P, K, pH, organic carbon, and EC values.

Every extracted field gets a **per-field confidence score**. Anything below **0.85** — including any value an LLM had to guess at because the regex pass failed — is routed into a mandatory human review queue rather than being written straight into the field's active soil record. Nothing low-confidence auto-enters the digital twin. This threshold is the same one referenced in Section 2.3's discussion of the LLM's OCR-assist role: it is one mechanism serving two purposes — keeping bad optical-character-recognition out of the system, and keeping LLM-guessed values out of the system, using the identical gate.

### 10.2 The farmer-facing dashboard

Presents the recommendation as an "official" panel: clear fertilizer product cards (what and how much), a plain-language application window, a confidence badge, and the underlying reasoning available on demand. A text-to-speech feature reads the full advisory aloud in English, Hindi, or Marathi, aimed at lower-literacy users for whom a wall of text or numbers is itself a barrier to adoption.

### 10.3 What-If: sandboxed scenario exploration

Lets a farmer or agronomist explore hypotheticals — a different fertilizer percentage, a different expected rainfall, a shifted planting date — by re-running the full recommendation pipeline in an isolated sandbox. Two properties matter here: it is **non-persisted** (nothing from a what-if run overwrites the field's actual active plan), and it respects real agronomy rather than naive scaling — if a field's nutrient gap is genuinely zero because the soil is already sufficient, multiplying "zero fertilizer needed" by any percentage still correctly gives zero, rather than an artifact of blindly applying a multiplier to a number that shouldn't be scaled in the first place.

### 10.4 The Command Center: agronomist oversight

Extension officers and agronomists need a fleet view, not a single-field view: a table of every registered field with its current status, confidence level, and any active alerts, so a low-confidence or abstained field can be triaged quickly across many farms. When an agronomist's professional judgment genuinely needs to override the system — a local condition the Ledger has no way to know about — they can submit a documented override with a mandatory reason, which supersedes the prior plan on the farmer's dashboard while preserving the original recommendation in an auditable log, so nothing is silently overwritten or lost.

---

## 11. System architecture and technology stack

### 11.1 Layered design

```
Presentation      Next.js 16 (App Router), TypeScript, Tailwind — knows nothing about agronomy
       │           calls the API and renders whatever it returns
       ▼
API layer         FastAPI routes — validate requests, resolve the field, delegate
       ▼
Orchestration     RecommendationPipeline — sequences agents, owns one run's shared state
       ▼
Agents            Soil / Crop / Weather / Knowledge / Monitoring / Validation / Report —
                  each owns one narrow concern, none of them compute fertilizer quantities
       ▼
Core domain       Ledger, Optimizer, Rules, Proof assembly — deterministic, fully testable,
                  this is the only layer that is allowed to create a number
       ▼
Persistence       SQLite (default, zero-setup) or PostgreSQL — one abstraction, either backend
```

The direction of trust flows one way: only the core domain layer originates numbers, and every layer above it is purely a transport for numbers someone else computed. That is what makes the "no hallucinated dose" claim something you can actually audit, rather than something you have to take on faith — the set of files where a kilogram figure could originate is small and specific.

### 11.2 Technology choices and the reasoning behind them

| Concern | Choice | Reasoning |
|---|---|---|
| Backend | FastAPI on Python 3.12, Pydantic validation | Fast to build correctly, typed request/response contracts, easy to test with an in-process test client |
| Database | SQLite by default, PostgreSQL via one connection string | Zero-setup local development and demoing; a straightforward path to a managed cloud database without changing application code |
| Optimization | SciPy's `linprog` with the HiGHS solver | A mature, open-source, dependency-light linear-programming solver — no proprietary solver license needed |
| ML | XGBoost for yield, EasyOCR + PyTorch for OCR | Standard, well-understood tools for tabular regression and text recognition respectively |
| Retrieval | `rank_bm25` plus optional `sentence-transformers` + FAISS | Keyword search that always works, upgraded to semantic search when the extra dependencies are available |
| LLM | Groq or xAI via an OpenAI-compatible client | Swappable provider behind one interface; used only where Section 2 permits |
| Weather | Open-Meteo | Free, keyless, sufficient precipitation forecast data for the heavy-rain rule |
| Frontend | Next.js 16, React, Tailwind, Leaflet for maps | A modern, fast-to-iterate stack; Leaflet for field/geospatial display |
| Accessibility | Browser-native Web Speech API | Multilingual voice output with no server cost and no dependency on an internet connection for playback |

---

## 12. What was actually verified in this session

In the spirit of the system's own "abstain rather than guess" principle, here is exactly what was run and observed on `FINAL_V1` (commit `7e215c8`), versus what is documented but not independently re-verified here:

**Run and observed directly:**
- Full dependency install and a fresh database seed (37 districts, 27 talukas, 16 crop-calendar rows, 8 fields, 8 soil tests).
- The backend test suite: **163 passed, 1 failed, 1 skipped** out of 165 collected. The single failure is a dense-retrieval-specific test; it fails here only because the embedding model cannot be downloaded from Hugging Face inside this sandbox's network restrictions — the code path itself (attempt dense retrieval, catch the failure, log it, fall back to BM25-only) executed exactly as designed and was directly observed in the logs.
- A live recommendation call end to end: RDF lookup, unit conversion, gap computation, the default heuristic's product allocation, a rule-engine pass, confidence computed from flags, and citation retrieval all executed and produced a coherent, internally consistent result.
- The opt-in linear-programming optimizer, producing a near-identical plan to the heuristic for the same field.
- A live heavy-rain event injection producing exactly the documented closed loop: plan invalidation, a selective partial replan touching only the relevant agents, an unchanged fertilizer quantity, and an updated, explicitly deferral-worded timing instruction.
- A live ABSTAIN case: requesting a recommendation for a field with no soil test correctly returned a structured reason and a concrete required action rather than a guess or a server error.

**Documented in project materials, not independently re-run here:**
- Live Open-Meteo weather fetches in a network-unrestricted environment.
- The PostgreSQL database path (only SQLite was exercised in this session).
- Live Groq/xAI LLM calls (no API key configured in this sandbox).
- Full dense-vector retrieval end to end with the embedding model actually downloaded.

This section exists because the system's own design philosophy — say "I don't know" rather than imply more certainty than you have — is a reasonable standard to hold this document to as well.

---

## 13. Glossary

| Term | Meaning |
|---|---|
| **N, P, K** | Nitrogen, phosphorus, potassium — the three primary crop macronutrients |
| **P₂O₅ / K₂O** | The oxide forms of phosphorus and potassium used in dose recommendations and on fertilizer product labels |
| **RDF** | Recommended Dose of Fertilizer — a published, crop-specific season-total nutrient target |
| **Gap** | The shortfall the Ledger computes: required nutrient minus what the soil already supplies |
| **FCO** | Fertiliser Control Order — the legal specification of guaranteed nutrient percentages in each fertilizer product |
| **Ledger** | The deterministic module that is the sole legitimate source of any kg/ha figure in the system |
| **Heuristic optimizer** | The default DAP → Urea → MOP allocation rule |
| **LP optimizer** | The opt-in linear program that minimizes total product weight subject to meeting every nutrient gap |
| **RAG** | Retrieval-Augmented Generation — here, retrieving real document text as citable evidence, never as a source of numbers |
| **BM25** | A keyword-based text-ranking algorithm |
| **Dense retrieval** | Semantic search using vector embeddings and cosine similarity |
| **RRF** | Reciprocal Rank Fusion — a way to merge two differently-scaled ranked lists into one combined ranking |
| **Twin state** | The shared, typed object carrying soil, crop, weather, flags, and evidence through one pipeline run |
| **ABSTAIN** | An explicit, structured refusal to produce a recommendation when required information is missing, rather than a guess |
| **HITL** | Human-in-the-loop — a mandatory human confirmation step, used for low-confidence OCR extractions and for agronomist overrides |
