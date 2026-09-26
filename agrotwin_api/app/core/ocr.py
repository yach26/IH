import os
import shutil
from typing import BinaryIO
import uuid

UPLOAD_DIR = os.environ.get(
    "AGROTWIN_UPLOADS",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "uploads")),
)

os.makedirs(UPLOAD_DIR, exist_ok=True)


def save_upload_file(upload_file, filename: str) -> str:
    """Save the uploaded file and return the path."""
    ext = os.path.splitext(filename)[1]
    unique_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    return file_path


def run_ocr_on_file(file_path: str) -> dict:
    """
    Mock OCR pipeline for the hackathon MVP.
    In a real implementation, this would use PaddleOCR or EasyOCR.
    """
    return {
        "n_kg_ha": {"value": 150.0, "confidence": 0.95},
        "p_kg_ha": {"value": 25.0, "confidence": 0.88},
        "k_kg_ha": {"value": 120.0, "confidence": 0.92},
        "ph": {"value": 7.2, "confidence": 0.80},
        "oc_percent": {"value": 0.6, "confidence": 0.99},
        "ec_ds_m": {"value": 0.4, "confidence": 0.70},
    }
