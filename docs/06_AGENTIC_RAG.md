# 06 — Agentic RAG Design

## Role of RAG

RAG is the **knowledge and evidence layer only**.  
It never calculates fertilizer quantities.  
It never invents agronomic thresholds.

---

## Pipeline

```
Trusted Agricultural Documents
        ↓
Ingestion → Document normalization → Metadata-aware chunking
                │
    ┌───────────┴───────────┐
    ▼                       ▼
Dense Embeddings         BM25
    ▼                       ▼
Vector Store          Keyword Index
    └───────────┬───────────┘
                ▼
               RRF (Reciprocal Rank Fusion)
                ▼
        Cross-Encoder Reranker (optional for MVP)
                ▼
          Evidence Pack
                ▼
        Knowledge Agent
                ▼
        Validation Agent
```

---

## Chunk Metadata Schema (mandatory)

```json
{
  "crop": "rice",
  "crop_stage": "tillering",
  "region": "kolhapur",
  "soil_type": "black",
  "nutrient": "N",
  "document_type": "rdf",
  "issuing_authority": "MPKV",
  "publication_date": "2022",
  "source": "mpkv_icar_rdf.md",
  "page": 12
}
```

A recommendation for one crop/region must **never** retrieve guidance meant for another.  
Filter hard on `region` + `crop` (and preferably `crop_stage`) at retrieval time.

---

## Implementation (Hackathon Feasible)

1. Start with a small curated set of trusted PDFs / markdown (MPKV, ICAR, FCO, local university guidance).
2. Use `sentence-transformers` (e.g. `all-MiniLM-L6-v2`) + FAISS or Chroma for dense retrieval.
3. Add BM25 (`rank_bm25`).
4. Reciprocal Rank Fusion → top-k.
5. Optional: cross-encoder reranker (`ms-marco-MiniLM`).
6. Knowledge Agent packages the evidence with citations and returns a structured `EvidencePack`.

### Suggested libraries

```
sentence-transformers
rank_bm25
faiss-cpu          # or chromadb
# optional: langchain for orchestration only
```

---

## Query Construction

The Knowledge Agent builds a precise query from the current plan + twin:

```
"Recommended nitrogen application for rice at tillering stage in Kolhapur region on low-N soil"
```

Plus hard metadata filters:
- `region = kolhapur`
- `crop = rice`
- `crop_stage = tillering` (if available)
- `nutrient = N`

---

## EvidencePack Contract

```python
{
  "query": "...",
  "chunks": [
    {
      "text": "...",
      "metadata": {...},
      "score": 0.87,
      "citation": "mpkv_icar_rdf.md#page-12"
    }
  ],
  "applicability_notes": "All chunks match region and crop"
}
```

---

## Checklist

- [x] Ingestion script that writes chunks + metadata into vector store.
      → `backend/rag/ingestion.py` — `ingest_documents()` + `HybridIndex`
- [x] Hybrid retriever (dense + BM25 + RRF).
      → `HybridIndex.query()` — BM25 (rank_bm25) + optional FAISS dense + Reciprocal Rank Fusion
- [x] Knowledge Agent returns structured EvidencePack with citations.
      → `backend/app/agents/knowledge_agent.py` — `retrieve_evidence()` → `EvidencePack`
- [x] Validation Agent checks that retrieved evidence is applicable (region/crop match).
      → `backend/app/agents/rag_validation_agent.py` — `validate_evidence_pack()`
- [x] No numeric extraction from LLM — only text evidence.
      → Enforced in scope: Knowledge Agent returns text chunks only; quantities never generated.
- [x] Clear fallback when no relevant evidence is found (still allow plan if confidence is otherwise acceptable, but lower confidence / flag it).
      → `NO_EVIDENCE` confidence tier + `RAG_NO_EVIDENCE` flag; ledger plan is never blocked.

**Tests**: `backend/tests/test_rag.py` — 38/38 passed ✅ (verified 2026-09-27)
