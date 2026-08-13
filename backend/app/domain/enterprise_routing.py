"""Versioned templates and deterministic routing/fallback policy for enterprise messages."""

from __future__ import annotations

import re
from datetime import datetime
from enum import StrEnum
from string import Template
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.time import as_utc_naive, utc_now
from app.domain.enterprise_messaging import (
    EnterpriseMessageFailureKind,
    EnterpriseMessageRequest,
    EnterpriseMessageResult,
    EnterpriseMessageStatus,
)

ENTERPRISE_TEMPLATE_CONTRACT_VERSION = "enterprise-message-template-v1"
_ROUTE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")


class EnterpriseRoutingStatus(StrEnum):
    SENT = "SENT"
    DEGRADED = "DEGRADED"
    RETRYABLE = "RETRYABLE"
    FAILED = "FAILED"
    SUPPRESSED = "SUPPRESSED"
    INVALID = "INVALID"
    NO_ROUTE = "NO_ROUTE"


class EnterpriseMessageTemplate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_version: str = ENTERPRISE_TEMPLATE_CONTRACT_VERSION
    name: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9][a-z0-9._-]{0,99}$")
    version: str = Field(min_length=1, max_length=40)
    title: str = Field(min_length=1, max_length=300)
    text: str = Field(min_length=1, max_length=200_000)

    @field_validator("title")
    @classmethod
    def reject_control_injection(cls, value: str) -> str:
        if "\r" in value or "\n" in value:
            raise ValueError("template fields contain unsupported control characters")
        return value

    @field_validator("text")
    @classmethod
    def reject_carriage_return(cls, value: str) -> str:
        if "\r" in value:
            raise ValueError("template text must not contain CR")
        return value

    def render(self, context: Mapping[str, Any]) -> tuple[str, str]:
        try:
            rendered_title = Template(self.title).substitute({key: str(value) for key, value in context.items()})
            rendered_text = Template(self.text).substitute({key: str(value) for key, value in context.items()})
        except (KeyError, ValueError) as exc:
            raise ValueError("enterprise message template has an unresolved or invalid placeholder") from exc
        if not rendered_title.strip() or not rendered_text.strip():
            raise ValueError("enterprise message template rendered an empty message")
        return rendered_title, rendered_text


DEFAULT_ALERT_ENTERPRISE_TEMPLATE = EnterpriseMessageTemplate(
    name="alert.event",
    version="v1",
    title="Opportunity Radar alert: $title",
    text=(
        "$priority alert for $title\n\n$message\n\n"
        "alert_event_id=$alert_event_id\n"
        "event_key=$event_key\n"
        "score=$score\n"
        "risk_score=$risk_score\n"
        "data_class=$data_class"
    ),
)


class EnterpriseMessageRoute(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=80)
    provider: str = Field(min_length=2, max_length=40)
    destination: str = Field(min_length=1, max_length=500)
    enabled: bool = True
    priority: int = Field(default=100, ge=0, le=10_000)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not _ROUTE_NAME_RE.fullmatch(value):
            raise ValueError("route name contains unsupported characters")
        return value

    @field_validator("provider")
    @classmethod
    def normalize_provider(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"^[a-z][a-z0-9_-]{1,39}$", value):
            raise ValueError("route provider contains unsupported characters")
        return value

    @field_validator("destination")
    @classmethod
    def validate_destination(cls, value: str) -> str:
        value = value.strip()
        if not value or "\r" in value or "\n" in value:
            raise ValueError("route destination is invalid")
        return value


class EnterpriseRoutingPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_version: str = Field(default="enterprise-routing-policy-v1", min_length=1, max_length=50)
    routes: list[EnterpriseMessageRoute] = Field(default_factory=list, max_length=20)
    fallback_on_retryable: bool = False
    fallback_on_permanent: bool = True
    fallback_on_invalid: bool = True

    @model_validator(mode="after")
    def validate_unique_routes(self):
        names = [route.name.lower() for route in self.routes]
        if len(names) != len(set(names)):
            raise ValueError("routing policy route names must be unique")
        return self

    def ordered_routes(self) -> list[EnterpriseMessageRoute]:
        seen: set[tuple[str, str]] = set()
        ordered: list[EnterpriseMessageRoute] = []
        for route in sorted(self.routes, key=lambda item: (item.priority, item.name.lower())):
            if not route.enabled or (route.provider, route.destination) in seen:
                continue
            seen.add((route.provider, route.destination))
            ordered.append(route)
        return ordered


class EnterpriseRoutingResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: EnterpriseRoutingStatus
    template_name: str | None = None
    template_version: str | None = None
    selected_route: str | None = None
    provider_message_id: str | None = None
    fallback_used: bool = False
    attempts: list[dict[str, Any]] = Field(default_factory=list)
    final_result: EnterpriseMessageResult | None = None
    completed_at: datetime = Field(default_factory=utc_now)

    @field_validator("completed_at", mode="before")
    @classmethod
    def normalize_completed_at(cls, value):
        return as_utc_naive(value) if value is not None else utc_now()
