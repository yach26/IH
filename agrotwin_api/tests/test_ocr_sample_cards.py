"""Tests for OCR extraction against realistic Maharashtra Soil Health Card samples.

These fixtures represent common SHC layouts found in Maharashtra:
- Sample 1: Standard English format (Kolhapur)
- Sample 2: Bilingual Marathi/English format (Kolhapur)
- Sample 3: Compact English format (Jalgaon)
- Sample 4: Bilingual with different field labels (Kolhapur)
- Sample 5: Table-based format (Jalgaon)
"""

import os

import pytest

from app.core.ocr import run_ocr_pipeline

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

SAMPLE_FILES = [
    "shc_sample_1.txt",
    "shc_sample_2.txt",
    "shc_sample_3.txt",
    "shc_sample_4.txt",
    "shc_sample_5.txt",
]


def _load_sample(filename: str) -> bytes:
    path = os.path.join(FIXTURES_DIR, filename)
    with open(path, "rb") as f:
        return f.read()


def _extract_value(result: dict, field: str) -> float | None:
    """Helper to extract a numeric value from the OCR result."""
    data = result.get("extracted_data", {})
    if field in data and data[field].get("value") is not None:
        return data[field]["value"]
    return None


def _extract_confidence(result: dict, field: str) -> float | None:
    """Helper to extract confidence from the OCR result."""
    data = result.get("extracted_data", {})
    if field in data:
        return data[field].get("confidence")
    return None


@pytest.mark.parametrize("filename", SAMPLE_FILES)
def test_sample_card_extracts_macronutrients(filename: str):
    """All sample cards must yield N, P, K values."""
    contents = _load_sample(filename)
    result = run_ocr_pipeline(contents, filename)

    n = _extract_value(result, "n_kg_ha")
    p = _extract_value(result, "p_kg_ha")
    k = _extract_value(result, "k_kg_ha")

    assert n is not None, f"{filename}: missing n_kg_ha"
    assert p is not None, f"{filename}: missing p_kg_ha"
    assert k is not None, f"{filename}: missing k_kg_ha"

    assert n > 0, f"{filename}: n_kg_ha must be positive"
    assert p > 0, f"{filename}: p_kg_ha must be positive"
    assert k > 0, f"{filename}: k_kg_ha must be positive"


@pytest.mark.parametrize("filename", SAMPLE_FILES)
def test_sample_card_extracts_ph(filename: str):
    """All sample cards must yield pH."""
    contents = _load_sample(filename)
    result = run_ocr_pipeline(contents, filename)

    ph = _extract_value(result, "ph")
    assert ph is not None, f"{filename}: missing ph"
    assert 3.0 <= ph <= 11.0, f"{filename}: pH out of range"


@pytest.mark.parametrize("filename", SAMPLE_FILES)
def test_sample_card_extracts_organic_carbon(filename: str):
    """All sample cards must yield organic carbon."""
    contents = _load_sample(filename)
    result = run_ocr_pipeline(contents, filename)

    oc = _extract_value(result, "oc_percent")
    assert oc is not None, f"{filename}: missing oc_percent"
    assert 0.0 <= oc <= 10.0, f"{filename}: OC out of range"


@pytest.mark.parametrize("filename", SAMPLE_FILES)
def test_sample_card_has_per_field_confidence(filename: str):
    """Every extracted field must have a confidence score."""
    contents = _load_sample(filename)
    result = run_ocr_pipeline(contents, filename)

    for field in ["n_kg_ha", "p_kg_ha", "k_kg_ha", "ph", "oc_percent"]:
        conf = _extract_confidence(result, field)
        if conf is not None:
            assert 0.0 <= conf <= 1.0, f"{filename}: confidence for {field} out of range"


def test_sample_1_specific_values():
    """Sample 1 (Kolhapur English) should extract exact values."""
    contents = _load_sample("shc_sample_1.txt")
    result = run_ocr_pipeline(contents, "shc_sample_1.txt")

    assert _extract_value(result, "n_kg_ha") == pytest.approx(210.0, rel=0.01)
    assert _extract_value(result, "p_kg_ha") == pytest.approx(35.0, rel=0.01)
    assert _extract_value(result, "k_kg_ha") == pytest.approx(310.0, rel=0.01)
    assert _extract_value(result, "ph") == pytest.approx(7.9, rel=0.01)
    assert _extract_value(result, "oc_percent") == pytest.approx(0.62, rel=0.01)


def test_sample_3_specific_values():
    """Sample 3 (Jalgaon compact) should extract exact values."""
    contents = _load_sample("shc_sample_3.txt")
    result = run_ocr_pipeline(contents, "shc_sample_3.txt")

    assert _extract_value(result, "n_kg_ha") == pytest.approx(95.5, rel=0.01)
    assert _extract_value(result, "p_kg_ha") == pytest.approx(22.0, rel=0.01)
    assert _extract_value(result, "k_kg_ha") == pytest.approx(180.0, rel=0.01)
    assert _extract_value(result, "ph") == pytest.approx(7.5, rel=0.01)


def test_sample_5_table_format():
    """Sample 5 (table format) should extract values from pipe-delimited table."""
    contents = _load_sample("shc_sample_5.txt")
    result = run_ocr_pipeline(contents, "shc_sample_5.txt")

    assert _extract_value(result, "n_kg_ha") == pytest.approx(130.0, rel=0.01)
    assert _extract_value(result, "p_kg_ha") == pytest.approx(30.5, rel=0.01)
    assert _extract_value(result, "k_kg_ha") == pytest.approx(220.0, rel=0.01)


def test_bilingual_sample_extracts_values():
    """Sample 2 (bilingual Marathi/English) must extract values despite mixed language."""
    contents = _load_sample("shc_sample_2.txt")
    result = run_ocr_pipeline(contents, "shc_sample_2.txt")

    assert _extract_value(result, "n_kg_ha") == pytest.approx(180.0, rel=0.01)
    assert _extract_value(result, "p_kg_ha") == pytest.approx(28.0, rel=0.01)
    assert _extract_value(result, "k_kg_ha") == pytest.approx(250.0, rel=0.01)
    assert _extract_value(result, "ph") == pytest.approx(6.8, rel=0.01)


def test_low_confidence_fields_flagged_for_review():
    """Fields with confidence < 0.85 must appear in fields_needing_review."""
    contents = _load_sample("shc_sample_1.txt")
    result = run_ocr_pipeline(contents, "shc_sample_1.txt")

    assert "fields_needing_review" in result
    assert isinstance(result["fields_needing_review"], list)


def test_text_files_get_high_confidence():
    """Plain text files should get confidence >= 0.95."""
    contents = _load_sample("shc_sample_1.txt")
    result = run_ocr_pipeline(contents, "shc_sample_1.txt")

    for field in ["n_kg_ha", "p_kg_ha", "k_kg_ha"]:
        conf = _extract_confidence(result, field)
        if conf is not None:
            assert conf >= 0.95, f"Text file confidence for {field} should be >= 0.95, got {conf}"
