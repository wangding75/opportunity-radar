"""Versioned business contract for the daily opportunity digest.

Generation, persistence, delivery, and presentation deliberately consume this
contract instead of inventing slightly different meanings for a "daily" list.
The contract is data-only; T104-02 owns the database query and ranking logic.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta
from enum import StrEnum
from typing import Any, Iterable, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.time import as_utc_naive


DIGEST_CONTRACT_VERSION = "1"
DIGEST_ALGORITHM_VERSION = "digest-v1"
DIGEST_TIMEZONE = "UTC"
DIGEST_MAX_ITEMS = 20
DIGEST_MAX_CANDIDATES = 100
DIGEST_MAX_EVIDENCE_IDS = 100


class DigestStatus(StrEnum):
    READY = "READY"
    EMPTY = "EMPTY"
    DEGRADED = "DEGRADED"


class DigestEvidenceProvenance(StrEnum):
    OBSERVED = "OBSERVED"
    MOCK = "MOCK"
    SYNTHETIC = "SYNTHETIC"
    MIXED = "MIXED"


class DigestSelectionPolicy(BaseModel):
    """The bounded, auditable inputs to a digest ranking run."""

    model_config = ConfigDict(extra="forbid")

    policy_version: str = Field(default="digest-selection-v1", min_length=1, max_length=50)
    min_score: float = Field(default=60.0, ge=0.0, le=100.0)
    min_evidence_count: int = Field(default=1, ge=0, le=100_000)
    max_items: int = Field(default=DIGEST_MAX_ITEMS, ge=1, le=DIGEST_MAX_ITEMS)
    include_degraded_analysis: bool = True
    exclude_dormant: bool = True
    sort_order: Literal["score_desc,risk_asc,last_seen_desc,key_asc"] = "score_desc,risk_asc,last_seen_desc,key_asc"


class DigestItem(BaseModel):
    """One explainable opportunity included in a digest snapshot."""

    model_config = ConfigDict(extra="forbid")

    rank: int = Field(ge=1, le=DIGEST_MAX_ITEMS)
    opportunity_id: int = Field(ge=1)
    opportunity_key: str = Field(min_length=1, max_length=240)
    title: str = Field(min_length=1, max_length=240)
    stage: str = Field(min_length=1, max_length=40)
    score: float = Field(ge=0.0, le=100.0)
    risk_score: float = Field(ge=0.0, le=100.0)
    evidence_count: int = Field(ge=0, le=100_000)
    summary: str = Field(default="", max_length=20_000)
    analysis_status: str = Field(min_length=1, max_length=30)
    analysis_provider: str = Field(min_length=1, max_length=80)
    analysis_signature: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")
    last_seen_at: datetime
    evidence_ids: list[str] = Field(default_factory=list, max_length=DIGEST_MAX_EVIDENCE_IDS)
    evidence_provenance: DigestEvidenceProvenance
    selection_reasons: list[str] = Field(min_length=1, max_length=10)
    score_breakdown: dict[str, Any] = Field(default_factory=dict)

    @field_validator("last_seen_at", mode="before")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        if not isinstance(value, datetime):
            raise ValueError("last_seen_at must be a datetime")
        return as_utc_naive(value)

    @field_validator("evidence_ids", mode="before")
    @classmethod
    def normalize_evidence_ids(cls, value: Any) -> list[str]:
        if value is None:
            return []
        return [str(item).strip() for item in value]

    @model_validator(mode="after")
    def validate_evidence_and_reasons(self) -> "DigestItem":
        if len(self.evidence_ids) != len(set(self.evidence_ids)):
            raise ValueError("digest item evidence_ids must be unique")
        if any(not item for item in self.evidence_ids):
            raise ValueError("digest item evidence_ids must not be empty")
        if any(not reason.strip() for reason in self.selection_reasons):
            raise ValueError("digest item selection_reasons must not be empty")
        return self


class DailyDigest(BaseModel):
    """A complete daily digest snapshot, including empty and degraded states."""

    model_config = ConfigDict(extra="forbid")

    contract_version: Literal["1"] = DIGEST_CONTRACT_VERSION
    algorithm_version: str = Field(default=DIGEST_ALGORITHM_VERSION, min_length=1, max_length=50)
    digest_date: date
    timezone: Literal["UTC"] = DIGEST_TIMEZONE
    window_start: datetime
    window_end: datetime
    generated_at: datetime
    status: DigestStatus
    selection_policy: DigestSelectionPolicy
    total_candidates: int = Field(ge=0, le=DIGEST_MAX_CANDIDATES)
    selected_count: int = Field(ge=0, le=DIGEST_MAX_ITEMS)
    input_signature: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")
    items: list[DigestItem] = Field(default_factory=list, max_length=DIGEST_MAX_ITEMS)
    warnings: list[str] = Field(default_factory=list, max_length=10)
    generation_error: str | None = Field(default=None, max_length=2_000)

    @field_validator("window_start", "window_end", "generated_at", mode="before")
    @classmethod
    def normalize_timestamps(cls, value: datetime) -> datetime:
        if not isinstance(value, datetime):
            raise ValueError("digest timestamps must be datetimes")
        return as_utc_naive(value)

    @model_validator(mode="after")
    def validate_snapshot_invariants(self) -> "DailyDigest":
        if self.window_end <= self.window_start:
            raise ValueError("digest window_end must be after window_start")
        if self.window_end - self.window_start != timedelta(days=1):
            raise ValueError("daily digest window must be exactly 24 hours")
        if self.window_start.date() != self.digest_date or self.window_end.date() != self.digest_date + timedelta(days=1):
            raise ValueError("daily digest window must use the UTC calendar day")
        if self.selected_count != len(self.items):
            raise ValueError("selected_count must equal the number of digest items")
        if self.selected_count > self.total_candidates:
            raise ValueError("selected_count cannot exceed total_candidates")
        if [item.rank for item in self.items] != list(range(1, len(self.items) + 1)):
            raise ValueError("digest item ranks must be contiguous and start at 1")
        if len({item.opportunity_id for item in self.items}) != len(self.items):
            raise ValueError("digest items must not contain duplicate opportunity_id values")
        if self.status == DigestStatus.EMPTY and self.items:
            raise ValueError("EMPTY digest must not contain items")
        if self.status == DigestStatus.READY and not self.items:
            raise ValueError("READY digest must contain at least one item")
        if self.status == DigestStatus.DEGRADED and not (self.warnings or self.generation_error):
            raise ValueError("DEGRADED digest must explain the degradation")
        if self.generation_error and self.status != DigestStatus.DEGRADED:
            raise ValueError("generation_error requires DEGRADED status")
        return self


def _canonical_candidate(row: Mapping[str, Any] | DigestItem) -> dict[str, Any]:
    values = row.model_dump(mode="json") if isinstance(row, DigestItem) else row
    return {
        "opportunity_id": values.get("opportunity_id"),
        "opportunity_key": values.get("opportunity_key"),
        "score": values.get("score"),
        "risk_score": values.get("risk_score"),
        "evidence_count": values.get("evidence_count"),
        "analysis_status": values.get("analysis_status"),
        "analysis_provider": values.get("analysis_provider"),
        "analysis_signature": values.get("analysis_signature"),
        "last_seen_at": values.get("last_seen_at"),
        "evidence_ids": sorted(str(item) for item in (values.get("evidence_ids") or [])),
        "evidence_provenance": values.get("evidence_provenance"),
    }


def build_digest_input_signature(
    *,
    digest_date: date,
    window_start: datetime,
    window_end: datetime,
    candidates: Iterable[Mapping[str, Any] | DigestItem],
    selection_policy: DigestSelectionPolicy,
) -> str:
    """Build a stable signature over bounded candidate meaning, not DB row order."""

    canonical_candidates = sorted(
        (_canonical_candidate(row) for row in candidates),
        key=lambda row: (str(row["opportunity_key"] or ""), int(row["opportunity_id"] or 0)),
    )
    payload = {
        "contract_version": DIGEST_CONTRACT_VERSION,
        "digest_date": digest_date.isoformat(),
        "window_start": as_utc_naive(window_start).isoformat(),
        "window_end": as_utc_naive(window_end).isoformat(),
        "selection_policy": selection_policy.model_dump(mode="json"),
        "candidates": canonical_candidates,
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
