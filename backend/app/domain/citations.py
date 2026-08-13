from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime
from enum import StrEnum
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator


CITATION_CONTRACT_VERSION = "1"
EVIDENCE_ID_ALGORITHM = "sha256-content-hash-v1"
EVIDENCE_ID_PREFIX = "ev1_"
_EVIDENCE_ID_RE = re.compile(r"^ev1_[0-9a-f]{64}$")
_CONTENT_HASH_RE = re.compile(r"^[0-9a-fA-F]{64}$")


class CitationProvenance(StrEnum):
    OBSERVED = "OBSERVED"
    MOCK = "MOCK"
    SYNTHETIC = "SYNTHETIC"


class EvidenceCitation(BaseModel):
    """The versioned, provider-facing representation of one evidence item.

    Database primary keys are deliberately absent from this contract.  A citation
    must remain resolvable when an observation is reloaded into another database.
    """

    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(min_length=68, max_length=68, pattern=r"^ev1_[0-9a-f]{64}$")
    source: str = Field(min_length=1, max_length=100)
    type: str = Field(min_length=1, max_length=40)
    item_type: str = Field(min_length=1, max_length=50)
    quality: str = Field(min_length=1, max_length=8)
    acquisition_method: str = Field(min_length=1, max_length=50)
    title: str = Field(default="", max_length=20_000)
    text: str = Field(default="", max_length=200_000)
    url: str | None = Field(default=None, max_length=10_000)
    observed_at: datetime
    provenance: CitationProvenance = CitationProvenance.OBSERVED

    @field_validator("source", "type", "item_type", "quality", "acquisition_method", mode="before")
    @classmethod
    def strip_required_text(cls, value: Any) -> str:
        value = str(value or "").strip()
        if not value:
            raise ValueError("citation field must not be empty")
        return value

    @field_validator("title", "text", mode="before")
    @classmethod
    def coerce_text(cls, value: Any) -> str:
        return str(value or "")

    @field_validator("url", mode="before")
    @classmethod
    def coerce_url(cls, value: Any) -> str | None:
        if value is None:
            return None
        value = str(value).strip()
        return value or None


class AnalysisCitation(BaseModel):
    """One provider claim bound to an evidence ID from the request."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(min_length=68, max_length=68, pattern=r"^ev1_[0-9a-f]{64}$")
    claim: str = Field(min_length=1, max_length=2_000)

    @field_validator("claim", mode="before")
    @classmethod
    def strip_claim(cls, value: Any) -> str:
        value = str(value or "").strip()
        if not value:
            raise ValueError("citation claim must not be empty")
        return value


def evidence_id_for_content_hash(content_hash: str) -> str:
    """Return the stable public evidence ID for an ingestion content hash.

    ``RawObservation.id`` and ``NormalizedItem.id`` are database-local and are
    therefore not valid citation identities.  The unique ingestion
    ``content_hash`` is the immutable identity input for contract version 1.
    """

    digest = str(content_hash or "").strip().lower()
    if not _CONTENT_HASH_RE.fullmatch(digest):
        raise ValueError("content_hash must be a 64-character hexadecimal SHA-256 digest")
    return f"{EVIDENCE_ID_PREFIX}{digest}"


def validate_evidence_id(evidence_id: str) -> str:
    value = str(evidence_id or "").strip()
    if not _EVIDENCE_ID_RE.fullmatch(value):
        raise ValueError("evidence_id must match ev1_<64 lowercase hex characters>")
    return value


def validate_analysis_citations(
    citations: Any,
    *,
    allowed_evidence_ids: set[str],
) -> list[dict[str, str]]:
    """Validate provider output and bind every citation to request evidence."""

    if not isinstance(citations, list):
        raise ValueError("citations must be a JSON array")
    if len(citations) > 100:
        raise ValueError("citations exceeds 100 item limit")
    if allowed_evidence_ids and not citations:
        raise ValueError("citations must not be empty when evidence is provided")

    normalized: list[dict[str, str]] = []
    seen: set[str] = set()
    for raw in citations:
        try:
            citation = AnalysisCitation.model_validate(raw)
        except Exception as exc:
            raise ValueError(f"invalid citation item: {exc}") from exc
        evidence_id = validate_evidence_id(citation.evidence_id)
        if evidence_id not in allowed_evidence_ids:
            raise ValueError(f"citation references unknown evidence_id: {evidence_id}")
        if evidence_id in seen:
            raise ValueError(f"citation references duplicate evidence_id: {evidence_id}")
        seen.add(evidence_id)
        normalized.append({"evidence_id": evidence_id, "claim": citation.claim})
    return normalized


def _json_safe(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return value


def evidence_id_for_row(row: Mapping[str, Any]) -> str:
    """Get or deterministically derive an ID for an analysis evidence row.

    Production rows always carry the ingestion-derived ID.  The deterministic
    fallback keeps the provider contract usable for standalone adapter tests and
    migration tooling that has not loaded a RawObservation object yet.
    """

    supplied = row.get("evidence_id")
    if supplied:
        return validate_evidence_id(str(supplied))
    stable = {
        "source": row.get("source") or row.get("source_id"),
        "type": row.get("type") or row.get("evidence_type"),
        "item_type": row.get("item_type"),
        "quality": row.get("quality") or row.get("evidence_quality"),
        "acquisition_method": row.get("acquisition_method"),
        "title": row.get("title", ""),
        "text": row.get("text", ""),
        "url": row.get("url") or row.get("source_url"),
        "observed_at": row.get("observed_at"),
        "provenance": row.get("provenance", CitationProvenance.OBSERVED),
    }
    digest = hashlib.sha256(
        json.dumps(_json_safe(stable), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return evidence_id_for_content_hash(digest)


def provenance_from_payload(payload: Mapping[str, Any] | None) -> CitationProvenance:
    """Read an explicit MOCK/SYNTHETIC marker without treating it as real data."""

    payload = payload or {}
    for key in ("_provenance", "provenance", "_data_class", "data_class"):
        marker = payload.get(key)
        if isinstance(marker, str):
            normalized = marker.strip().upper()
            if normalized in CitationProvenance.__members__:
                return CitationProvenance[normalized]
    return CitationProvenance.OBSERVED
