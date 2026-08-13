from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
import json

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.time import utc_now
from .enums import AcquisitionMethod, AcquisitionRisk, Capability, EvidenceQuality, ItemType, QueryMode

MAX_OBSERVATION_BYTES = 512 * 1024
MAX_IMPORT_REQUEST_BYTES = 20 * 1024 * 1024
MAX_PAYLOAD_DEPTH = 32
MAX_PAYLOAD_NODES = 20_000


def observation_size_bytes(value: Any) -> int:
    payload = getattr(value, "payload", {}) or {}
    payload_bytes = len(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str).encode("utf-8"))
    text_bytes = sum(
        len(str(getattr(value, field, "") or "").encode("utf-8"))
        for field in ("source_id", "query", "external_id", "title", "text", "url")
    )
    return payload_bytes + text_bytes


def _validate_payload_structure(payload: dict[str, Any]) -> None:
    stack: list[tuple[Any, int]] = [(payload, 0)]
    nodes = 0
    while stack:
        current, depth = stack.pop()
        nodes += 1
        if nodes > MAX_PAYLOAD_NODES:
            raise ValueError(f"payload exceeds {MAX_PAYLOAD_NODES} node limit")
        if depth > MAX_PAYLOAD_DEPTH:
            raise ValueError(f"payload exceeds {MAX_PAYLOAD_DEPTH} level depth limit")
        if isinstance(current, dict):
            stack.extend((value, depth + 1) for value in current.values())
        elif isinstance(current, list):
            stack.extend((value, depth + 1) for value in current)


def _validate_observation_size(value: Any) -> None:
    payload = getattr(value, "payload", {}) or {}
    _validate_payload_structure(payload)
    try:
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    except (TypeError, ValueError) as exc:
        raise ValueError("payload must contain only JSON-serializable values") from exc
    size = observation_size_bytes(value)
    if size > MAX_OBSERVATION_BYTES:
        raise ValueError(f"observation exceeds {MAX_OBSERVATION_BYTES} byte limit")


class CollectorQuery(BaseModel):
    query: str = Field(min_length=1, max_length=200)
    limit: int = Field(default=20, ge=1, le=100)
    cursor: str | None = Field(default=None, max_length=500)


class CollectedRecord(BaseModel):
    external_id: str | None = Field(default=None, max_length=300)
    item_type: ItemType = ItemType.CONTENT
    title: str = Field(default="", max_length=20_000)
    text: str = Field(default="", max_length=200_000)
    url: str | None = Field(default=None, max_length=10_000)
    observed_at: datetime = Field(default_factory=utc_now)
    payload: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_size(self):
        _validate_observation_size(self)
        return self


class CollectionResult(BaseModel):
    source_id: str = Field(min_length=1, max_length=100)
    query: str = Field(min_length=1, max_length=300)
    records: list[CollectedRecord] = Field(max_length=100)
    next_cursor: str | None = Field(default=None, max_length=500)


class SourceDescriptor(BaseModel):
    source_id: str = Field(min_length=1, max_length=100)
    display_name: str = Field(min_length=1, max_length=200)
    acquisition_method: AcquisitionMethod
    evidence_quality: EvidenceQuality
    acquisition_risk: AcquisitionRisk
    capabilities: set[Capability]
    query_mode: QueryMode = QueryMode.KEYWORD
    enabled: bool = True


class ImportRecord(BaseModel):
    source_id: str = Field(default="manual_import", min_length=1, max_length=100)
    query: str = Field(min_length=1, max_length=300)
    external_id: str | None = Field(default=None, max_length=300)
    item_type: ItemType = ItemType.CONTENT
    title: str = Field(default="", max_length=20_000)
    text: str = Field(default="", max_length=200_000)
    url: str | None = Field(default=None, max_length=10_000)
    observed_at: datetime | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    acquisition_method: AcquisitionMethod = AcquisitionMethod.MANUAL_IMPORT
    evidence_quality: EvidenceQuality = EvidenceQuality.C
    acquisition_risk: AcquisitionRisk = AcquisitionRisk.R2

    @model_validator(mode="after")
    def validate_import_provenance(self):
        if self.acquisition_method in {AcquisitionMethod.OFFICIAL_API, AcquisitionMethod.INSTRUMENTED_APP}:
            raise ValueError("OFFICIAL_API and INSTRUMENTED_APP must use dedicated connectors/endpoints")
        if self.evidence_quality == EvidenceQuality.A:
            raise ValueError("EvidenceQuality.A is reserved for official API connectors")
        if self.acquisition_method == AcquisitionMethod.OFFICIAL_EXPORT and self.evidence_quality != EvidenceQuality.B:
            raise ValueError("OFFICIAL_EXPORT imports must use EvidenceQuality.B")
        _validate_observation_size(self)
        return self


class ImportRequest(BaseModel):
    records: list[ImportRecord] = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def validate_aggregate_size(self):
        total = sum(observation_size_bytes(record) for record in self.records)
        if total > MAX_IMPORT_REQUEST_BYTES:
            raise ValueError(f"import request exceeds {MAX_IMPORT_REQUEST_BYTES} byte limit")
        return self


class InstrumentedAppObservation(BaseModel):
    source_id: str = Field(min_length=1, max_length=100)
    query: str = Field(min_length=1, max_length=300)
    app_package: str = Field(min_length=1, max_length=300)
    app_version: str | None = Field(default=None, max_length=100)
    emulator_profile: str | None = Field(default=None, max_length=200)
    instrumentation_version: str | None = Field(default=None, max_length=100)
    session_id: str | None = Field(default=None, max_length=200)
    external_id: str | None = Field(default=None, max_length=300)
    item_type: ItemType = ItemType.APP_OBSERVATION
    title: str = Field(default="", max_length=20_000)
    text: str = Field(default="", max_length=200_000)
    url: str | None = Field(default=None, max_length=10_000)
    observed_at: datetime | None = None
    payload: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_size(self):
        _validate_observation_size(self)
        return self


class OpportunityResearchPatch(BaseModel):
    status: str | None = Field(default=None, max_length=30)
    starred: bool | None = None
    priority: int | None = Field(default=None, ge=0, le=5)
    notes: str | None = Field(default=None, max_length=50_000)
    tags: list[str] | None = Field(default=None, max_length=30)


class AlertRuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    enabled: bool = True
    min_score: float = Field(default=60.0, ge=0, le=100)
    max_risk_score: float = Field(default=100.0, ge=0, le=100)
    min_evidence_count: int = Field(default=2, ge=1, le=10_000)
    stages: list[str] = Field(default_factory=list, max_length=20)
    keyword_contains: list[str] = Field(default_factory=list, max_length=30)
    cooldown_minutes: int = Field(default=1440, ge=1, le=525_600)


class AlertRulePatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    enabled: bool | None = None
    min_score: float | None = Field(default=None, ge=0, le=100)
    max_risk_score: float | None = Field(default=None, ge=0, le=100)
    min_evidence_count: int | None = Field(default=None, ge=1, le=10_000)
    stages: list[str] | None = Field(default=None, max_length=20)
    keyword_contains: list[str] | None = Field(default=None, max_length=30)
    cooldown_minutes: int | None = Field(default=None, ge=1, le=525_600)


class AlertEventStatusPatch(BaseModel):
    status: Literal["NEW", "ACKNOWLEDGED", "DISMISSED", "RESOLVED"]

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value: object) -> object:
        return value.strip().upper() if isinstance(value, str) else value


class EmailDeliveryEnqueueRequest(BaseModel):
    alert_event_ids: list[int] | None = Field(default=None, max_length=500)
    recipients: list[str] = Field(min_length=1, max_length=50)
    data_class: Literal["ALERT_EVENT", "OBSERVED", "MOCK", "SYNTHETIC"] = "ALERT_EVENT"
    limit: int = Field(default=100, ge=1, le=500)


class EmailDeliveryProcessRequest(BaseModel):
    limit: int = Field(default=100, ge=1, le=500)


class WebhookDeliveryEnqueueRequest(BaseModel):
    alert_event_ids: list[int] | None = Field(default=None, max_length=500)
    endpoint_ids: list[int] | None = Field(default=None, max_length=500)
    data_class: Literal["ALERT_EVENT", "OBSERVED", "MOCK", "SYNTHETIC"] = "ALERT_EVENT"
    limit: int = Field(default=100, ge=1, le=500)


class WebhookDeliveryProcessRequest(BaseModel):
    limit: int = Field(default=100, ge=1, le=500)


class SourcePreferencePatch(BaseModel):
    enabled: bool
    note: str = Field(default="", max_length=10_000)


class WatchKeywordCreate(BaseModel):
    keyword: str = Field(min_length=2, max_length=200)
    priority: int = Field(default=3, ge=0, le=5)
    notes: str = Field(default="", max_length=10_000)


class WatchKeywordPatch(BaseModel):
    enabled: bool | None = None
    priority: int | None = Field(default=None, ge=0, le=5)
    notes: str | None = Field(default=None, max_length=10_000)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=500)


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=12, max_length=500)
    role: str = Field(default="VIEWER", max_length=30)
    enabled: bool = True


class UserPatch(BaseModel):
    role: str | None = Field(default=None, max_length=30)
    enabled: bool | None = None
    password: str | None = Field(default=None, min_length=12, max_length=500)


class ApiTokenCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    scopes: list[str] = Field(default_factory=lambda: ["read"], min_length=1, max_length=3)
    expires_in_days: int | None = Field(default=None, ge=1, le=3650)
