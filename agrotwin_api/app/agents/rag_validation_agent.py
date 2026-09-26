"""
RAG applicability check (doc 06). Complements the agronomic RuleEngine.

Never blocks the ledger plan. Missing / mismatched evidence only lowers
confidence via flags.
"""

from __future__ import annotations

from typing import Any, Optional


def validate_evidence_list(
    chunks: list[dict],
    required_crop: Optional[str],
    required_region: Optional[str],
) -> dict[str, Any]:
    flags: list[str] = []
    warnings: list[str] = []
    if not chunks or (
        len(chunks) == 1
        and chunks[0].get("source_file") in ("NONE", "MISSING")
    ):
        flags.append("RAG_NO_EVIDENCE")
        return {
            "is_applicable": False,
            "confidence_adjustment": "DOWNGRADE",
            "warnings": ["No applicable evidence chunks. Plan may still proceed from the ledger."],
            "blocking_issues": [],
            "flags_added": flags,
            "validated_chunks_count": 0,
        }

    crop = (required_crop or "").lower()
    region = (required_region or "").lower()
    matched = 0
    for c in chunks:
        text = (c.get("excerpt") or c.get("text") or "").lower()
        meta = c.get("metadata") or {}
        meta_crop = " ".join(str(x) for x in (meta.get("crop") or [])).lower() if isinstance(meta.get("crop"), list) else str(meta.get("crop") or "").lower()
        meta_region = " ".join(str(x) for x in (meta.get("region") or [])).lower() if isinstance(meta.get("region"), list) else str(meta.get("region") or "").lower()
        hay = " ".join([text, meta_crop, meta_region, str(c.get("source_file") or "")])
        crop_ok = (not crop) or crop in hay
        region_ok = (not region) or region in hay
        if crop_ok and region_ok:
            matched += 1
        else:
            warnings.append("Chunk may not match crop/region filters.")
            flags.append("PARTIAL_EVIDENCE_MATCH")

    return {
        "is_applicable": matched > 0,
        "confidence_adjustment": "NONE" if matched > 0 and "PARTIAL_EVIDENCE_MATCH" not in flags else "DOWNGRADE",
        "warnings": warnings,
        "blocking_issues": [],
        "flags_added": flags,
        "validated_chunks_count": matched,
    }
