"""
Soil Report Agent (doc 11 OCR pipeline).

Flow:
  upload → extract (per-field confidence) → farmer confirms → soil_tests + SOIL_REPORT_UPDATED

Never writes to the Digital Twin until `farmer_confirmed=True`.
Low-confidence fields (< 0.85) are flagged for review.

OCR engines (PaddleOCR / EasyOCR / tesseract) are optional. The default
extractor is a deterministic regex parser over decoded text — used for
tests, sample reports, and as a fallback when OCR libraries are absent.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from datetime import date, datetime, timezone
from typing import Any

from ..core.event_bus import get_bus
from ..core.events import Event, EventType
from . import soil_agent
from ..db import _json_load

CONFIDENCE_REVIEW_THRESHOLD = 0.85
UPLOAD_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "soil_reports")
)

# Patterns for Indian Soil Health Card / lab reports (N,P,K in kg/ha).
_FIELD_PATTERNS: dict[str, list[re.Pattern]] = {
    "n_kg_ha": [
        re.compile(r"\bN(?:itrogen)?\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:kg/?ha)?", re.I),
        re.compile(r"available\s+n(?:itrogen)?\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)", re.I),
    ],
    "p_kg_ha": [
        re.compile(r"\bP(?:hosphorus|hos)?\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:kg/?ha)?", re.I),
        re.compile(r"available\s+p(?:hosphorus)?\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)", re.I),
    ],
    "k_kg_ha": [
        re.compile(r"\bK(?:potassium)?\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:kg/?ha)?", re.I),
        re.compile(r"available\s+k(?:potassium)?\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)", re.I),
    ],
    "ph": [re.compile(r"\bpH\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)", re.I)],
    "oc_percent": [
        re.compile(r"\bOC(?:\s*%|\s+percent)?\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)", re.I),
        re.compile(r"organic\s+carbon\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)", re.I),
    ],
    "ec_ds_m": [
        re.compile(r"\bEC\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)", re.I),
    ],
}


def extract_from_text(text: str) -> dict[str, dict[str, Any]]:
    """
    Returns {field: {"value": float|None, "confidence": float}}.
    Found numeric fields get 0.92; missing fields get 0.0 (force review).
    """
    extracted: dict[str, dict[str, Any]] = {}
    for field, patterns in _FIELD_PATTERNS.items():
        value = None
        for pat in patterns:
            m = pat.search(text or "")
            if m:
                value = float(m.group(1))
                break
        extracted[field] = {
            "value": value,
            "confidence": 0.92 if value is not None else 0.0,
        }
    return extracted


def extract_from_bytes(filename: str, data: bytes) -> tuple[dict[str, dict[str, Any]], str]:
    """
    Decode text files directly. For images/PDF try optional OCR engines,
    then fall back to utf-8 decode (useful for fixture .txt reports).
    Returns (extracted, engine_name).
    """
    name = (filename or "").lower()
    if name.endswith((".txt", ".md", ".csv")) or not name:
        text = data.decode("utf-8", errors="replace")
        return extract_from_text(text), "regex_text"

    ocr_text, engine = _try_ocr(data, name)
    if ocr_text:
        return extract_from_text(ocr_text), engine

    # Last resort: treat as text so tests/manual paste still work
    text = data.decode("utf-8", errors="replace")
    extracted = extract_from_text(text)
    if all(v["value"] is None for v in extracted.values()):
        for k in extracted:
            extracted[k]["confidence"] = 0.0
        return extracted, "ocr_failed"
    return extracted, "regex_fallback"


def _extract_text_from_pdf(data: bytes) -> str:
    """Extract readable text from a PDF byte array without requiring external binaries."""
    try:
        import pypdf
        import io
        reader = pypdf.PdfReader(io.BytesIO(data))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        if text.strip():
            return text
    except Exception:
        pass
    try:
        import zlib
        found_texts = []
        for stream in re.findall(b"stream[\r\n]+(.*?)[\r\n]+endstream", data, re.DOTALL):
            try:
                decomp = zlib.decompress(stream)
            except Exception:
                decomp = stream
            for m in re.finditer(rb"\(([^\(\)]+)\)", decomp):
                try:
                    found_texts.append(m.group(1).decode("latin-1"))
                except Exception:
                    pass
        if found_texts:
            return " ".join(found_texts)
    except Exception:
        pass
    return ""


def _try_ocr(data: bytes, name: str) -> tuple[str | None, str]:
    """Optional PDF text extractor and EasyOCR."""
    if name.endswith(".pdf"):
        pdf_text = _extract_text_from_pdf(data)
        if pdf_text and len(pdf_text.strip()) > 5:
            return pdf_text, "pdf_text_extractor"
    try:
        import easyocr  # type: ignore
        import tempfile

        ext = os.path.splitext(name)[1] or ".png"
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        try:
            reader = easyocr.Reader(["en"], gpu=False)
            results = reader.readtext(tmp_path, detail=0)
            ocr_text = "\n".join(results)
            if ocr_text.strip():
                return ocr_text, "easyocr"
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
    except Exception:
        pass
    return None, "no_ocr_engine"


def needs_review(extracted: dict[str, dict[str, Any]]) -> list[str]:
    return [
        field
        for field, payload in extracted.items()
        if payload.get("confidence", 0) < CONFIDENCE_REVIEW_THRESHOLD
        or payload.get("value") is None
    ]


def store_upload(
    conn: sqlite3.Connection,
    field_id: int,
    extracted: dict,
    original_file_path: str | None,
    status: str = "PENDING_CONFIRMATION",
) -> int:
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO soil_report_uploads
           (field_id, original_file_path, extracted_json, status)
           VALUES (?,?,?,?)""",
        (field_id, original_file_path, json.dumps(extracted), status),
    )
    conn.commit()
    return int(cur.lastrowid)


def save_original_file(field_id: int, filename: str, data: bytes) -> str:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    safe = os.path.basename(filename) or "report.txt"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(UPLOAD_DIR, f"{field_id}_{stamp}_{safe}")
    with open(path, "wb") as f:
        f.write(data)
    return path


def get_upload(conn: sqlite3.Connection, upload_id: int) -> dict | None:
    row = conn.execute(
        "SELECT * FROM soil_report_uploads WHERE upload_id = ?", (upload_id,)
    ).fetchone()
    if row is None:
        return None
    data = dict(row)
    try:
        data["extracted"] = _json_load(data["extracted_json"])
    except (json.JSONDecodeError, TypeError):
        data["extracted"] = {}
    return data


def confirm_and_write(
    conn: sqlite3.Connection,
    upload_id: int,
    confirmed: dict[str, Any],
    *,
    actor: str = "farmer",
    emit_event: bool = True,
) -> dict:
    """
    Writes soil_tests ONLY after explicit confirmation.
    `confirmed` must include n_kg_ha, p_kg_ha, k_kg_ha (farmer-corrected).
    """
    upload = get_upload(conn, upload_id)
    if upload is None:
        raise ValueError(f"Unknown upload_id {upload_id}")
    if upload["status"] == "CONFIRMED":
        raise ValueError("Upload already confirmed")

    for key in ("n_kg_ha", "p_kg_ha", "k_kg_ha"):
        if confirmed.get(key) is None:
            raise ValueError(f"Confirmed values must include {key}")

    test_date = confirmed.get("test_date") or date.today().isoformat()
    soil_test_id = soil_agent.write_soil_test(
        conn,
        upload["field_id"],
        test_date,
        float(confirmed["n_kg_ha"]),
        float(confirmed["p_kg_ha"]),
        float(confirmed["k_kg_ha"]),
        ph=confirmed.get("ph"),
        oc_percent=confirmed.get("oc_percent"),
        ec_ds_m=confirmed.get("ec_ds_m"),
        source="ocr",
    )
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """UPDATE soil_report_uploads
           SET status = 'CONFIRMED', confirmed_at = ?, soil_test_id = ?
           WHERE upload_id = ?""",
        (now, soil_test_id, upload_id),
    )
    conn.execute(
        """INSERT INTO audit_log (entity_type, entity_id, action, actor, new_value)
           VALUES (?,?,?,?,?)""",
        (
            "soil_test",
            soil_test_id,
            "OCR_CONFIRMED",
            actor,
            json.dumps({"upload_id": upload_id, "values": confirmed}),
        ),
    )
    conn.commit()

    if emit_event:
        get_bus().publish(
            Event.create(
                EventType.SOIL_REPORT_UPDATED,
                field_id=int(upload["field_id"]),
                payload={
                    "upload_id": upload_id,
                    "soil_test_id": soil_test_id,
                    "source": "ocr",
                },
                actor=actor,
            ),
            conn=conn,
        )
    return {
        "status": "CONFIRMED",
        "upload_id": upload_id,
        "soil_test_id": soil_test_id,
        "values": {
            "n_kg_ha": float(confirmed["n_kg_ha"]),
            "p_kg_ha": float(confirmed["p_kg_ha"]),
            "k_kg_ha": float(confirmed["k_kg_ha"]),
            "ph": confirmed.get("ph"),
            "test_date": test_date,
        },
    }


def process_upload(
    conn: sqlite3.Connection,
    field_id: int,
    filename: str,
    data: bytes,
) -> dict:
    path = save_original_file(field_id, filename, data)
    extracted, engine = extract_from_bytes(filename, data)
    review = needs_review(extracted)
    status = "OCR_FAILED" if engine == "ocr_failed" and review == list(extracted) else "PENDING_CONFIRMATION"
    upload_id = store_upload(conn, field_id, extracted, path, status=status)
    return {
        "upload_id": upload_id,
        "field_id": field_id,
        "status": status,
        "engine": engine,
        "original_file_path": path,
        "extracted": extracted,
        "fields_needing_review": review,
        "review_threshold": CONFIDENCE_REVIEW_THRESHOLD,
        "message": (
            "Low-confidence fields must be confirmed or corrected by the farmer. "
            "Nothing has been written to the Digital Twin yet."
        ),
    }
