"""
AgroTwin AI — Agentic RAG Ingestion Module
==========================================
Implements doc 06_AGENTIC_RAG.md exactly.

Responsibilities:
  - Load trusted markdown documents from backend/rag/docs/
  - Parse YAML frontmatter into per-document metadata
  - Split each document into metadata-aware chunks (each chunk inherits metadata)
  - Build two indexes:
      1. Dense vector index (sentence-transformers + FAISS)
      2. BM25 sparse keyword index (rank_bm25)

Global constraints (00_CONTEXT.md):
  - Ingestion never calculates quantities.
  - Metadata must include region + crop for every chunk (enables hard filtering).
  - Chunks without region/crop are stored but flagged as unfiltered.
"""

from __future__ import annotations

import os
import re
import glob
import json
import pickle
from typing import Optional
import numpy as np

# --- Optional dense retrieval (graceful fallback if FAISS/sentence-transformers absent) ---
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    DENSE_AVAILABLE = True
except ImportError:
    DENSE_AVAILABLE = False

from rank_bm25 import BM25Okapi

# ── Paths ──────────────────────────────────────────────────────────────────────
DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")
STORE_DIR = os.path.join(os.path.dirname(__file__), "store")
DENSE_MODEL_NAME = "all-MiniLM-L6-v2"

# ── Chunk size ─────────────────────────────────────────────────────────────────
MIN_CHUNK_CHARS = 60   # discard trivially short paragraphs
MAX_CHUNK_CHARS = 1200  # split very long paragraphs to keep context tight

# ── Known metadata keys in YAML frontmatter ────────────────────────────────────
FRONTMATTER_KEYS = {
    "document_type", "issuing_authority", "publication_date",
    "region", "crops", "nutrients", "source",
}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _parse_frontmatter(content: str) -> tuple[dict, str]:
    """
    Extract YAML-like frontmatter delimited by --- lines.
    Returns (metadata_dict, remaining_body).
    Very lightweight — no full YAML parser dependency needed.
    """
    metadata: dict = {}
    if not content.startswith("---"):
        return metadata, content

    end = content.find("\n---", 3)
    if end == -1:
        return metadata, content

    fm_block = content[3:end].strip()
    body = content[end + 4:].strip()

    for line in fm_block.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, raw_val = line.partition(":")
        key = key.strip()
        raw_val = raw_val.strip()

        # Parse list values: [rice, sugarcane, soybean]
        if raw_val.startswith("[") and raw_val.endswith("]"):
            items = [v.strip() for v in raw_val[1:-1].split(",") if v.strip()]
            metadata[key] = items
        else:
            # Strip surrounding quotes
            metadata[key] = raw_val.strip('"\'')

    return metadata, body


def _extract_inline_metadata(paragraph: str) -> dict:
    """
    Extract inline metadata from a paragraph.
    Format used in sample docs:
        **crop**: rice
        **region**: kolhapur
        **crop_stage**: tillering
        **nutrient**: N
    Returns a dict of found keys.
    """
    inline: dict = {}
    pattern = re.compile(r"\*\*(\w+)\*\*:\s*([^\n]+)")
    for match in pattern.finditer(paragraph):
        key = match.group(1).strip()
        val = match.group(2).strip()
        # Normalise list-like values
        if "," in val:
            inline[key] = [v.strip() for v in val.split(",")]
        else:
            inline[key] = val
    return inline


def _split_into_paragraphs(text: str) -> list[str]:
    """Split body by double newlines; handle markdown sections sensibly."""
    raw = re.split(r"\n{2,}", text)
    chunks = []
    for para in raw:
        para = para.strip()
        if len(para) < MIN_CHUNK_CHARS:
            continue
        if len(para) <= MAX_CHUNK_CHARS:
            chunks.append(para)
        else:
            # Split long paragraph at sentence boundaries
            sentences = re.split(r"(?<=[.!?])\s+", para)
            current = ""
            for sent in sentences:
                if len(current) + len(sent) + 1 > MAX_CHUNK_CHARS and current:
                    if len(current) >= MIN_CHUNK_CHARS:
                        chunks.append(current.strip())
                    current = sent
                else:
                    current = (current + " " + sent).strip()
            if len(current) >= MIN_CHUNK_CHARS:
                chunks.append(current.strip())
    return chunks


def _normalise_list_field(val) -> list[str]:
    """Ensure a metadata field that can be str or list becomes a lowercase list."""
    if isinstance(val, list):
        return [v.lower() for v in val]
    if isinstance(val, str):
        return [val.lower()]
    return []


# ─────────────────────────────────────────────────────────────────────────────
# ChunkStore — holds all ingested chunks with metadata
# ─────────────────────────────────────────────────────────────────────────────

class ChunkStore:
    """
    In-memory list of dicts, each representing one chunk.
    Schema per chunk (matches doc 06 Chunk Metadata Schema):
        {
            "text": str,
            "metadata": {
                "crop": list[str],        # ["rice"] or ["banana", "cotton"]
                "crop_stage": str | None,
                "region": list[str],      # ["kolhapur"]
                "soil_type": str | None,
                "nutrient": list[str],
                "document_type": str,
                "issuing_authority": str,
                "publication_date": str,
                "source": str,
                "page": int,             # paragraph ordinal within document
            },
            "citation": str,             # "source_file.md#para-N"
        }
    """

    def __init__(self):
        self.chunks: list[dict] = []

    def add(self, text: str, metadata: dict, citation: str):
        self.chunks.append({
            "text": text,
            "metadata": metadata,
            "citation": citation,
        })

    def __len__(self):
        return len(self.chunks)


# ─────────────────────────────────────────────────────────────────────────────
# Ingestion
# ─────────────────────────────────────────────────────────────────────────────

def ingest_documents(docs_dir: str = DOCS_DIR) -> ChunkStore:
    """
    Load all .md files from docs_dir, chunk them with metadata, return ChunkStore.
    """
    store = ChunkStore()
    md_files = glob.glob(os.path.join(docs_dir, "**", "*.md"), recursive=True)

    if not md_files:
        print(f"[Ingestion] WARNING: No markdown files found in {docs_dir}")
        return store

    for filepath in sorted(md_files):
        filename = os.path.basename(filepath)
        try:
            with open(filepath, "r", encoding="utf-8") as fh:
                raw = fh.read()
        except Exception as exc:
            print(f"[Ingestion] ERROR reading {filepath}: {exc}")
            continue

        doc_meta, body = _parse_frontmatter(raw)

        # Normalise doc-level crop + region lists
        doc_crops  = _normalise_list_field(doc_meta.get("crops", []))
        doc_regions = _normalise_list_field(doc_meta.get("region", []))

        paragraphs = _split_into_paragraphs(body)

        for para_idx, para_text in enumerate(paragraphs):
            inline_meta = _extract_inline_metadata(para_text)

            # Merge: inline overrides doc-level for crop/region/stage
            para_crop = _normalise_list_field(
                inline_meta.get("crop", doc_crops or [])
            )
            para_region = _normalise_list_field(
                inline_meta.get("region", doc_regions or [])
            )
            para_stage = inline_meta.get("crop_stage") or None
            para_soil = inline_meta.get("soil_type") or doc_meta.get("soil_type") or None
            para_nutrient = _normalise_list_field(
                inline_meta.get("nutrient", doc_meta.get("nutrients", []))
            )

            meta = {
                "crop": para_crop,
                "crop_stage": para_stage,
                "region": para_region,
                "soil_type": para_soil,
                "nutrient": para_nutrient,
                "document_type": inline_meta.get("document_type",
                                                  doc_meta.get("document_type", "unknown")),
                "issuing_authority": doc_meta.get("issuing_authority", "unknown"),
                "publication_date": doc_meta.get("publication_date", "unknown"),
                "source": doc_meta.get("source", filename),
                "page": para_idx + 1,
            }

            citation = f"{doc_meta.get('source', filename)}#para-{para_idx + 1}"
            store.add(text=para_text, metadata=meta, citation=citation)

    print(f"[Ingestion] Loaded {len(store)} chunks from {len(md_files)} documents.")
    return store


# ─────────────────────────────────────────────────────────────────────────────
# Index — wraps BM25 and optionally FAISS
# ─────────────────────────────────────────────────────────────────────────────

class HybridIndex:
    """
    Builds and holds BM25 + (optionally) a FAISS dense index over a ChunkStore.

    Usage:
        idx = HybridIndex(store)
        idx.build()
        results = idx.query(query_text, top_k=5, filters={"region": "kolhapur", "crop": "rice"})
    """

    def __init__(self, store: ChunkStore, dense_model: str = DENSE_MODEL_NAME):
        self.store = store
        self.dense_model_name = dense_model
        self._bm25: Optional[BM25Okapi] = None
        self._faiss_index = None
        self._embedder = None
        self._embeddings: Optional[np.ndarray] = None
        self._built = False

    # ── Build ─────────────────────────────────────────────────────────────────

    def build(self) -> None:
        if self._built:
            return
        if len(self.store) == 0:
            print("[HybridIndex] WARNING: Empty store — nothing to index.")
            self._built = True
            return

        texts = [c["text"] for c in self.store.chunks]

        # BM25
        tokenized = [t.lower().split() for t in texts]
        self._bm25 = BM25Okapi(tokenized)

        # Dense (optional)
        if DENSE_AVAILABLE:
            try:
                self._embedder = SentenceTransformer(self.dense_model_name)
                self._embeddings = self._embedder.encode(
                    texts, convert_to_numpy=True, show_progress_bar=False
                ).astype("float32")
                faiss.normalize_L2(self._embeddings)
                dim = self._embeddings.shape[1]
                self._faiss_index = faiss.IndexFlatIP(dim)
                self._faiss_index.add(self._embeddings)
                print(f"[HybridIndex] Dense index built: {dim}d, {len(texts)} vectors.")
            except Exception as exc:
                print(f"[HybridIndex] Dense index failed — BM25-only mode. Reason: {exc}")
                DENSE_AVAILABLE_local = False

        self._built = True
        print(f"[HybridIndex] BM25 index built over {len(texts)} chunks.")

    # ── Metadata filter ───────────────────────────────────────────────────────

    def _matches_filters(self, chunk: dict, filters: dict) -> bool:
        """
        Hard filter: chunk must satisfy ALL provided filter keys.
        For list-valued metadata (crop, region), at least ONE item must match.
        """
        meta = chunk["metadata"]
        for key, value in filters.items():
            if value is None:
                continue
            meta_val = meta.get(key)
            if meta_val is None:
                return False
            # Normalise filter value
            filter_val = value.lower() if isinstance(value, str) else str(value).lower()
            if isinstance(meta_val, list):
                if not any(filter_val == mv.lower() for mv in meta_val):
                    return False
            else:
                if filter_val not in str(meta_val).lower():
                    return False
        return True

    # ── BM25 retrieval ────────────────────────────────────────────────────────

    def _bm25_scores(self, query: str) -> np.ndarray:
        if self._bm25 is None:
            return np.zeros(len(self.store.chunks))
        tokenized = query.lower().split()
        scores = self._bm25.get_scores(tokenized)
        return np.array(scores, dtype="float32")

    # ── Dense retrieval ───────────────────────────────────────────────────────

    def _dense_scores(self, query: str) -> Optional[np.ndarray]:
        if self._faiss_index is None or self._embedder is None:
            return None
        q_vec = self._embedder.encode([query], convert_to_numpy=True).astype("float32")
        faiss.normalize_L2(q_vec)
        scores, indices = self._faiss_index.search(q_vec, len(self.store.chunks))
        # Rebuild scores in chunk order
        ordered = np.zeros(len(self.store.chunks), dtype="float32")
        for rank, idx in enumerate(indices[0]):
            ordered[idx] = scores[0][rank]
        return ordered

    # ── Reciprocal Rank Fusion ────────────────────────────────────────────────

    @staticmethod
    def _rrf(rank_lists: list[list[int]], k: int = 60) -> dict[int, float]:
        """
        Standard RRF formula: score(d) = sum( 1 / (k + rank(d)) )
        rank_lists: list of ranked index lists (most relevant first)
        """
        scores: dict[int, float] = {}
        for ranked in rank_lists:
            for rank, doc_idx in enumerate(ranked):
                scores[doc_idx] = scores.get(doc_idx, 0.0) + 1.0 / (k + rank + 1)
        return scores

    # ── Main query interface ──────────────────────────────────────────────────

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        filters: Optional[dict] = None,
    ) -> list[dict]:
        """
        Hybrid retrieval with metadata hard-filtering.

        Args:
            query_text: Natural language query.
            top_k: Number of chunks to return.
            filters: Dict of metadata constraints, e.g.:
                     {"region": "kolhapur", "crop": "rice", "crop_stage": "tillering"}
                     All filters are AND-ed; crop and region are matched against lists.

        Returns:
            List of result dicts, sorted by descending RRF score:
            [{"text", "metadata", "citation", "score"}, ...]
        """
        self.build()  # no-op if already built

        if not self.store.chunks:
            return []

        filters = filters or {}

        # 1. Get candidate set (apply hard filters first)
        candidate_indices = [
            i for i, c in enumerate(self.store.chunks)
            if self._matches_filters(c, filters)
        ]

        if not candidate_indices:
            return []

        # 2. BM25 scores over candidates
        all_bm25 = self._bm25_scores(query_text)
        bm25_candidates = sorted(candidate_indices,
                                  key=lambda i: all_bm25[i], reverse=True)

        # 3. Dense scores over candidates (if available)
        all_dense = self._dense_scores(query_text)
        if all_dense is not None:
            dense_candidates = sorted(candidate_indices,
                                       key=lambda i: all_dense[i], reverse=True)
            rank_lists = [bm25_candidates, dense_candidates]
        else:
            rank_lists = [bm25_candidates]

        # 4. RRF fusion
        rrf_scores = self._rrf(rank_lists)

        # 5. Top-k by RRF score
        top_indices = sorted(rrf_scores.keys(),
                              key=lambda i: rrf_scores[i], reverse=True)[:top_k]

        results = []
        for idx in top_indices:
            chunk = self.store.chunks[idx]
            results.append({
                "text": chunk["text"],
                "metadata": chunk["metadata"],
                "citation": chunk["citation"],
                "score": round(rrf_scores[idx], 6),
            })

        return results

    # ── Persistence (optional, for large corpora) ─────────────────────────────

    def save(self, path: str = STORE_DIR) -> None:
        os.makedirs(path, exist_ok=True)
        with open(os.path.join(path, "chunks.pkl"), "wb") as fh:
            pickle.dump(self.store.chunks, fh)
        if self._faiss_index is not None:
            faiss.write_index(self._faiss_index, os.path.join(path, "faiss.index"))
        if self._embeddings is not None:
            np.save(os.path.join(path, "embeddings.npy"), self._embeddings)
        print(f"[HybridIndex] Saved to {path}")

    @classmethod
    def load(cls, path: str = STORE_DIR, dense_model: str = DENSE_MODEL_NAME) -> "HybridIndex":
        chunks_path = os.path.join(path, "chunks.pkl")
        if not os.path.exists(chunks_path):
            raise FileNotFoundError(f"No saved index at {path}")
        with open(chunks_path, "rb") as fh:
            chunks = pickle.load(fh)
        store = ChunkStore()
        store.chunks = chunks
        instance = cls(store, dense_model)

        # Rebuild BM25 (fast, no GPU)
        texts = [c["text"] for c in chunks]
        tokenized = [t.lower().split() for t in texts]
        instance._bm25 = BM25Okapi(tokenized)

        # Load FAISS if available
        faiss_path = os.path.join(path, "faiss.index")
        emb_path   = os.path.join(path, "embeddings.npy")
        if DENSE_AVAILABLE and os.path.exists(faiss_path) and os.path.exists(emb_path):
            instance._faiss_index = faiss.read_index(faiss_path)
            instance._embeddings  = np.load(emb_path)
            instance._embedder    = SentenceTransformer(dense_model)

        instance._built = True
        print(f"[HybridIndex] Loaded {len(chunks)} chunks from {path}")
        return instance
