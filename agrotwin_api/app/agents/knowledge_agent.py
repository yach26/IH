"""
Knowledge Agent (Agentic RAG) — fetches evidence from the Phase-1 Data Pack.

Responsibility:
  - Read local markdown documents from the data pack.
  - Chunk them into paragraphs.
  - Index them using BM25 (sparse retrieval, lightweight, no GPU required).
  - Surface top_k excerpts relevant to a crop/region query.

Crucial Scope Rule:
  This agent ONLY returns TEXT EVIDENCE. It NEVER generates fertilizer quantities.
  All numbers come from app/ledger.py (the MPKV/ICAR exact match module)
  or the Optimizer. This RAG simply surfaces the qualitative why/how
  (e.g., "apply 50% urea at planting").

Dependencies: rank-bm25
Data Pack Location: ../AgroTwin_Phase1_Data
"""

import os
import glob
from rank_bm25 import BM25Okapi

# We look up one level to find the data pack, as it is outside the API folder.
DATA_PACK_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "AgroTwin_Phase1_Data")
)
# Note: since the script may be run from various places, finding the data pack
# exactly can be fragile. We also allow it to be parallel to agrotwin_api.
if not os.path.exists(DATA_PACK_DIR):
    DATA_PACK_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "AgroTwin_Phase1_Data")
    )


class BM25Index:
    def __init__(self):
        self.chunks = []
        self.corpus_tokens = []
        self.bm25 = None
        self._is_built = False

    def build_index(self):
        if self._is_built:
            return

        if not os.path.exists(DATA_PACK_DIR):
            print(f"Knowledge Agent WARNING: Data pack not found at {DATA_PACK_DIR}")
            self._is_built = True
            return

        # Find all markdown files in the data pack
        md_files = glob.glob(os.path.join(DATA_PACK_DIR, "**", "*.md"), recursive=True)

        for file_path in md_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue

            # Naive chunking by paragraph (double newline)
            paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 30]

            filename = os.path.basename(file_path)
            for p in paragraphs:
                self.chunks.append({
                    "source_file": filename,
                    "text": p
                })
                # simple tokenization (lower + split)
                self.corpus_tokens.append(p.lower().split())

        if self.corpus_tokens:
            self.bm25 = BM25Okapi(self.corpus_tokens)

        self._is_built = True

    def retrieve(self, query: str, top_k: int = 3) -> list[dict]:
        self.build_index()
        if not self.bm25:
            return [{"source_file": "MISSING", "excerpt": "No documents indexed.", "score": 0.0}]

        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)

        # get top_k indices
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results = []
        for i in top_indices:
            if scores[i] > 0.0:  # only include if there is some match
                results.append({
                    "source_file": self.chunks[i]["source_file"],
                    "excerpt": self.chunks[i]["text"][:300] + "..." if len(self.chunks[i]["text"]) > 300 else self.chunks[i]["text"],
                    "score": round(float(scores[i]), 2)
                })

        if not results:
            return [{"source_file": "NONE", "excerpt": "No relevant evidence found for query.", "score": 0.0}]
        return results


# Global singleton instance
_index = BM25Index()


def retrieve_evidence(
    crop_code: str | None,
    region: str | None,
    recommendation_type: str | None,
    extra_query: str = "",
    top_k: int = 3,
) -> list[dict]:
    """
    Constructs a search query from the context and retrieves evidence.
    """
    parts = []
    if crop_code:
        parts.append(crop_code)
    if region:
        parts.append(region)
    if recommendation_type:
        parts.append(recommendation_type)
    if extra_query:
        parts.append(extra_query)

    query = " ".join(parts)
    if not query:
        return [{"source_file": "NONE", "excerpt": "Empty query context.", "score": 0.0}]

    return _index.retrieve(query, top_k=top_k)


def reset_index():
    """Forces the index to rebuild on next query (useful after testing/seeding)."""
    global _index
    _index = BM25Index()
