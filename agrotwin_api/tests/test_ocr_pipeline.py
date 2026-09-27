"""
Tests for the Real OCR Pipeline & Endpoints (EasyOCR, PDF, API routes).
"""

from __future__ import annotations

import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from app.main import app
from app.api.routes import get_conn
from app.core.ocr import run_ocr_pipeline, run_ocr_on_file, get_ocr_reader


@pytest.fixture
def client(db):
    conn, ids = db

    def _override():
        yield conn

    app.dependency_overrides[get_conn] = _override
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_conn, None)


@pytest.fixture
def sample_report_image_bytes():
    """Generate a clean synthetic soil test report image with standard font."""
    img = Image.new("RGB", (700, 350), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((30, 20), "GOVERNMENT SOIL TESTING LABORATORY", fill=(0, 0, 0))
    d.text((30, 50), "Farmer Name: Ramesh Patil", fill=(0, 0, 0))
    d.text((30, 80), "Sample No: SHC-2026-981", fill=(0, 0, 0))
    d.text((30, 120), "Available Nitrogen (N): 215.5 kg/ha", fill=(0, 0, 0))
    d.text((30, 160), "Available Phosphorus (P): 24.2 kg/ha", fill=(0, 0, 0))
    d.text((30, 200), "Available Potassium (K): 165.0 kg/ha", fill=(0, 0, 0))
    d.text((30, 240), "Soil pH: 7.35", fill=(0, 0, 0))
    d.text((30, 280), "Organic Carbon (OC): 0.58 %", fill=(0, 0, 0))
    d.text((30, 310), "Electrical Conductivity (EC): 0.35 dS/m", fill=(0, 0, 0))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def sample_report_text():
    return (
        "Soil Testing Laboratory, Jalgaon\n"
        "Farmer Name: Ramesh Patil\n"
        "Sample ID: SHC-104\n"
        "Available Nitrogen (N): 190.0 kg/ha\n"
        "Available Phosphorus (P): 21.0 kg/ha\n"
        "Available Potassium (K): 150.0 kg/ha\n"
        "pH: 7.2\n"
        "Organic Carbon (OC): 0.62 %\n"
        "EC: 0.40 dS/m\n"
    )


def test_ocr_health(client):
    res = client.get("/ocr/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("ready", "degraded")
    assert "EasyOCR" in data["engine"]
    assert ".png" in data["supported_extensions"]


def test_ocr_standalone_text_file(client, sample_report_text):
    files = {"file": ("report.txt", io.BytesIO(sample_report_text.encode("utf-8")), "text/plain")}
    res = client.post("/ocr/extract", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "extracted"
    extracted = data["extracted_data"]
    assert extracted["n_kg_ha"]["value"] == 190.0
    assert extracted["p_kg_ha"]["value"] == 21.0
    assert extracted["k_kg_ha"]["value"] == 150.0
    assert extracted["ph"]["value"] == 7.2
    assert extracted["oc_percent"]["value"] == 0.62
    assert extracted["ec_ds_m"]["value"] == 0.40
    assert extracted["n_kg_ha"]["confidence"] >= 0.85


def test_real_easyocr_image_extraction(sample_report_image_bytes):
    """Verifies that EasyOCR processes real image pixels and extracts nutrients."""
    res = run_ocr_pipeline(sample_report_image_bytes, "soil_test.png")
    assert res["status"] == "extracted"
    assert res["engine"].startswith("easyocr")
    data = res["extracted_data"]
    # Check that actual numbers were recognized from the image
    assert data["n_kg_ha"]["value"] is not None
    assert abs(data["n_kg_ha"]["value"] - 215.5) < 5.0
    assert data["ph"]["value"] is not None
    assert 6.5 <= data["ph"]["value"] <= 8.0
    assert data["n_kg_ha"]["confidence"] > 0.5


def test_corrupt_image_upload_falls_back_to_manual_entry_live(client, db):
    """Phase 4.1: a real corrupt/unreadable image, uploaded over live HTTP, must
    signal graceful fallback (not a 500), and must NOT write to soil_tests since
    nothing was ever confirmed."""
    conn, ids = db
    field_id = ids["field_id"]

    before = conn.execute(
        "SELECT COUNT(*) AS n FROM soil_tests WHERE field_id = ?", (field_id,)
    ).fetchone()["n"]

    garbage_png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00\xff\x13\x37" * 200
    files = {"file": ("corrupt_report.png", io.BytesIO(garbage_png_bytes), "image/png")}
    res = client.post(f"/fields/{field_id}/soil-report/upload", files=files)

    assert res.status_code == 200, res.text
    body = res.json()
    assert body["status"] in ("no_text_detected", "extraction_failed", "OCR_FAILED")
    for v in body["extracted_data"].values():
        assert v["value"] is None

    after = conn.execute(
        "SELECT COUNT(*) AS n FROM soil_tests WHERE field_id = ?", (field_id,)
    ).fetchone()["n"]
    assert after == before, "Upload alone must never write to soil_tests without farmer confirmation"


def test_field_upload_and_confirm_flow(client, sample_report_text, db):
    conn, ids = db
    field_id = ids["field_id"]

    # Upload via field endpoint
    files = {"file": ("report.txt", io.BytesIO(sample_report_text.encode("utf-8")), "text/plain")}
    res = client.post(f"/fields/{field_id}/soil-report/upload", files=files)
    assert res.status_code == 200
    upload_res = res.json()
    assert upload_res["status"] == "PENDING_CONFIRMATION"
    upload_id = upload_res["upload_id"]
    extracted = upload_res["extracted_data"]
    assert extracted["n_kg_ha"]["value"] == 190.0

    # Farmer confirms values
    confirm_body = {
        "upload_id": upload_id,
        "soil_test": {
            "n_kg_ha": 195.0,  # Farmer adjusted
            "p_kg_ha": 21.0,
            "k_kg_ha": 150.0,
            "ph": 7.2,
            "oc_percent": 0.62,
            "ec_ds_m": 0.40,
            "source": "ocr",
            "test_date": "2026-09-27",
        }
    }
    confirm_res = client.post(f"/fields/{field_id}/soil-report/confirm", json=confirm_body)
    assert confirm_res.status_code == 200
    assert confirm_res.json()["status"] == "success"

    # Verify soil test was written into DB
    row = conn.execute(
        "SELECT * FROM soil_tests WHERE field_id = ? ORDER BY soil_test_id DESC LIMIT 1",
        (field_id,)
    ).fetchone()
    assert row is not None
    assert row["source"] == "ocr"
    assert row["n_kg_ha"] == 195.0
