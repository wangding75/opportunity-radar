"""Persistent webhook endpoint configuration with write-only secret handling."""

from __future__ import annotations

import hashlib
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import WebhookDeliveryRecord, WebhookEndpoint
from app.domain.webhook import WebhookEndpointCreate, WebhookEndpointPatch, validate_webhook_secret


def _fingerprint(secret: str) -> str:
    return hashlib.sha256(validate_webhook_secret(secret)).hexdigest()


def _event_values(values) -> list[str]:
    return [item.value if hasattr(item, "value") else str(item) for item in values]


def serialize_webhook_endpoint(row: WebhookEndpoint) -> dict:
    """Never include the signing secret in API or audit-facing output."""

    return {
        "id": row.id,
        "name": row.name,
        "url": row.url,
        "secret_fingerprint": row.secret_fingerprint,
        "event_types": row.event_types or [],
        "enabled": row.enabled,
        "description": row.description,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def list_webhook_endpoints(db: Session) -> list[dict]:
    return [serialize_webhook_endpoint(row) for row in db.scalars(select(WebhookEndpoint).order_by(WebhookEndpoint.id)).all()]


def create_webhook_endpoint(db: Session, payload: WebhookEndpointCreate, *, now: datetime | None = None) -> WebhookEndpoint:
    normalized_name = payload.name.strip()
    if db.scalar(select(WebhookEndpoint.id).where(func.lower(WebhookEndpoint.name) == normalized_name.lower())) is not None:
        raise ValueError("webhook endpoint name already exists")
    now = now or utc_now()
    row = WebhookEndpoint(
        name=normalized_name,
        url=payload.url,
        secret=payload.secret,
        secret_fingerprint=_fingerprint(payload.secret),
        event_types=_event_values(payload.event_types),
        enabled=payload.enabled,
        description=payload.description,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.flush()
    return row


def patch_webhook_endpoint(db: Session, endpoint_id: int, payload: WebhookEndpointPatch, *, now: datetime | None = None) -> WebhookEndpoint:
    row = db.get(WebhookEndpoint, endpoint_id)
    if row is None:
        raise KeyError("webhook endpoint not found")
    values = payload.model_dump(exclude_unset=True)
    if "name" in values:
        name = str(values["name"]).strip()
        collision = db.scalar(select(WebhookEndpoint.id).where(func.lower(WebhookEndpoint.name) == name.lower(), WebhookEndpoint.id != endpoint_id))
        if collision is not None:
            raise ValueError("webhook endpoint name already exists")
        row.name = name
    if "url" in values:
        row.url = str(values["url"])
    if "secret" in values and values["secret"] is not None:
        row.secret = str(values["secret"])
        row.secret_fingerprint = _fingerprint(row.secret)
    if "event_types" in values:
        row.event_types = _event_values(values["event_types"])
    for field in ("enabled", "description"):
        if field in values:
            setattr(row, field, values[field])
    row.updated_at = now or utc_now()
    db.flush()
    return row


def delete_webhook_endpoint(db: Session, endpoint_id: int) -> None:
    row = db.get(WebhookEndpoint, endpoint_id)
    if row is None:
        raise KeyError("webhook endpoint not found")
    if db.scalar(select(WebhookDeliveryRecord.id).where(WebhookDeliveryRecord.endpoint_id == endpoint_id)) is not None:
        raise ValueError("webhook endpoint cannot be deleted while delivery history exists; disable it instead")
    db.delete(row)
    db.flush()
