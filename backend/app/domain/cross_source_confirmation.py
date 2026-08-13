"""Versioned contract for conservative cross-source confirmation."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import datetime, timedelta
from enum import StrEnum
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.time import as_utc_naive, utc_now
from app.domain.citations import CitationProvenance, validate_evidence_id

CROSS_SOURCE_CONFIRMATION_CONTRACT_VERSION = "1"
CROSS_SOURCE_CONFIRMATION_ALGORITHM_VERSION = "cross-source-confirmation-v1"
CROSS_SOURCE_MAX_EVIDENCE = 100
_SPACE_RE = re.compile(r"\s+")
_SOURCE_RE = re.compile(r"[^a-z0-9]+")


class ConfirmationStatus(StrEnum):
    CONFIRMED = "CONFIRMED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    NO_EVIDENCE = "NO_EVIDENCE"


class CrossSourceConfirmationPolicy(BaseModel):
    """Explicit thresholds for one bounded source-independence decision."""

    model_config = ConfigDict(extra="forbid")

    policy_version: str = Field(default="cross-source-confirmation-policy-v1", min_length=1, max_length=50)
    min_independent_sources: int = Field(default=2, ge=1, le=100)
    min_unique_claims: int = Field(default=2, ge=1, le=100)
    max_evidence: int = Field(default=50, ge=1, le=CROSS_SOURCE_MAX_EVIDENCE)
    max_age_hours: int = Field(default=24 * 30, ge=1, le=24 * 365)


class CrossSourceEvidence(BaseModel):
    """One evidence item whose source endpoint can be independently grouped."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(min_length=68, max_length=68, pattern=r"^ev1_[0-9a-f]{64}$")
    source_id: str = Field(min_length=1, max_length=100)
    title: str = Field(default="", max_length=20_000)
    text: str = Field(default="", max_length=200_000)
    url: str | None = Field(default=None, max_length=10_000)
    observed_at: datetime
    provenance: CitationProvenance = CitationProvenance.OBSERVED

    @field_validator("evidence_id", mode="before")
    @classmethod
    def normalize_evidence_id(cls, value: str) -> str:
        return validate_evidence_id(str(value))

    @field_validator("source_id", mode="before")
    @classmethod
    def normalize_source_id(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("source_id must not be empty")
        return normalized

    @field_validator("title", "text", mode="before")
    @classmethod
    def normalize_text(cls, value: object) -> str:
        return str(value or "")

    @field_validator("observed_at", mode="before")
    @classmethod
    def normalize_observed_at(cls, value: datetime | str) -> datetime:
        if isinstance(value, str):
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if not isinstance(value, datetime):
            raise ValueError("observed_at must be a datetime")
        return as_utc_naive(value)


class CrossSourceConfirmationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject_key: str = Field(min_length=1, max_length=300)
    evidence: list[CrossSourceEvidence] = Field(default_factory=list, max_length=CROSS_SOURCE_MAX_EVIDENCE)


class CrossSourceConfirmationEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_version: str = CROSS_SOURCE_CONFIRMATION_CONTRACT_VERSION
    algorithm_version: str = CROSS_SOURCE_CONFIRMATION_ALGORITHM_VERSION
    evaluated_at: datetime
    subject_key: str = Field(min_length=1, max_length=300)
    policy: CrossSourceConfirmationPolicy
    status: ConfirmationStatus
    confirmed: bool
    input_evidence_count: int = Field(ge=0)
    fresh_evidence_count: int = Field(ge=0)
    deduplicated_evidence_count: int = Field(ge=0)
    stale_evidence_count: int = Field(ge=0)
    future_evidence_count: int = Field(ge=0)
    independent_source_count: int = Field(ge=0)
    unique_claim_count: int = Field(ge=0)
    source_endpoints: list[str] = Field(default_factory=list, max_length=100)
    evidence_ids: list[str] = Field(default_factory=list, max_length=CROSS_SOURCE_MAX_EVIDENCE)
    claim_fingerprints: list[str] = Field(default_factory=list, max_length=CROSS_SOURCE_MAX_EVIDENCE)
    conflict_count: int = Field(ge=0, le=100)
    conflict_groups: list[str] = Field(default_factory=list, max_length=100)
    reasons: list[str] = Field(default_factory=list, min_length=1, max_length=20)
    input_signature: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")


def _stable_text(value: object) -> str:
    normalized = unicodedata.normalize("NFKC", str(value or "")).casefold().strip()
    return _SPACE_RE.sub(" ", normalized)


def source_endpoint_key(source_id: str, url: str | None = None) -> str:
    """Return the conservative independent endpoint identity.

    A hostname is preferred over a URL path, so multiple pages on one provider
    remain one source. If no valid hostname exists, the normalized source ID is
    used. This intentionally under-counts independence when identity is unclear.
    """

    normalized_source = _SOURCE_RE.sub("-", _stable_text(source_id)).strip("-") or "unknown"
    raw_url = str(url or "").strip()
    if raw_url:
        try:
            parsed = urlsplit(raw_url if "://" in raw_url else f"https://{raw_url}")
            hostname = (parsed.hostname or "").casefold().rstrip(".")
            if hostname.startswith("www."):
                hostname = hostname[4:]
            if hostname:
                return f"host:{hostname}"
        except ValueError:
            # Keep the explicit source fallback when a malformed URL cannot
            # provide a stable host identity; never silently discard the error
            # path as a successful independent source.
            hostname = ""
    return f"source:{normalized_source}"


def claim_fingerprint(evidence: CrossSourceEvidence) -> str:
    """Hash claim text without source or URL so syndicated copies collapse."""

    payload = {"title": _stable_text(evidence.title), "text": _stable_text(evidence.text)}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _input_signature(
    input: CrossSourceConfirmationInput,
    policy: CrossSourceConfirmationPolicy,
    *,
    evidence: list[CrossSourceEvidence],
    source_endpoints: list[str],
    claim_fingerprints: list[str],
) -> str:
    payload = {
        "contract_version": CROSS_SOURCE_CONFIRMATION_CONTRACT_VERSION,
        "algorithm_version": CROSS_SOURCE_CONFIRMATION_ALGORITHM_VERSION,
        "policy": policy.model_dump(mode="json"),
        "subject_key": input.subject_key,
        "evidence": [
            {"evidence_id": row.evidence_id, "observed_at": row.observed_at.isoformat(), "claim": claim_fingerprint(row)}
            for row in evidence
        ],
        "source_endpoints": source_endpoints,
        "claim_fingerprints": claim_fingerprints,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def evaluate_cross_source_confirmation(
    input: CrossSourceConfirmationInput,
    *,
    policy: CrossSourceConfirmationPolicy | None = None,
    evaluated_at: datetime | None = None,
) -> CrossSourceConfirmationEvaluation:
    """Evaluate fresh, de-duplicated evidence and fail closed on ambiguity."""

    policy = policy or CrossSourceConfirmationPolicy()
    now = as_utc_naive(evaluated_at or utc_now())
    if len(input.evidence) > policy.max_evidence:
        raise ValueError(f"evidence exceeds policy max_evidence={policy.max_evidence}")
    cutoff = now - timedelta(hours=policy.max_age_hours)
    fresh: list[CrossSourceEvidence] = []
    stale = 0
    future = 0
    for evidence in input.evidence:
        if evidence.observed_at > now:
            future += 1
        elif evidence.observed_at < cutoff:
            stale += 1
        else:
            fresh.append(evidence)

    by_evidence_id: dict[str, CrossSourceEvidence] = {}
    for evidence in sorted(fresh, key=lambda row: (row.observed_at, row.evidence_id), reverse=True):
        by_evidence_id.setdefault(evidence.evidence_id, evidence)
    exact_deduplicated = list(by_evidence_id.values())
    by_claim: dict[str, CrossSourceEvidence] = {}
    for evidence in exact_deduplicated:
        by_claim.setdefault(claim_fingerprint(evidence), evidence)
    representatives = list(by_claim.values())
    source_endpoints = sorted({source_endpoint_key(row.source_id, row.url) for row in exact_deduplicated})
    claim_fingerprints = sorted(by_claim)
    title_claims: dict[str, set[str]] = {}
    title_endpoints: dict[str, set[str]] = {}
    for evidence in exact_deduplicated:
        title = _stable_text(evidence.title)
        if not title:
            continue
        title_claims.setdefault(title, set()).add(_stable_text(evidence.text))
        title_endpoints.setdefault(title, set()).add(source_endpoint_key(evidence.source_id, evidence.url))
    conflict_groups = sorted(title for title, claims in title_claims.items() if len(claims) > 1 and len(title_endpoints.get(title, set())) > 1)
    deduplicated_count = len(input.evidence) - len(representatives) - stale - future
    if not fresh:
        status = ConfirmationStatus.NO_EVIDENCE
        confirmed = False
        reasons = ["no fresh evidence remains after time-bound filtering"]
    else:
        confirmed = not conflict_groups and len(source_endpoints) >= policy.min_independent_sources and len(claim_fingerprints) >= policy.min_unique_claims
        status = ConfirmationStatus.CONFIRMED if confirmed else ConfirmationStatus.INSUFFICIENT_EVIDENCE
        reasons = [
            f"independent source endpoints {len(source_endpoints)} / {policy.min_independent_sources}",
            f"unique claims {len(claim_fingerprints)} / {policy.min_unique_claims}",
        ]
        if stale:
            reasons.append(f"excluded stale evidence count={stale}")
        if future:
            reasons.append(f"excluded future evidence count={future}")
        if conflict_groups:
            reasons.append(f"conflicting claim groups={','.join(conflict_groups[:5])}")
        if confirmed:
            reasons.append("fresh claims are supported by independent source endpoints")
    signature = _input_signature(
        input,
        policy,
        evidence=representatives,
        source_endpoints=source_endpoints,
        claim_fingerprints=claim_fingerprints,
    )
    return CrossSourceConfirmationEvaluation(
        evaluated_at=now,
        subject_key=input.subject_key,
        policy=policy,
        status=status,
        confirmed=confirmed,
        input_evidence_count=len(input.evidence),
        fresh_evidence_count=len(fresh),
        deduplicated_evidence_count=max(0, deduplicated_count),
        stale_evidence_count=stale,
        future_evidence_count=future,
        independent_source_count=len(source_endpoints),
        unique_claim_count=len(claim_fingerprints),
        source_endpoints=source_endpoints,
        evidence_ids=[row.evidence_id for row in representatives],
        claim_fingerprints=claim_fingerprints,
        conflict_count=len(conflict_groups),
        conflict_groups=conflict_groups,
        reasons=reasons,
        input_signature=signature,
    )
