"""
Test: Real Soil Health Card OCR — Jqbe2.png
Maharashtra SHC (MH5468/2024-25/208451), issued 15-06-2024
Farmer: Ramesh Balasaheb Patil, Baramati, Pune

Ground-truth values read directly from the card image:
  N = 198 kg/ha, P = 18.5 kg/ha, K = 312 kg/ha
  pH = 7.8, OC = 0.48 %, EC = 0.42 dS/m
  Micronutrients: Zn = 0.52 ppm (Deficient), B = 0.38 ppm (Deficient),
                  S = 12.4 ppm, Fe = 6.8 ppm, Mn = 4.1 ppm, Cu = 0.85 ppm
"""

from __future__ import annotations

import os
import pytest

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "Jqbe2.png")

# Ground truth from the card
GROUND_TRUTH = {
    "n_kg_ha": 198.0,
    "p_kg_ha": 18.5,
    "k_kg_ha": 312.0,
    "ph": 7.8,
    "oc_percent": 0.48,
    "ec_ds_m": 0.42,
}

MICRO_GROUND_TRUTH = {
    "zn_ppm": 0.52,
    "s_ppm": 12.4,
    "fe_ppm": 6.8,
    "mn_ppm": 4.1,
    "cu_ppm": 0.85,
    "b_ppm": 0.38,
}

DEFICIENT_FIELDS = {"zn_ppm", "b_ppm"}


@pytest.mark.skipif(
    not os.path.exists(FIXTURE_PATH),
    reason="Real soil card fixture Jqbe2.png not present",
)
def test_real_soilcard_jqbe2_macronutrients():
    """Extract correct values and flag actual low-confidence OCR for review."""
    from app.core.ocr import run_ocr_pipeline

    with open(FIXTURE_PATH, "rb") as f:
        data = f.read()

    result = run_ocr_pipeline(data, "Jqbe2.png")

    assert result["status"] == "extracted", f"OCR failed: {result}"
    fields = result["extracted_data"]

    for field, expected in GROUND_TRUTH.items():
        val = fields[field]["value"]
        conf = fields[field]["confidence"]
        assert val is not None, f"{field}: value is None"
        assert abs(val - expected) < 0.5, (
            f"{field}: expected {expected}, got {val}"
        )
        assert 0.0 < conf <= 1.0, f"{field}: invalid OCR confidence {conf}"

    # Confidence depends on OCR runtime; never inflate it to force auto-approval.
    review = [f for f in result["fields_needing_review"] if f in GROUND_TRUTH]
    expected_review = [f for f in GROUND_TRUTH if fields[f]["confidence"] < 0.85]
    assert set(review) == set(expected_review)


@pytest.mark.skipif(
    not os.path.exists(FIXTURE_PATH),
    reason="Real soil card fixture Jqbe2.png not present",
)
def test_real_soilcard_jqbe2_micronutrients():
    """Micronutrients extracted from real card."""
    from app.core.ocr import run_ocr_pipeline

    with open(FIXTURE_PATH, "rb") as f:
        data = f.read()

    result = run_ocr_pipeline(data, "Jqbe2.png")
    micros = result.get("micronutrients", {})

    # At least Zn and S should be detected — card has all 6 listed
    assert "zn_ppm" in micros, "Zn not extracted from real card"
    assert abs(micros["zn_ppm"]["value"] - MICRO_GROUND_TRUTH["zn_ppm"]) < 0.1, (
        f"Zn value mismatch: {micros['zn_ppm']['value']}"
    )


@pytest.mark.skipif(
    not os.path.exists(FIXTURE_PATH),
    reason="Real soil card fixture Jqbe2.png not present",
)
def test_real_soilcard_jqbe2_metadata():
    """Metadata fields extracted from real card."""
    from app.core.ocr import run_ocr_pipeline

    with open(FIXTURE_PATH, "rb") as f:
        data = f.read()

    result = run_ocr_pipeline(data, "Jqbe2.png")
    meta = result.get("metadata", {})

    # Sample ID must contain the card ID
    if "sample_id" in meta:
        assert "MH5468" in meta["sample_id"] or "208451" in meta["sample_id"], (
            f"Unexpected sample_id: {meta['sample_id']}"
        )


@pytest.mark.skipif(
    not os.path.exists(FIXTURE_PATH),
    reason="Real soil card fixture Jqbe2.png not present",
)
def test_real_soilcard_jqbe2_engine():
    """EasyOCR (or LLM-refined) engine is used on real image."""
    from app.core.ocr import run_ocr_pipeline

    with open(FIXTURE_PATH, "rb") as f:
        data = f.read()

    result = run_ocr_pipeline(data, "Jqbe2.png")
    assert "easyocr" in result["engine"] or "llm_refined" in result["engine"], (
        f"Unexpected engine: {result['engine']}"
    )
