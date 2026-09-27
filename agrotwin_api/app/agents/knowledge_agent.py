"""
Knowledge Agent (Agentic RAG) — fetches evidence from the trusted agricultural docs.

Responsibility:
  - Read local trusted markdown documents from rag/docs/ (MPKV/ICAR RDF, FCO specs, Crop Calendars).
  - Uses HybridIndex (BM25 sparse retrieval + optional dense vector retrieval via FAISS).
  - Applies metadata filters (region, crop, nutrient).
  - Surfaces relevant excerpts and citations for a crop/region query.

Crucial Scope Rule:
  This agent ONLY returns TEXT EVIDENCE. It NEVER generates fertilizer quantities.
  All numbers come from ledger.py / the optimizer / the rule engine.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Any, Optional

# Try local rag package first, then backend.rag
try:
    from ...rag.ingestion import ingest_documents, HybridIndex, DOCS_DIR
except (ImportError, ValueError):
    try:
        from rag.ingestion import ingest_documents, HybridIndex, DOCS_DIR
    except (ImportError, ValueError):
        from backend.rag.ingestion import ingest_documents, HybridIndex, DOCS_DIR


@dataclass
class EvidenceChunk:
    text: str
    metadata: dict
    score: float
    citation: str


@dataclass
class EvidencePack:
    query: str
    chunks: list[EvidenceChunk]
    applicability_notes: str
    confidence: str  # "HIGH" | "MEDIUM" | "LOW" | "NO_EVIDENCE"
    flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "chunks": [
                {
                    "text": c.text,
                    "metadata": c.metadata,
                    "score": c.score,
                    "citation": c.citation,
                }
                for c in self.chunks
            ],
            "applicability_notes": self.applicability_notes,
            "confidence": self.confidence,
            "flags": self.flags,
        }

    def is_empty(self) -> bool:
        return len(self.chunks) == 0


_index: Optional[HybridIndex] = None


def _get_index() -> HybridIndex:
    global _index
    if _index is None:
        store = ingest_documents(DOCS_DIR)
        _index = HybridIndex(store)
        _index.build()
    return _index


def reset_index() -> None:
    """Forces the index to rebuild on next query."""
    global _index
    _index = None


def _build_query(
    crop: Optional[str],
    region: Optional[str],
    recommendation_type: Optional[str],
    extra_query: str,
) -> str:
    parts: list[str] = []
    if recommendation_type:
        parts.append(f"{recommendation_type.replace('_', ' ')} fertilizer recommendation")
    else:
        parts.append("Fertilizer recommendation")

    if crop:
        parts.append(f"for {crop}")
    if region:
        parts.append(f"in {region} region")
    if extra_query:
        parts.append(extra_query)
    return " ".join(parts).strip()


def retrieve_evidence(
    crop_code: str | None = None,
    region: str | None = None,
    recommendation_type: str | None = None,
    extra_query: str = "",
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """
    Constructs search query and retrieves evidence chunks from the trusted documents.
    Returns list of dicts with source_file, excerpt, score, citation, metadata.
    """
    if not crop_code and not region and not recommendation_type and not extra_query:
        return [{"source_file": "NONE", "excerpt": "Empty query context.", "score": 0.0}]

    query_str = _build_query(crop_code, region, recommendation_type, extra_query)
    if not query_str:
        return [{"source_file": "NONE", "excerpt": "Empty query context.", "score": 0.0}]

    filters: dict[str, str] = {}
    if region:
        filters["region"] = region.lower().strip()
    if crop_code:
        filters["crop"] = crop_code.lower().strip()

    try:
        idx = _get_index()
        raw_chunks = idx.query(query_str, top_k=top_k, filters=filters)
        # If strict filter returned nothing, retry without strict filters
        if not raw_chunks and filters:
            raw_chunks = idx.query(query_str, top_k=top_k, filters={})
    except Exception as exc:
        return [{"source_file": "RAG_ERROR", "excerpt": f"Retrieval error: {exc}", "score": 0.0}]

    if not raw_chunks:
        return [{"source_file": "NONE", "excerpt": "No relevant evidence found for query.", "score": 0.0}]

    results = []
    for c in raw_chunks:
        text = c.get("text", "")
        excerpt = text[:300] + "..." if len(text) > 300 else text
        citation = c.get("citation") or (c.get("metadata", {}).get("source") or "mpkv_icar_rdf.md")
        meta = dict(c.get("metadata", {}))
        score = round(float(c.get("score", 0.0)), 3)
        meta["score"] = score
        results.append({
            "source_file": citation,
            "excerpt": excerpt,
            "content": excerpt,
            "confidence": "HIGH" if score > 0 else "MEDIUM",
            "score": score,
            "citation": citation,
            "metadata": meta,
        })

    return results


def retrieve_evidence_pack(
    crop: Optional[str] = None,
    region: Optional[str] = None,
    crop_stage: Optional[str] = None,
    nutrient: Optional[str] = None,
    extra_query: str = "",
    top_k: int = 5,
) -> EvidencePack:
    """Full EvidencePack retrieval compatible with backend/app/agents/knowledge_agent.py."""
    query = _build_query(crop, region, crop_stage, extra_query)
    chunks_dicts = retrieve_evidence(crop, region, crop_stage, extra_query=extra_query, top_k=top_k)

    chunks: list[EvidenceChunk] = []
    for cd in chunks_dicts:
        if cd["source_file"] in ("NONE", "RAG_ERROR"):
            continue
        chunks.append(
            EvidenceChunk(
                text=cd.get("excerpt", ""),
                metadata=cd.get("metadata", {}),
                score=cd.get("score", 0.0),
                citation=cd.get("citation", cd.get("source_file", "")),
            )
        )

    confidence = "HIGH" if len(chunks) >= 3 else ("MEDIUM" if len(chunks) >= 1 else "NO_EVIDENCE")
    return EvidencePack(
        query=query,
        chunks=chunks,
        applicability_notes="Evidence retrieved from curated MPKV/ICAR and FCO specifications.",
        confidence=confidence,
        flags=[] if confidence != "NO_EVIDENCE" else ["NO_EVIDENCE"],
    )
