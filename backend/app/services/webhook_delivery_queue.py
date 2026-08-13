"""Durable Webhook delivery queue with HMAC signing, leases, retries and idempotency."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Callable

import httpx
from sqlalchemy import and_, or_, select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.time import as_utc_naive, utc_now
from app.db.models import AlertEvent, WebhookDeliveryRecord, WebhookEndpoint
from app.domain.webhook import (
    WebhookDeliveryPort,
    WebhookDeliveryRequest,
    WebhookDeliveryResult,
    WebhookDeliveryStatus,
    WebhookDataClass,
    WebhookEvent,
    WebhookEventType,
    WebhookFailureKind,
    WebhookRetryPolicy,
    build_webhook_headers,
    canonical_event_bytes,
    format_webhook_signature,
    sign_webhook_event,
)
from app.services.locks import acquire_webhook_delivery_lock
from app.services.webhook_security import resolve_webhook_destination

WEBHOOK_QUEUE_CONTRACT_VERSION = "webhook-delivery-queue-v1"
QUEUE_RETRY_POLICY = WebhookRetryPolicy()
WEBHOOK_CLAIM_SECONDS = 300
MAX_QUEUE_LIMIT = 500
QUEUEABLE_ALERT_STATUSES = {"NEW", "ACKNOWLEDGED"}
ALLOWED_DATA_CLASSES = {item.value for item in WebhookDataClass}


class WebhookQueueStatus(StrEnum):
    QUEUED = "QUEUED"
    CLAIMED = "CLAIMED"
    RETRY_WAIT = "RETRY_WAIT"
    SENT = "SENT"
    PERMANENT_FAILURE = "PERMANENT_FAILURE"
    SUPPRESSED = "SUPPRESSED"
    INVALID = "INVALID"


class HTTPWebhookDeliveryService:
    """The only production HTTP adapter; the queue remains provider-neutral."""

    def __init__(self, *, timeout_seconds: float = 10.0):
        self.timeout_seconds = timeout_seconds

    def send(
        self,
        request: WebhookDeliveryRequest,
        *,
        endpoint_url: str,
        headers: dict[str, str],
        body: bytes,
    ) -> WebhookDeliveryResult:
        resolve_webhook_destination(endpoint_url, allowed_hosts=settings.webhook_allowed_hosts)
        response = httpx.post(
            endpoint_url,
            headers=headers,
            content=body,
            timeout=self.timeout_seconds,
            follow_redirects=False,
        )
        status = response.status_code
        provider_message_id = response.headers.get("X-Request-ID") or response.headers.get("X-Webhook-Receipt")
        if 200 <= status < 300:
            return WebhookDeliveryResult(
                status=WebhookDeliveryStatus.SENT,
                attempt=request.attempt,
                http_status=status,
                provider_message_id=provider_message_id,
            )
        if status in {408, 425, 429} or 500 <= status <= 599:
            failure_kind = WebhookFailureKind.RATE_LIMITED if status == 429 else WebhookFailureKind.TRANSIENT_NETWORK
            return WebhookDeliveryResult(
                status=WebhookDeliveryStatus.RETRYABLE_FAILURE,
                attempt=request.attempt,
                http_status=status,
                provider_message_id=provider_message_id,
                failure_kind=failure_kind,
                error_code=f"HTTP_{status}",
                error_detail="webhook receiver returned a retryable HTTP status",
            )
        return WebhookDeliveryResult(
            status=WebhookDeliveryStatus.PERMANENT_FAILURE,
            attempt=request.attempt,
            http_status=status,
            provider_message_id=provider_message_id,
            failure_kind=WebhookFailureKind.AUTHENTICATION if status in {401, 403} else WebhookFailureKind.INVALID_ENDPOINT,
            error_code=f"HTTP_{status}",
            error_detail="webhook receiver returned a non-retryable HTTP status",
        )


_default_port: tuple[float, WebhookDeliveryPort] | None = None


def get_default_webhook_delivery_port() -> WebhookDeliveryPort:
    global _default_port
    timeout = settings.webhook_delivery_timeout_seconds
    if _default_port is None or _default_port[0] != timeout:
        _default_port = (timeout, HTTPWebhookDeliveryService(timeout_seconds=timeout))
    return _default_port[1]


def _bounded_limit(limit: int) -> int:
    if limit < 1 or limit > MAX_QUEUE_LIMIT:
        raise ValueError(f"limit must be between 1 and {MAX_QUEUE_LIMIT}")
    return limit


def _normalize_data_class(value: str) -> str:
    normalized = str(value or "ALERT_EVENT").strip().upper()
    if normalized not in ALLOWED_DATA_CLASSES:
        raise ValueError(f"data_class must be one of {sorted(ALLOWED_DATA_CLASSES)}")
    return normalized


def _event_for_alert(event: AlertEvent, *, data_class: str) -> WebhookEvent:
    return WebhookEvent(
        event_id=f"evt_alert_{event.event_key}",
        event_type=WebhookEventType.ALERT_EVENT,
        event_version="1",
        occurred_at=event.created_at,
        data_class=data_class,
        payload={
            "alert_event_id": event.id,
            "event_key": event.event_key,
            "status": event.status,
            "priority": event.priority,
            "title": event.title,
            "message": event.message or "",
            "score": event.score,
            "risk_score": event.risk_score,
        },
    )


def _input_signature(event: WebhookEvent, *, endpoint_id: int) -> str:
    material = b"|".join((WEBHOOK_QUEUE_CONTRACT_VERSION.encode("ascii"), str(endpoint_id).encode("ascii"), canonical_event_bytes(event)))
    return hashlib.sha256(material).hexdigest()


def _serialize_record(row: WebhookDeliveryRecord) -> dict:
    return {
        "id": row.id,
        "alert_event_id": row.alert_event_id,
        "endpoint_id": row.endpoint_id,
        "event_id": row.event_id,
        "delivery_id": row.delivery_id,
        "input_signature": row.input_signature,
        "event_payload": row.event_payload or {},
        "status": row.status,
        "attempt_count": row.attempt_count,
        "claim_until": row.claim_until,
        "next_retry_at": row.next_retry_at,
        "request_body": row.request_body,
        "signature_header": row.signature_header,
        "http_status": row.http_status,
        "provider_message_id": row.provider_message_id,
        "failure_kind": row.failure_kind,
        "error_code": row.error_code,
        "error_detail": row.error_detail,
        "last_attempt_at": row.last_attempt_at,
        "sent_at": row.sent_at,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
        "contract_version": WEBHOOK_QUEUE_CONTRACT_VERSION,
    }


def enqueue_alert_webhooks(
    db: Session,
    *,
    alert_event_ids: set[int] | None = None,
    endpoint_ids: set[int] | None = None,
    data_class: str = "ALERT_EVENT",
    limit: int = 100,
    now: datetime | None = None,
) -> dict:
    """Create at most one delivery per alert event and enabled endpoint."""

    limit = _bounded_limit(limit)
    normalized_data_class = _normalize_data_class(data_class)
    now = as_utc_naive(now or utc_now())
    acquire_webhook_delivery_lock(db)
    if alert_event_ids is not None and not alert_event_ids:
        return {"selected": 0, "endpoints": 0, "created": 0, "duplicates": 0, "conflicts": 0, "skipped": 0, "missing": 0, "records": []}

    stmt = select(AlertEvent).order_by(AlertEvent.created_at, AlertEvent.id).limit(limit)
    if alert_event_ids is None:
        stmt = stmt.where(AlertEvent.status.in_(QUEUEABLE_ALERT_STATUSES))
    else:
        stmt = stmt.where(AlertEvent.id.in_(sorted(alert_event_ids)))
    events = db.scalars(stmt).all()
    requested_ids = alert_event_ids or set()
    endpoints_stmt = select(WebhookEndpoint).where(WebhookEndpoint.enabled.is_(True)).order_by(WebhookEndpoint.id)
    if endpoint_ids is not None:
        if not endpoint_ids:
            return {"selected": len(events), "endpoints": 0, "created": 0, "duplicates": 0, "conflicts": 0, "skipped": 0, "missing": len(requested_ids - {event.id for event in events}), "records": []}
        endpoints_stmt = endpoints_stmt.where(WebhookEndpoint.id.in_(sorted(endpoint_ids)))
    endpoints = [row for row in db.scalars(endpoints_stmt).all() if WebhookEventType.ALERT_EVENT.value in (row.event_types or [])]
    existing = {}
    if events and endpoints:
        existing = {
            (row.alert_event_id, row.endpoint_id): row
            for row in db.scalars(
                select(WebhookDeliveryRecord).where(
                    WebhookDeliveryRecord.alert_event_id.in_([event.id for event in events]),
                    WebhookDeliveryRecord.endpoint_id.in_([endpoint.id for endpoint in endpoints]),
                )
            ).all()
        }
    result = {
        "selected": len(events),
        "endpoints": len(endpoints),
        "created": 0,
        "duplicates": 0,
        "conflicts": 0,
        "skipped": sum(1 for event in events if event.status not in QUEUEABLE_ALERT_STATUSES),
        "missing": len(requested_ids - {event.id for event in events}) if alert_event_ids is not None else 0,
        "records": [],
    }
    for event in events:
        if event.status not in QUEUEABLE_ALERT_STATUSES:
            continue
        for endpoint in endpoints:
            webhook_event = _event_for_alert(event, data_class=normalized_data_class)
            signature = _input_signature(webhook_event, endpoint_id=endpoint.id)
            row = existing.get((event.id, endpoint.id))
            if row is not None:
                if row.input_signature == signature:
                    result["duplicates"] += 1
                else:
                    result["conflicts"] += 1
                result["records"].append(_serialize_record(row))
                continue
            row = WebhookDeliveryRecord(
                alert_event_id=event.id,
                endpoint_id=endpoint.id,
                event_id=webhook_event.event_id,
                delivery_id=f"del_alert_{event.id}_endpoint_{endpoint.id}",
                input_signature=signature,
                event_payload=webhook_event.model_dump(mode="json"),
                status=WebhookQueueStatus.QUEUED,
                attempt_count=0,
                next_retry_at=now,
                created_at=now,
                updated_at=now,
            )
            db.add(row)
            db.flush()
            existing[(event.id, endpoint.id)] = row
            result["created"] += 1
            result["records"].append(_serialize_record(row))
    db.flush()
    return result


def claim_webhook_deliveries(
    db: Session,
    *,
    limit: int = 100,
    now: datetime | None = None,
    lease_seconds: int = WEBHOOK_CLAIM_SECONDS,
) -> list[WebhookDeliveryRecord]:
    limit = _bounded_limit(limit)
    if lease_seconds < 30 or lease_seconds > 86_400:
        raise ValueError("lease_seconds must be between 30 and 86400")
    now = as_utc_naive(now or utc_now())
    due = or_(WebhookDeliveryRecord.next_retry_at.is_(None), WebhookDeliveryRecord.next_retry_at <= now)
    available = or_(
        WebhookDeliveryRecord.status.in_([WebhookQueueStatus.QUEUED, WebhookQueueStatus.RETRY_WAIT]),
        and_(WebhookDeliveryRecord.status == WebhookQueueStatus.CLAIMED, WebhookDeliveryRecord.claim_until <= now),
    )
    candidate_ids = db.scalars(
        select(WebhookDeliveryRecord.id).where(available, due).order_by(WebhookDeliveryRecord.created_at, WebhookDeliveryRecord.id).limit(limit)
    ).all()
    claimed_ids: list[int] = []
    for record_id in candidate_ids:
        changed = db.execute(
            update(WebhookDeliveryRecord)
            .where(WebhookDeliveryRecord.id == record_id, available, due)
            .values(
                status=WebhookQueueStatus.CLAIMED,
                claim_until=now + timedelta(seconds=lease_seconds),
                attempt_count=WebhookDeliveryRecord.attempt_count + 1,
                last_attempt_at=now,
                updated_at=now,
            )
            .execution_options(synchronize_session=False)
        )
        if changed.rowcount == 1:
            claimed_ids.append(record_id)
    db.commit()
    if not claimed_ids:
        return []
    return db.scalars(
        select(WebhookDeliveryRecord).where(WebhookDeliveryRecord.id.in_(claimed_ids)).order_by(WebhookDeliveryRecord.id).execution_options(populate_existing=True)
    ).all()


def _retry_at(now: datetime, attempt: int) -> datetime:
    delay = min(QUEUE_RETRY_POLICY.base_delay_seconds * (2 ** max(0, attempt - 1)), QUEUE_RETRY_POLICY.max_delay_seconds)
    return now + timedelta(seconds=delay)


def _exception_result(*, attempt: int, now: datetime) -> WebhookDeliveryResult:
    if attempt < QUEUE_RETRY_POLICY.max_attempts:
        return WebhookDeliveryResult(
            status=WebhookDeliveryStatus.RETRYABLE_FAILURE,
            attempt=attempt,
            next_retry_at=_retry_at(now, attempt),
            failure_kind=WebhookFailureKind.TRANSIENT_NETWORK,
            error_code="PROVIDER_EXCEPTION",
            error_detail="webhook provider raised an exception",
        )
    return WebhookDeliveryResult(
        status=WebhookDeliveryStatus.PERMANENT_FAILURE,
        attempt=attempt,
        failure_kind=WebhookFailureKind.UNKNOWN,
        error_code="RETRY_EXHAUSTED",
        error_detail="webhook provider failed after the maximum retry attempts",
    )


def _apply_result(row: WebhookDeliveryRecord, result: WebhookDeliveryResult, *, now: datetime) -> str:
    if result.input_signature is not None and result.input_signature != row.input_signature:
        row.status = WebhookQueueStatus.INVALID
        row.failure_kind = WebhookFailureKind.UNKNOWN
        row.error_code = "INPUT_SIGNATURE_MISMATCH"
        row.error_detail = "provider result did not match the persisted request signature"
        row.next_retry_at = None
    elif result.status == WebhookDeliveryStatus.RETRYABLE_FAILURE:
        row.status = WebhookQueueStatus.RETRY_WAIT if result.next_retry_at is not None else WebhookQueueStatus.PERMANENT_FAILURE
        row.next_retry_at = result.next_retry_at
    else:
        row.status = result.status.value
        row.next_retry_at = None
    row.attempt_count = max(row.attempt_count, result.attempt)
    row.http_status = result.http_status
    row.provider_message_id = result.provider_message_id
    row.failure_kind = result.failure_kind.value if result.failure_kind else None
    row.error_code = result.error_code
    row.error_detail = (result.error_detail or "")[:2_000] or None
    row.claim_until = None
    row.updated_at = now
    if result.status == WebhookDeliveryStatus.SENT:
        row.sent_at = result.observed_at
    return row.status


def process_webhook_delivery_queue(
    db: Session,
    *,
    limit: int = 100,
    port: WebhookDeliveryPort | None = None,
    now: datetime | None = None,
    progress_callback: Callable[[], None] | None = None,
) -> dict:
    now = as_utc_naive(now or utc_now())
    port = port or get_default_webhook_delivery_port()
    records = claim_webhook_deliveries(db, limit=limit, now=now)
    results: list[dict] = []
    for row in records:
        observed_at = now
        endpoint = db.get(WebhookEndpoint, row.endpoint_id)
        try:
            if endpoint is None:
                raise LookupError("webhook endpoint no longer exists")
            if not endpoint.enabled:
                row.status = WebhookQueueStatus.SUPPRESSED
                row.error_code = "ENDPOINT_DISABLED"
                row.error_detail = "webhook endpoint was disabled before delivery"
                row.next_retry_at = None
                row.claim_until = None
                row.updated_at = observed_at
                status = row.status
            else:
                event = WebhookEvent.model_validate(row.event_payload)
                request = WebhookDeliveryRequest(event=event, delivery_id=row.delivery_id, attempt=row.attempt_count)
                nonce = f"nonce_{hashlib.sha256(f'{row.delivery_id}:{row.attempt_count}'.encode('ascii')).hexdigest()[:24]}"
                signature = sign_webhook_event(
                    event,
                    endpoint.secret,
                    timestamp=int(observed_at.replace(tzinfo=timezone.utc).timestamp()),
                    delivery_id=row.delivery_id,
                    nonce=nonce,
                )
                request = request.model_copy(update={"signature": signature})
                body = canonical_event_bytes(event)
                headers = build_webhook_headers(event, endpoint.secret, signature=signature)
                row.request_body = body.decode("utf-8")
                row.signature_header = format_webhook_signature(signature)
                provider_result = port.send(request, endpoint_url=endpoint.url, headers=headers, body=body)
                status = _apply_result(row, provider_result, now=observed_at)
        except ValueError as exc:
            row.status = WebhookQueueStatus.INVALID
            row.failure_kind = WebhookFailureKind.UNKNOWN
            row.error_code = "INVALID_REQUEST"
            row.error_detail = str(exc)[:2_000]
            row.next_retry_at = None
            row.claim_until = None
            row.updated_at = observed_at
            status = row.status
        except LookupError as exc:
            row.status = WebhookQueueStatus.PERMANENT_FAILURE
            row.failure_kind = WebhookFailureKind.INVALID_ENDPOINT
            row.error_code = "ENDPOINT_NOT_FOUND"
            row.error_detail = str(exc)[:2_000]
            row.next_retry_at = None
            row.claim_until = None
            row.updated_at = observed_at
            status = row.status
        except Exception as exc:
            status = _apply_result(row, _exception_result(attempt=row.attempt_count, now=observed_at), now=observed_at)
            row.error_detail = f"{row.error_detail or ''}: {str(exc)[:1_000]}"[:2_000]
        results.append({"id": row.id, "alert_event_id": row.alert_event_id, "endpoint_id": row.endpoint_id, "status": status, "attempt": row.attempt_count})
        db.commit()
        if progress_callback is not None:
            progress_callback()
    return {
        "contract_version": WEBHOOK_QUEUE_CONTRACT_VERSION,
        "claimed": len(records),
        "processed": len(records),
        "sent": sum(1 for item in results if item["status"] == WebhookQueueStatus.SENT),
        "retry_wait": sum(1 for item in results if item["status"] == WebhookQueueStatus.RETRY_WAIT),
        "failed": sum(1 for item in results if item["status"] in {WebhookQueueStatus.PERMANENT_FAILURE, WebhookQueueStatus.INVALID}),
        "suppressed": sum(1 for item in results if item["status"] == WebhookQueueStatus.SUPPRESSED),
        "results": results,
    }


def list_webhook_delivery_records(
    db: Session,
    *,
    alert_event_id: int | None = None,
    endpoint_id: int | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[dict]:
    stmt = select(WebhookDeliveryRecord).order_by(WebhookDeliveryRecord.created_at.desc(), WebhookDeliveryRecord.id.desc()).limit(_bounded_limit(limit))
    if alert_event_id is not None:
        stmt = stmt.where(WebhookDeliveryRecord.alert_event_id == alert_event_id)
    if endpoint_id is not None:
        stmt = stmt.where(WebhookDeliveryRecord.endpoint_id == endpoint_id)
    if status:
        stmt = stmt.where(WebhookDeliveryRecord.status == status.strip().upper())
    return [_serialize_record(row) for row in db.scalars(stmt).all()]
