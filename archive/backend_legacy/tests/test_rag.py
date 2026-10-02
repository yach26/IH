"""
AgroTwin AI — Unit Tests: Agentic RAG Layer
===========================================
Tests cover:
  1. Ingestion: chunk count, metadata parsing, frontmatter, inline metadata
  2. Metadata filtering: hard region + crop filters
  3. BM25 retrieval: scores are non-zero for relevant queries
  4. Hybrid retrieval (RRF): result order, top-k
  5. Knowledge Agent: EvidencePack contract, NO_EVIDENCE fallback
  6. RAG Validation Agent: region/crop mismatch detection, empty pack handling

Run from project root:
    cd backend
    python -m pytest tests/test_rag.py -v

Or without pytest:
    python backend/tests/test_rag.py
"""

import sys
import os
import tempfile
import textwrap
import unittest

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.rag.ingestion import (
    ingest_documents,
    HybridIndex,
    ChunkStore,
    _parse_frontmatter,
    _extract_inline_metadata,
    _split_into_paragraphs,
)
from backend.app.agents.knowledge_agent import (
    retrieve_evidence,
    EvidencePack,
    reset_index,
    _build_query,
)
from backend.app.agents.rag_validation_agent import (
    validate_evidence_pack,
    RAGValidationResult,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures — minimal trusted documents for isolated testing
# ─────────────────────────────────────────────────────────────────────────────

SAMPLE_DOC_KOLHAPUR_RICE = textwrap.dedent("""\
    ---
    document_type: rdf
    issuing_authority: MPKV-ICAR
    publication_date: "2022"
    region: kolhapur
    crops: [rice]
    nutrients: [N, P, K]
    source: test_kolhapur_rice.md
    ---

    ## Rice Basal Dose — Kolhapur

    **crop**: rice
    **region**: kolhapur
    **crop_stage**: basal
    **nutrient**: N

    For rice grown in Kolhapur on black soils, apply 100 kg N/ha, 50 kg P2O5/ha,
    50 kg K2O/ha as the total seasonal dose. Apply full P at basal before transplanting.

    ## Rice Tillering — Kolhapur

    **crop**: rice
    **region**: kolhapur
    **crop_stage**: tillering
    **nutrient**: N

    At tillering stage (21-28 DAT), apply 25 kg N/ha using Urea.
    Avoid application if heavy rain is forecast. Soil must be at field capacity.

    ## Rice Panicle Initiation — Kolhapur

    **crop**: rice
    **region**: kolhapur
    **crop_stage**: panicle_initiation
    **nutrient**: N

    At panicle initiation (45-55 DAT), apply 25 kg N/ha as Urea.
    If yellowing observed earlier, advance by 5-7 days.
""")

SAMPLE_DOC_JALGAON_BANANA = textwrap.dedent("""\
    ---
    document_type: rdf
    issuing_authority: MPKV-ICAR
    publication_date: "2021"
    region: jalgaon
    crops: [banana]
    nutrients: [N, P, K]
    source: test_jalgaon_banana.md
    ---

    ## Banana Seasonal Dose — Jalgaon

    **crop**: banana
    **region**: jalgaon
    **nutrient**: N

    Banana total seasonal dose in Jalgaon: 200 g N/plant/year.
    Use mid-point 2250 plants/ha when exact density is unavailable — flag as DERIVED_DENSITY.

    ## Banana Bunch Development — Jalgaon

    **crop**: banana
    **region**: jalgaon
    **crop_stage**: bunch_development
    **nutrient**: K

    During bunch development (months 4-6), apply 75 g K2O/plant/month.
    Potassium deficiency at this stage directly reduces bunch weight.
""")

SAMPLE_DOC_FCO = textwrap.dedent("""\
    ---
    document_type: fco_specification
    issuing_authority: FCO-India
    publication_date: "2023"
    region: all
    crops: [all]
    nutrients: [N, P, K]
    source: test_fco.md
    ---

    ## Urea Specification

    **product**: UREA
    **document_type**: fco_specification
    **nutrient**: N

    Urea: N content 46.0% minimum guaranteed (FCO India, 2023).
    Apply in split doses. Never apply more than 50 kg N/ha per dose.
    High volatilisation risk at temperature above 35 degrees C or pH above 7.5.

    ## DAP Specification

    **product**: DAP
    **document_type**: fco_specification
    **nutrients**: [N, P]

    DAP: N content 18.0%, P2O5 content 46.0% minimum guaranteed.
    Primary use is basal phosphorus application. Apply as basal only.
""")


def _make_temp_docs(*docs: str) -> str:
    """Write docs to a temp dir and return its path."""
    tmp = tempfile.mkdtemp(prefix="agrotwin_rag_test_")
    for i, content in enumerate(docs):
        with open(os.path.join(tmp, f"doc_{i}.md"), "w", encoding="utf-8") as fh:
            fh.write(content)
    return tmp


# ─────────────────────────────────────────────────────────────────────────────
# Test Suite 1: Ingestion
# ─────────────────────────────────────────────────────────────────────────────

class TestIngestion(unittest.TestCase):

    def setUp(self):
        self.docs_dir = _make_temp_docs(
            SAMPLE_DOC_KOLHAPUR_RICE,
            SAMPLE_DOC_JALGAON_BANANA,
            SAMPLE_DOC_FCO,
        )

    def test_chunks_are_created(self):
        store = ingest_documents(self.docs_dir)
        self.assertGreater(len(store), 0, "Should have at least one chunk")

    def test_rice_chunks_have_region(self):
        store = ingest_documents(self.docs_dir)
        rice_chunks = [
            c for c in store.chunks
            if "rice" in c["metadata"].get("crop", [])
        ]
        self.assertGreater(len(rice_chunks), 0, "Rice chunks must exist")
        for chunk in rice_chunks:
            self.assertIn("kolhapur", chunk["metadata"]["region"],
                          f"Rice chunk must have region=kolhapur, got {chunk['metadata']['region']}")

    def test_banana_chunks_have_region(self):
        store = ingest_documents(self.docs_dir)
        banana_chunks = [
            c for c in store.chunks
            if "banana" in c["metadata"].get("crop", [])
        ]
        self.assertGreater(len(banana_chunks), 0, "Banana chunks must exist")
        for chunk in banana_chunks:
            self.assertIn("jalgaon", chunk["metadata"]["region"],
                          "Banana chunks must have region=jalgaon")

    def test_tillering_stage_parsed(self):
        store = ingest_documents(self.docs_dir)
        tillering_chunks = [
            c for c in store.chunks
            if c["metadata"].get("crop_stage") == "tillering"
        ]
        self.assertGreater(len(tillering_chunks), 0,
                           "At least one chunk should have crop_stage=tillering")

    def test_frontmatter_parsed(self):
        store = ingest_documents(self.docs_dir)
        # All chunks from MPKV-ICAR docs should have the issuing authority
        mpkv_chunks = [
            c for c in store.chunks
            if c["metadata"].get("issuing_authority") == "MPKV-ICAR"
        ]
        self.assertGreater(len(mpkv_chunks), 0, "MPKV-ICAR authority must be parsed")

    def test_citation_format(self):
        store = ingest_documents(self.docs_dir)
        for chunk in store.chunks:
            self.assertIn("#para-", chunk["citation"],
                          f"Citation must include #para- marker: {chunk['citation']}")

    def test_no_documents_returns_empty_store(self):
        empty_dir = tempfile.mkdtemp(prefix="agrotwin_empty_")
        store = ingest_documents(empty_dir)
        self.assertEqual(len(store), 0, "Empty directory should produce empty store")


# ─────────────────────────────────────────────────────────────────────────────
# Test Suite 2: Frontmatter + Inline Metadata Parsing
# ─────────────────────────────────────────────────────────────────────────────

class TestMetadataParsing(unittest.TestCase):

    def test_frontmatter_basic(self):
        content = "---\nregion: kolhapur\ncrops: [rice, wheat]\n---\n\nBody text here."
        meta, body = _parse_frontmatter(content)
        self.assertEqual(meta["region"], "kolhapur")
        self.assertIn("rice", meta["crops"])
        self.assertIn("wheat", meta["crops"])
        self.assertIn("Body text here", body)

    def test_frontmatter_missing_returns_empty(self):
        content = "No frontmatter here.\n\nJust plain text."
        meta, body = _parse_frontmatter(content)
        self.assertEqual(meta, {})
        self.assertIn("No frontmatter", body)

    def test_inline_metadata_extracted(self):
        para = "**crop**: rice\n**region**: kolhapur\n**crop_stage**: tillering\n\nSome agronomic content."
        inline = _extract_inline_metadata(para)
        self.assertEqual(inline["crop"], "rice")
        self.assertEqual(inline["region"], "kolhapur")
        self.assertEqual(inline["crop_stage"], "tillering")

    def test_inline_metadata_list_values(self):
        para = "**nutrients**: N, P, K\nSome content about nutrients."
        inline = _extract_inline_metadata(para)
        self.assertIsInstance(inline["nutrients"], list)
        self.assertIn("N", inline["nutrients"])

    def test_chunk_split_respects_min_length(self):
        text = "Short.\n\nThis is a longer paragraph with meaningful agronomic content about rice cultivation in Kolhapur district.\n\nTiny."
        chunks = _split_into_paragraphs(text)
        for c in chunks:
            self.assertGreaterEqual(len(c), 60,
                                    f"Chunk too short: '{c}'")


# ─────────────────────────────────────────────────────────────────────────────
# Test Suite 3: Metadata Filtering
# ─────────────────────────────────────────────────────────────────────────────

class TestMetadataFiltering(unittest.TestCase):

    def setUp(self):
        docs_dir = _make_temp_docs(SAMPLE_DOC_KOLHAPUR_RICE, SAMPLE_DOC_JALGAON_BANANA)
        self.store = ingest_documents(docs_dir)
        self.idx = HybridIndex(self.store)
        self.idx.build()

    def test_region_filter_isolates_kolhapur(self):
        results = self.idx.query(
            "nitrogen application recommendation",
            filters={"region": "kolhapur"},
        )
        for r in results:
            self.assertIn("kolhapur", r["metadata"]["region"],
                          "All results must have region=kolhapur when filtered")

    def test_region_filter_isolates_jalgaon(self):
        results = self.idx.query(
            "potassium application banana",
            filters={"region": "jalgaon"},
        )
        for r in results:
            self.assertIn("jalgaon", r["metadata"]["region"],
                          "All results must have region=jalgaon when filtered")

    def test_crop_filter_excludes_banana_for_rice_query(self):
        results = self.idx.query(
            "nitrogen fertilizer",
            filters={"crop": "rice"},
        )
        for r in results:
            self.assertIn("rice", r["metadata"]["crop"],
                          "Rice filter must exclude banana chunks")

    def test_combined_region_crop_filter(self):
        results = self.idx.query(
            "nitrogen rice tillering",
            filters={"region": "kolhapur", "crop": "rice"},
        )
        self.assertGreater(len(results), 0, "Should find rice+kolhapur chunks")
        for r in results:
            self.assertIn("rice", r["metadata"]["crop"])
            self.assertIn("kolhapur", r["metadata"]["region"])

    def test_wrong_region_returns_empty(self):
        """Query for a region not in documents should return no results."""
        results = self.idx.query(
            "nitrogen application",
            filters={"region": "pune"},
        )
        self.assertEqual(len(results), 0,
                         "No results expected for a region not in docs")

    def test_crop_stage_filter(self):
        results = self.idx.query(
            "nitrogen",
            filters={"region": "kolhapur", "crop": "rice", "crop_stage": "tillering"},
        )
        self.assertGreater(len(results), 0, "Tillering chunks must be found")
        for r in results:
            self.assertEqual(r["metadata"].get("crop_stage"), "tillering")


# ─────────────────────────────────────────────────────────────────────────────
# Test Suite 4: BM25 Retrieval Quality
# ─────────────────────────────────────────────────────────────────────────────

class TestBM25Retrieval(unittest.TestCase):

    def setUp(self):
        docs_dir = _make_temp_docs(
            SAMPLE_DOC_KOLHAPUR_RICE,
            SAMPLE_DOC_JALGAON_BANANA,
            SAMPLE_DOC_FCO,
        )
        self.store = ingest_documents(docs_dir)
        self.idx = HybridIndex(self.store)
        self.idx.build()

    def test_tillering_query_returns_tillering_chunk_first(self):
        results = self.idx.query(
            "nitrogen application at tillering stage rice kolhapur",
            filters={"region": "kolhapur", "crop": "rice"},
        )
        self.assertGreater(len(results), 0)
        top_chunk = results[0]
        # Top result should be about tillering
        self.assertIn("tillering", top_chunk["text"].lower(),
                      "Top result for tillering query should contain 'tillering'")

    def test_urea_query_returns_relevant_chunks(self):
        results = self.idx.query("urea nitrogen specification FCO", top_k=3)
        texts = " ".join(r["text"].lower() for r in results)
        self.assertIn("urea", texts, "Urea query must return urea-related chunks")

    def test_top_k_respected(self):
        results = self.idx.query("nitrogen fertilizer recommendation", top_k=2)
        self.assertLessEqual(len(results), 2, "top_k=2 must not return more than 2 results")

    def test_empty_query_no_crash(self):
        """Even an empty query string must not raise."""
        try:
            results = self.idx.query("", top_k=3)
            # Empty query may return 0 or random results — just must not crash
        except Exception as exc:
            self.fail(f"Empty query raised exception: {exc}")

    def test_scores_are_non_negative(self):
        results = self.idx.query("rice kolhapur nitrogen")
        for r in results:
            self.assertGreaterEqual(r["score"], 0.0, "Scores must be non-negative")


# ─────────────────────────────────────────────────────────────────────────────
# Test Suite 5: Knowledge Agent — EvidencePack Contract
# ─────────────────────────────────────────────────────────────────────────────

class TestKnowledgeAgent(unittest.TestCase):

    def setUp(self):
        """Point Knowledge Agent at isolated test docs."""
        reset_index()
        # Monkey-patch DOCS_DIR to use test fixtures
        import backend.rag.ingestion as ing_mod
        self._original_docs_dir = ing_mod.DOCS_DIR
        self._tmp = _make_temp_docs(
            SAMPLE_DOC_KOLHAPUR_RICE,
            SAMPLE_DOC_JALGAON_BANANA,
            SAMPLE_DOC_FCO,
        )
        ing_mod.DOCS_DIR = self._tmp
        reset_index()

    def tearDown(self):
        import backend.rag.ingestion as ing_mod
        ing_mod.DOCS_DIR = self._original_docs_dir
        reset_index()

    def test_returns_evidence_pack(self):
        pack = retrieve_evidence(crop="rice", region="kolhapur")
        self.assertIsInstance(pack, EvidencePack)

    def test_query_is_populated(self):
        pack = retrieve_evidence(crop="rice", region="kolhapur", crop_stage="tillering", nutrient="N")
        self.assertIn("rice", pack.query.lower())
        self.assertIn("kolhapur", pack.query.lower())

    def test_chunks_have_citation(self):
        pack = retrieve_evidence(crop="rice", region="kolhapur")
        for chunk in pack.chunks:
            self.assertIsNotNone(chunk.citation)
            self.assertTrue(len(chunk.citation) > 0, "Citation must not be empty")

    def test_evidence_respects_region_filter(self):
        pack = retrieve_evidence(crop="rice", region="kolhapur")
        for chunk in pack.chunks:
            self.assertIn("kolhapur", chunk.metadata.get("region", []),
                          "All returned chunks must match region=kolhapur")

    def test_evidence_respects_crop_filter(self):
        pack = retrieve_evidence(crop="banana", region="jalgaon")
        for chunk in pack.chunks:
            self.assertIn("banana", chunk.metadata.get("crop", []),
                          "All returned chunks must match crop=banana")

    def test_no_evidence_for_unknown_region(self):
        pack = retrieve_evidence(crop="rice", region="delhi")
        self.assertEqual(pack.confidence, "NO_EVIDENCE",
                         "Unknown region should return NO_EVIDENCE confidence")

    def test_no_evidence_pack_is_not_crash(self):
        """NO_EVIDENCE must return a valid EvidencePack, not raise."""
        pack = retrieve_evidence(crop="xyz_unknown", region="xyz_unknown")
        self.assertIsInstance(pack, EvidencePack)
        self.assertTrue(pack.is_empty())

    def test_confidence_not_empty_for_valid_query(self):
        pack = retrieve_evidence(crop="rice", region="kolhapur")
        self.assertIn(pack.confidence, ["HIGH", "MEDIUM", "LOW", "NO_EVIDENCE"])

    def test_to_dict_is_serialisable(self):
        pack = retrieve_evidence(crop="rice", region="kolhapur")
        import json
        d = pack.to_dict()
        # Must be JSON-serialisable (no numpy floats etc.)
        serialised = json.dumps(d)
        self.assertIsInstance(serialised, str)

    def test_query_builder(self):
        q = _build_query("rice", "kolhapur", "tillering", "N", "low soil nitrogen")
        self.assertIn("N", q)
        self.assertIn("rice", q)
        self.assertIn("kolhapur", q)
        self.assertIn("tillering", q)

    def test_no_quantities_in_applicability_notes(self):
        """Applicability notes must not contain kg/ha numbers (that would mean RAG is generating quantities)."""
        pack = retrieve_evidence(crop="rice", region="kolhapur")
        # Notes should never look like "apply X kg/ha" generated by the agent itself
        # (quoted source text in chunks is allowed — this checks the notes field)
        self.assertNotRegex(
            pack.applicability_notes,
            r"apply\s+\d+\s*kg/ha",
            "applicability_notes must not contain quantity prescriptions",
        )


# ─────────────────────────────────────────────────────────────────────────────
# Test Suite 6: RAG Validation Agent
# ─────────────────────────────────────────────────────────────────────────────

class TestRAGValidationAgent(unittest.TestCase):

    def setUp(self):
        reset_index()
        import backend.rag.ingestion as ing_mod
        self._original_docs_dir = ing_mod.DOCS_DIR
        self._tmp = _make_temp_docs(
            SAMPLE_DOC_KOLHAPUR_RICE,
            SAMPLE_DOC_JALGAON_BANANA,
        )
        ing_mod.DOCS_DIR = self._tmp
        reset_index()

    def tearDown(self):
        import backend.rag.ingestion as ing_mod
        ing_mod.DOCS_DIR = self._original_docs_dir
        reset_index()

    def test_valid_evidence_passes(self):
        pack = retrieve_evidence(crop="rice", region="kolhapur")
        result = validate_evidence_pack(pack, required_crop="rice", required_region="kolhapur")
        self.assertIsInstance(result, RAGValidationResult)
        if not pack.is_empty():
            self.assertTrue(result.is_applicable, "Valid evidence should be applicable")

    def test_empty_pack_is_not_applicable(self):
        pack = retrieve_evidence(crop="xyz", region="xyz")
        result = validate_evidence_pack(pack, required_crop="xyz", required_region="xyz")
        self.assertFalse(result.is_applicable)
        self.assertIn("RAG_NO_EVIDENCE", result.flags_added)
        self.assertEqual(result.confidence_adjustment, "DOWNGRADE")

    def test_region_mismatch_flag(self):
        """Retrieve banana/jalgaon evidence but validate against rice/kolhapur."""
        pack = retrieve_evidence(crop="banana", region="jalgaon")
        if pack.is_empty():
            self.skipTest("No evidence to validate")
        result = validate_evidence_pack(
            pack,
            required_crop="rice",
            required_region="kolhapur",
        )
        # Should detect mismatch
        flags = result.flags_added
        self.assertTrue(
            "REGION_MISMATCH" in flags or "CROP_MISMATCH" in flags,
            f"Expected region/crop mismatch flag, got: {flags}",
        )

    def test_to_dict_works(self):
        pack = retrieve_evidence(crop="rice", region="kolhapur")
        result = validate_evidence_pack(pack, required_crop="rice", required_region="kolhapur")
        d = result.to_dict()
        self.assertIn("is_applicable", d)
        self.assertIn("confidence_adjustment", d)
        self.assertIn("flags_added", d)


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main(verbosity=2)
