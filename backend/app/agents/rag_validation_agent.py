"""
AgroTwin AI — RAG Validation Agent
====================================
Implements doc 06_AGENTIC_RAG.md — Validation Agent role for RAG evidence.

Responsibility:
  - Checks that the EvidencePack returned by the Knowledge Agent is applicable
    to the current recommendation context (region/crop match).
  - Complements validation_agent.py (which handles ledger + weather checks).
  - Returns structured applicability verdict with confidence adjustment.

SCOPE RULES:
  - Never modifies or generates evidence text.
  - Only validates metadata applicability.
  - When evidence is absent or mismatched, lowers confidence — does NOT block
    the ledger-based plan (which can still proceed, per doc 06 checklist).
"""

from __future__ import annotations

from typing import Optional
from backend.app.agents.knowledge_agent import EvidencePack


# ─────────────────────────────────────────────────────────────────────────────
# RAG Validation result schema
# ─────────────────────────────────────────────────────────────────────────────

class RAGValidationResult:
    """
    Result of validating an EvidencePack against a recommendation context.
    """

    def __init__(
        self,
        is_applicable: bool,
        confidence_adjustment: str,
        warnings: list[str],
        blocking_issues: list[str],
        flags_added: list[str],
        validated_chunks_count: int,
    ):
        self.is_applicable = is_applicable
        self.confidence_adjustment = confidence_adjustment  # "NONE" | "DOWNGRADE" | "SEVERE_DOWNGRADE"
        self.warnings = warnings
        self.blocking_issues = blocking_issues
        self.flags_added = flags_added
        self.validated_chunks_count = validated_chunks_count

    def to_dict(self) -> dict:
        return {
            "is_applicable": self.is_applicable,
            "confidence_adjustment": self.confidence_adjustment,
            "warnings": self.warnings,
            "blocking_issues": self.blocking_issues,
            "flags_added": self.flags_added,
            "validated_chunks_count": self.validated_chunks_count,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Core validation function
# ─────────────────────────────────────────────────────────────────────────────

def validate_evidence_pack(
    evidence: EvidencePack,
    required_crop: Optional[str],
    required_region: Optional[str],
    required_crop_stage: Optional[str] = None,
) -> RAGValidationResult:
    """
    Validate an EvidencePack against required context.

    Checks:
      1. Evidence not empty (NO_EVIDENCE → confidence downgrade, not block).
      2. Every chunk's region matches required_region (hard).
      3. Every chunk's crop matches required_crop (hard).
      4. Crop stage alignment (soft warning only).
      5. Evidence source authority (warn on unknown authority).

    Returns RAGValidationResult.
    """
    warnings: list[str] = []
    blocking_issues: list[str] = []
    flags_added: list[str] = []

    crop_norm   = required_crop.lower().strip()   if required_crop   else None
    region_norm = required_region.lower().strip() if required_region else None
    stage_norm  = required_crop_stage.lower().strip() if required_crop_stage else None

    # ── Check 1: Empty evidence ───────────────────────────────────────────────
    if evidence.is_empty():
        flags_added.append("RAG_NO_EVIDENCE")
        warnings.append(
            "RAG_NO_EVIDENCE: No evidence retrieved for this crop/region combination. "
            "Ledger-based recommendation can proceed but RAG confidence is downgraded. "
            "Consider adding relevant documents to backend/rag/docs/."
        )
        return RAGValidationResult(
            is_applicable=False,
            confidence_adjustment="DOWNGRADE",
            warnings=warnings,
            blocking_issues=blocking_issues,
            flags_added=flags_added,
            validated_chunks_count=0,
        )

    # ── Check 2–4: Per-chunk metadata validation ──────────────────────────────
    region_mismatches = 0
    crop_mismatches   = 0
    stage_mismatches  = 0
    unknown_authority_count = 0
    validated_count = 0

    for chunk in evidence.chunks:
        meta = chunk.metadata

        chunk_regions = [r.lower() for r in meta.get("region", [])]
        chunk_crops   = [c.lower() for c in meta.get("crop", [])]
        chunk_stage   = (meta.get("crop_stage") or "").lower()
        chunk_auth    = meta.get("issuing_authority", "unknown").lower()

        # Region check (hard)
        if region_norm and chunk_regions and region_norm not in chunk_regions:
            region_mismatches += 1

        # Crop check (hard)
        if crop_norm and chunk_crops and crop_norm not in chunk_crops:
            crop_mismatches += 1

        # Stage check (soft)
        if stage_norm and chunk_stage and stage_norm not in chunk_stage:
            stage_mismatches += 1

        # Authority check (soft)
        trusted_authorities = {"mpkv-icar", "mpkv", "icar", "icar-nrri", "fco-india", "fco"}
        if chunk_auth not in trusted_authorities and chunk_auth != "unknown":
            unknown_authority_count += 1

        validated_count += 1

    # ── Build warnings from counts ────────────────────────────────────────────
    total = len(evidence.chunks)

    if region_mismatches > 0:
        flags_added.append("REGION_MISMATCH")
        msg = (
            f"REGION_MISMATCH: {region_mismatches}/{total} chunks do not match "
            f"required region '{required_region}'. Evidence from other regions "
            "must not be used for this recommendation."
        )
        if region_mismatches == total:
            blocking_issues.append(msg)
        else:
            warnings.append(msg)

    if crop_mismatches > 0:
        flags_added.append("CROP_MISMATCH")
        msg = (
            f"CROP_MISMATCH: {crop_mismatches}/{total} chunks do not match "
            f"required crop '{required_crop}'."
        )
        if crop_mismatches == total:
            blocking_issues.append(msg)
        else:
            warnings.append(msg)

    if stage_mismatches > 0:
        flags_added.append("STAGE_MISMATCH")
        warnings.append(
            f"STAGE_MISMATCH (soft): {stage_mismatches}/{total} chunks are not "
            f"specifically for crop_stage='{required_crop_stage}'. Evidence may "
            "still be applicable at seasonal level."
        )

    if unknown_authority_count > 0:
        flags_added.append("UNTRUSTED_SOURCE")
        warnings.append(
            f"UNTRUSTED_SOURCE: {unknown_authority_count}/{total} chunks are from "
            "non-MPKV/ICAR/FCO sources. Treat with caution."
        )

    # ── Overall applicability and confidence adjustment ───────────────────────
    is_applicable = len(blocking_issues) == 0

    if not is_applicable:
        confidence_adjustment = "SEVERE_DOWNGRADE"
    elif flags_added:
        confidence_adjustment = "DOWNGRADE"
    else:
        confidence_adjustment = "NONE"

    return RAGValidationResult(
        is_applicable=is_applicable,
        confidence_adjustment=confidence_adjustment,
        warnings=warnings,
        blocking_issues=blocking_issues,
        flags_added=flags_added,
        validated_chunks_count=validated_count,
    )
