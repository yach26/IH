# AgroTwin AI — Agentic RAG Layer

> **PR**: `feat: agentic RAG with hybrid retrieval and Knowledge Agent`
> **Implements**: `docs/06_AGENTIC_RAG.md` — constrained by `docs/00_CONTEXT.md`

---

## What This PR Does

Implements the **Agentic RAG (Retrieval-Augmented Generation) layer** of AgroTwin AI — the knowledge and evidence layer that answers *WHY* and *BASED ON WHAT* in every fertilizer recommendation.

### Strict Scope (non-negotiable per 00_CONTEXT.md)

| ✅ This layer DOES | ❌ This layer NEVER does |
|---|---|
| Returns text evidence from trusted documents | Generates fertilizer quantities (kg/ha) |
| Cites source documents with page/para refs | Invents agronomic thresholds |
| Hard-filters on region + crop | Replaces the Ledger or Optimizer |
| Returns structured `EvidencePack` | Extracts numbers for application |
| Degrades gracefully when no evidence found | Makes up evidence |

---

## Architecture

```
Trusted Agricultural Documents (backend/rag/docs/)
        ↓
Ingestion (ingestion.py)
  → YAML frontmatter metadata
  → Inline metadata parsing (**crop**: rice)
  → Metadata-aware chunking
        ↓
    ┌───────────────────────┐
    ▼                       ▼
Dense Embeddings         BM25 (rank_bm25)
(sentence-transformers)  Keyword Index
    ▼                       ▼
FAISS Vector Store    Sparse Scores
    └───────────┬───────────┘
                ▼
            RRF Fusion
     (Reciprocal Rank Fusion)
                ↓
     Hard Metadata Filtering
       (region + crop MUST match)
                ↓
         EvidencePack
                ↓
       Knowledge Agent  →  RAG Validation Agent
```

---

## File Structure

```
backend/
├── __init__.py
├── requirements.txt
├── rag/
│   ├── __init__.py
│   ├── ingestion.py          # Ingestion + HybridIndex (BM25 + FAISS + RRF)
│   └── docs/                 # Trusted source documents
│       ├── mpkv_icar_rdf.md  # MPKV-ICAR RDF — Kolhapur (rice, sugarcane, soybean, wheat)
│       ├── jalgaon_rdf.md    # MPKV-ICAR RDF — Jalgaon (banana, cotton, maize, onion)
│       ├── fco_fertilizer_spec.md  # FCO legal NPK specifications
│       └── crop_calendars.md # ICAR crop growth calendars — Maharashtra
├── app/
│   ├── __init__.py
│   └── agents/
│       ├── __init__.py
│       ├── knowledge_agent.py      # EvidencePack producer
│       └── rag_validation_agent.py # RAG applicability validator
└── tests/
    ├── __init__.py
    └── test_rag.py           # 30+ unit tests across 6 test suites
```

---

## Installation

```bash
cd backend
pip install -r requirements.txt
```

**Minimum (BM25-only mode)**:
```bash
pip install rank-bm25 numpy
```

**Full hybrid (recommended)**:
```bash
pip install rank-bm25 sentence-transformers faiss-cpu numpy
```

If `sentence-transformers` or `faiss-cpu` are not installed, the system **automatically falls back to BM25-only** mode — no code changes needed.

---

## Running the Tests

```bash
# From project root (IH/)
cd IH
python -m pytest backend/tests/test_rag.py -v
```

Or run directly:
```bash
python backend/tests/test_rag.py
```

Expected output (BM25-only mode, no GPU):
```
TestIngestion::test_chunks_are_created ... ok
TestIngestion::test_rice_chunks_have_region ... ok
TestIngestion::test_banana_chunks_have_region ... ok
TestIngestion::test_tillering_stage_parsed ... ok
TestIngestion::test_frontmatter_parsed ... ok
TestIngestion::test_citation_format ... ok
TestIngestion::test_no_documents_returns_empty_store ... ok
TestMetadataParsing::test_frontmatter_basic ... ok
TestMetadataParsing::test_inline_metadata_extracted ... ok
...
Ran 30 tests in ~2s — OK
```

---

## Using the Knowledge Agent

```python
from backend.app.agents.knowledge_agent import retrieve_evidence

# Query for rice at tillering stage in Kolhapur
pack = retrieve_evidence(
    crop="rice",
    region="kolhapur",
    crop_stage="tillering",
    nutrient="N",
    top_k=5,
)

print(pack.query)
# → "Recommended N application for rice at tillering stage in kolhapur region"

print(pack.confidence)       # "HIGH" | "MEDIUM" | "LOW" | "NO_EVIDENCE"
print(pack.applicability_notes)

for chunk in pack.chunks:
    print(chunk.citation)    # "mpkv_icar_rdf.md#para-7"
    print(chunk.score)       # RRF score
    print(chunk.text[:200])  # Evidence text (from trusted source)

# Serialise to dict (for API response)
import json
print(json.dumps(pack.to_dict(), indent=2))
```

### EvidencePack Schema

```json
{
  "query": "Recommended N application for rice at tillering stage in kolhapur region",
  "chunks": [
    {
      "text": "At the tillering stage (21-28 DAT), apply the second split of nitrogen...",
      "metadata": {
        "crop": ["rice"],
        "crop_stage": "tillering",
        "region": ["kolhapur"],
        "nutrient": ["n"],
        "document_type": "rdf",
        "issuing_authority": "MPKV-ICAR",
        "publication_date": "2022",
        "source": "mpkv_icar_rdf.md",
        "page": 7
      },
      "score": 0.032258,
      "citation": "mpkv_icar_rdf.md#para-7"
    }
  ],
  "applicability_notes": "All chunks match required region and crop.",
  "confidence": "HIGH",
  "flags": []
}
```

---

## Validating Evidence Applicability

```python
from backend.app.agents.rag_validation_agent import validate_evidence_pack

result = validate_evidence_pack(
    evidence=pack,
    required_crop="rice",
    required_region="kolhapur",
    required_crop_stage="tillering",
)

print(result.is_applicable)          # True
print(result.confidence_adjustment)  # "NONE" | "DOWNGRADE" | "SEVERE_DOWNGRADE"
print(result.flags_added)            # [] or ["REGION_MISMATCH", ...]
```

---

## Adding New Documents

1. **Create a new markdown file** in `backend/rag/docs/`:

```markdown
---
document_type: rdf
issuing_authority: MPKV-ICAR
publication_date: "2023"
region: kolhapur
crops: [tomato, chilli]
nutrients: [N, P, K]
source: kolhapur_horticulture_rdf.md
---

# Horticulture Crops — Kolhapur RDF

## Tomato Basal Dose

**crop**: tomato
**region**: kolhapur
**crop_stage**: transplanting
**nutrient**: N

For tomato in Kolhapur, apply 120 kg N/ha, 60 kg P2O5/ha, 80 kg K2O/ha total seasonal dose...
```

2. **Mandatory metadata fields** (per `06_AGENTIC_RAG.md`):
   - `region` — must match pilot regions (kolhapur / jalgaon) or `all`
   - `crops` — list of crop names this document covers
   - `issuing_authority` — trusted: `MPKV-ICAR`, `ICAR`, `FCO-India`
   - `source` — filename for citation

3. **Inline metadata** — add `**crop**: xyz` etc. at section level for precision.

4. **Reset index** after adding documents:
```python
from backend.app.agents.knowledge_agent import reset_index
reset_index()  # forces rebuild on next call
```

5. **Verify** with a quick retrieval test:
```bash
python -c "
from backend.app.agents.knowledge_agent import retrieve_evidence
pack = retrieve_evidence(crop='tomato', region='kolhapur')
print(f'Chunks: {len(pack.chunks)}, Confidence: {pack.confidence}')
"
```

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| BM25 + Dense + RRF | RRF beats score fusion empirically; both retrievers complement each other |
| Hard region+crop filter | Doc 06 mandate — cross-region evidence is never acceptable |
| Graceful NO_EVIDENCE | Plan can still proceed from ledger; RAG absence lowers confidence only |
| Inline `**crop**: rice` metadata | Allows paragraph-level precision without a full NLP pipeline |
| YAML frontmatter | Standard, readable, no external dependency for parsing |
| Singleton index | Built once per process; `reset_index()` for test isolation |

---

## Checklist (doc 06_AGENTIC_RAG.md)

- [x] Ingestion script that writes chunks + metadata into vector store
- [x] Hybrid retriever (dense + BM25 + RRF)
- [x] Knowledge Agent returns structured EvidencePack with citations
- [x] Validation Agent checks that retrieved evidence is applicable (region/crop match)
- [x] No numeric extraction from LLM — only text evidence
- [x] Clear fallback when no relevant evidence is found (NO_EVIDENCE confidence, plan not blocked)
- [x] Unit tests for retrieval and metadata filtering

---

*Maintainer: Team AgroTwin | yach26/IH*
