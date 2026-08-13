"""Versioned contract for identifying new tools and products from evidence."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.time import as_utc_naive, utc_now
from app.domain.citations import CitationProvenance, validate_evidence_id


TOOL_PRODUCT_CONTRACT_VERSION = "1"
TOOL_PRODUCT_ALGORITHM_VERSION = "tool-product-identification-v1"
TOOL_PRODUCT_ID_PREFIX = "tp1_"
TOOL_PRODUCT_MAX_EVIDENCE = 20
_NAME_TOKEN_RE = re.compile(r"[^\w]+", re.UNICODE)


class ToolProductKind(StrEnum):
    TOOL = "TOOL"
    PRODUCT = "PRODUCT"
    SERVICE = "SERVICE"
    UNKNOWN = "UNKNOWN"


class ToolProductStatus(StrEnum):
    IDENTIFIED = "IDENTIFIED"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    UNRESOLVED = "UNRESOLVED"


class ToolProductEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(min_length=68, max_length=68, pattern=r"^ev1_[0-9a-f]{64}$")
    source: str = Field(min_length=1, max_length=100)
    title: str = Field(default="", max_length=500)
    text: str = Field(default="", max_length=2_000)
    item_type: str = Field(default="CONTENT", min_length=1, max_length=50)
    observed_at: datetime
    provenance: CitationProvenance = CitationProvenance.OBSERVED
    source_url: str | None = Field(default=None, max_length=2_000)

    @field_validator("evidence_id", mode="before")
    @classmethod
    def normalize_evidence_id(cls, value: Any) -> str:
        return validate_evidence_id(str(value))

    @field_validator("source", "title", "text", "item_type", mode="before")
    @classmethod
    def normalize_text(cls, value: Any) -> str:
        return str(value or "").strip()

    @field_validator("observed_at", mode="before")
    @classmethod
    def normalize_timestamp(cls, value: datetime | str) -> datetime:
        if isinstance(value, str):
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if not isinstance(value, datetime):
            raise ValueError("observed_at must be a datetime")
        return as_utc_naive(value)


class ToolProductIdentificationPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_version: str = Field(default="tool-product-policy-v1", min_length=1, max_length=50)
    min_evidence_count: int = Field(default=2, ge=1, le=TOOL_PRODUCT_MAX_EVIDENCE)
    min_source_count: int = Field(default=1, ge=1, le=100)
    min_confidence: float = Field(default=0.65, ge=0.0, le=1.0)
    max_evidence: int = Field(default=TOOL_PRODUCT_MAX_EVIDENCE, ge=1, le=TOOL_PRODUCT_MAX_EVIDENCE)
    tool_terms: list[str] = Field(default_factory=lambda: ["tool", "software", "app", "platform", "工具", "软件", "应用", "平台"], max_length=50)
    product_terms: list[str] = Field(default_factory=lambda: ["product", "productized", "产品", "产品化", "saas"], max_length=50)
    service_terms: list[str] = Field(default_factory=lambda: ["service", "服务", "api", "consulting", "咨询"], max_length=50)

    @field_validator("tool_terms", "product_terms", "service_terms")
    @classmethod
    def normalize_terms(cls, values: list[str]) -> list[str]:
        normalized = [str(value).strip().casefold() for value in values if str(value).strip()]
        return list(dict.fromkeys(normalized))


class ToolProductIdentificationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_name: str = Field(default="", max_length=300)
    claimed_kind: ToolProductKind | None = None
    evidence: list[ToolProductEvidence] = Field(default_factory=list, max_length=TOOL_PRODUCT_MAX_EVIDENCE)


class ToolProductIdentificationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_version: str = TOOL_PRODUCT_CONTRACT_VERSION
    algorithm_version: str = TOOL_PRODUCT_ALGORITHM_VERSION
    policy: ToolProductIdentificationPolicy
    status: ToolProductStatus
    entity_key: str | None = Field(default=None, pattern=r"^tp1_[0-9a-f]{64}$")
    display_name: str | None = Field(default=None, max_length=300)
    kind: ToolProductKind
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_count: int = Field(ge=0, le=TOOL_PRODUCT_MAX_EVIDENCE)
    deduplicated_count: int = Field(ge=0, le=TOOL_PRODUCT_MAX_EVIDENCE)
    source_count: int = Field(ge=0, le=100)
    evidence_ids: list[str] = Field(default_factory=list, max_length=TOOL_PRODUCT_MAX_EVIDENCE)
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    reasons: list[str] = Field(min_length=1, max_length=12)
    input_signature: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")
    evaluated_at: datetime

    @model_validator(mode="after")
    def validate_state(self) -> "ToolProductIdentificationResult":
        if self.status == ToolProductStatus.IDENTIFIED:
            if not self.entity_key or not self.display_name or self.kind == ToolProductKind.UNKNOWN:
                raise ValueError("IDENTIFIED result requires an entity key, name, and known kind")
            if self.confidence < self.policy.min_confidence:
                raise ValueError("IDENTIFIED result must meet min_confidence")
        if self.status in {ToolProductStatus.INSUFFICIENT_EVIDENCE, ToolProductStatus.UNRESOLVED} and self.entity_key is not None:
            raise ValueError("unresolved result must not fabricate an entity key")
        if self.first_seen_at and self.last_seen_at and self.first_seen_at > self.last_seen_at:
            raise ValueError("first_seen_at must not be after last_seen_at")
        return self


def normalize_tool_product_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", str(value or "")).casefold().strip()
    normalized = _NAME_TOKEN_RE.sub(" ", normalized)
    return " ".join(normalized.split())


def tool_product_entity_key(name: str, kind: ToolProductKind) -> str:
    normalized = normalize_tool_product_name(name)
    if not normalized or kind == ToolProductKind.UNKNOWN:
        raise ValueError("a non-empty name and known kind are required for an entity key")
    return TOOL_PRODUCT_ID_PREFIX + hashlib.sha256(f"{kind.value}|{normalized}".encode("utf-8")).hexdigest()


def _input_signature(input: ToolProductIdentificationInput, policy: ToolProductIdentificationPolicy, evidence: list[ToolProductEvidence]) -> str:
    payload = {
        "contract_version": TOOL_PRODUCT_CONTRACT_VERSION,
        "algorithm_version": TOOL_PRODUCT_ALGORITHM_VERSION,
        "policy": policy.model_dump(mode="json"),
        "candidate_name": normalize_tool_product_name(input.candidate_name),
        "claimed_kind": input.claimed_kind.value if input.claimed_kind else None,
        "evidence": [row.model_dump(mode="json") for row in evidence],
    }
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _classify_kind(input: ToolProductIdentificationInput, policy: ToolProductIdentificationPolicy, text: str) -> ToolProductKind:
    if input.claimed_kind and input.claimed_kind != ToolProductKind.UNKNOWN:
        return input.claimed_kind
    scores = {
        ToolProductKind.TOOL: sum(1 for term in policy.tool_terms if term in text),
        ToolProductKind.PRODUCT: sum(1 for term in policy.product_terms if term in text),
        ToolProductKind.SERVICE: sum(1 for term in policy.service_terms if term in text),
    }
    best = max(scores.values(), default=0)
    winners = [kind for kind, score in scores.items() if score == best and score > 0]
    return winners[0] if len(winners) == 1 else ToolProductKind.UNKNOWN


def identify_tool_product(
    input: ToolProductIdentificationInput,
    *,
    policy: ToolProductIdentificationPolicy | None = None,
    evaluated_at: datetime | None = None,
) -> ToolProductIdentificationResult:
    """Produce a traceable identification decision without inventing evidence."""

    policy = policy or ToolProductIdentificationPolicy()
    seen: set[str] = set()
    evidence: list[ToolProductEvidence] = []
    for row in input.evidence[: policy.max_evidence]:
        if row.evidence_id not in seen:
            seen.add(row.evidence_id)
            evidence.append(row)
    evidence.sort(key=lambda row: (row.observed_at, row.evidence_id))
    name = str(input.candidate_name or "").strip()
    if not name and evidence:
        name = evidence[0].title.strip()
    text = " ".join([name, *[f"{row.title} {row.text}" for row in evidence]]).casefold()
    kind = _classify_kind(input, policy, text)
    source_count = len({row.source for row in evidence})
    # Confidence rewards corroboration from a second source even when the
    # policy permits a one-source provisional identification.
    source_support = min(1.0, source_count / 2.0)
    confidence = min(1.0, 0.35 * min(1.0, len(evidence) / max(policy.min_evidence_count, 1)) + 0.35 * source_support + 0.30 * (1.0 if kind != ToolProductKind.UNKNOWN else 0.0))
    reasons = [f"deduplicated evidence count={len(evidence)}", f"distinct source count={source_count}"]
    status = ToolProductStatus.IDENTIFIED
    if not evidence or len(evidence) < policy.min_evidence_count or source_count < policy.min_source_count:
        status = ToolProductStatus.INSUFFICIENT_EVIDENCE
        reasons.append(f"evidence/source minimums require {policy.min_evidence_count}/{policy.min_source_count}")
    elif not name or kind == ToolProductKind.UNKNOWN:
        status = ToolProductStatus.UNRESOLVED
        reasons.append("candidate name or kind could not be resolved")
    elif confidence < policy.min_confidence:
        status = ToolProductStatus.LOW_CONFIDENCE
        reasons.append(f"confidence {confidence:.3f} is below {policy.min_confidence:.3f}")
    else:
        reasons.append(f"confidence {confidence:.3f} meets {policy.min_confidence:.3f}")
    entity_key = tool_product_entity_key(name, kind) if status in {ToolProductStatus.IDENTIFIED, ToolProductStatus.LOW_CONFIDENCE} and name and kind != ToolProductKind.UNKNOWN else None
    return ToolProductIdentificationResult(
        policy=policy,
        status=status,
        entity_key=entity_key,
        display_name=name or None,
        kind=kind,
        confidence=round(confidence, 6),
        evidence_count=len(evidence),
        deduplicated_count=len(input.evidence) - len(evidence),
        source_count=source_count,
        evidence_ids=[row.evidence_id for row in evidence],
        first_seen_at=evidence[0].observed_at if evidence else None,
        last_seen_at=evidence[-1].observed_at if evidence else None,
        reasons=reasons,
        input_signature=_input_signature(input, policy, evidence),
        evaluated_at=as_utc_naive(evaluated_at or utc_now()),
    )
