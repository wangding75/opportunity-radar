"""Durable alert-email queue with idempotency, leases, and bounded retries."""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import StrEnum
from typing import Callable

from sqlalchemy import and_, or_, select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.time import as_utc_naive, utc_now
from app.db.models import AlertEvent, EmailDeliveryRecord
from app.domain.email_delivery import (
    EmailDeliveryPort,
    EmailDeliveryPolicy,
    EmailDeliveryRequest,
    EmailDeliveryResult,
    EmailDeliveryStatus,
    EmailFailureKind,
    EmailRetryPolicy,
    EmailTemplate,
    build_delivery_result,
    build_email_request,
    delivery_input_signature,
)
from app.services.locks import acquire_email_delivery_lock
from app.services.mock_mail import MockMailService
from app.services.mock_mail_http import MockMailHTTPService
from app.services.smtp_mail import SMTPMailService

EMAIL_QUEUE_CONTRACT_VERSION = "email-delivery-queue-v1"
EMAIL_QUEUE_TEMPLATE = EmailTemplate(
    name="alert.event",
    version="v1",
    subject="Opportunity Radar alert: $title",
    text_body=(
        "$priority alert for $title\n\n"
        "$message\n\n"
        "alert_event_id=$alert_event_id\n"
        "event_key=$event_key\n"
        "score=$score\n"
        "risk_score=$risk_score\n"
        "data_class=$data_class"
    ),
    # Keep the first queue version plain-text only. Alert titles/messages are
    # user/source-controlled and are not treated as trusted HTML.
    html_body=None,
)
QUEUE_RETRY_POLICY = EmailRetryPolicy()
QUEUE_DELIVERY_POLICY = EmailDeliveryPolicy(retry=QUEUE_RETRY_POLICY)
EMAIL_CLAIM_SECONDS = 300
MAX_QUEUE_LIMIT = 500
QUEUEABLE_ALERT_STATUSES = {"NEW", "ACKNOWLEDGED"}
TERMINAL_QUEUE_STATUSES = {"SENT", "ACCEPTED", "PERMANENT_FAILURE", "SUPPRESSED", "INVALID"}
ALLOWED_DATA_CLASSES = {"ALERT_EVENT", "OBSERVED", "MOCK", "SYNTHETIC"}


class EmailQueueStatus(StrEnum):
    QUEUED = "QUEUED"
    CLAIMED = "CLAIMED"
    RETRY_WAIT = "RETRY_WAIT"
    ACCEPTED = "ACCEPTED"
    SENT = "SENT"
    PERMANENT_FAILURE = "PERMANENT_FAILURE"
    SUPPRESSED = "SUPPRESSED"
    INVALID = "INVALID"


_default_port: tuple[str, EmailDeliveryPort] | None = None


def get_default_email_delivery_port() -> EmailDeliveryPort:
    """Build the configured adapter without exposing provider secrets."""

    global _default_port
    provider = settings.email_delivery_provider
    if _default_port is None or _default_port[0] != provider:
        adapter: EmailDeliveryPort
        if provider == "smtp":
            adapter = SMTPMailService.from_settings(settings)
        elif provider == "mock_http":
            adapter = MockMailHTTPService.from_settings(settings)
        else:
            adapter = MockMailService()
        _default_port = (provider, adapter)
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


def _request_for_event(
    event: AlertEvent,
    *,
    recipients: list[str],
    data_class: str,
    requested_at: datetime,
) -> EmailDeliveryRequest:
    return build_email_request(
        message_id=f"alert-event-{event.id}",
        idempotency_key=f"alert-event:{event.event_key}:email:{EMAIL_QUEUE_TEMPLATE.version}",
        recipients=recipients,
        template=EMAIL_QUEUE_TEMPLATE,
        context={
            "alert_event_id": event.id,
            "event_key": event.event_key,
            "priority": event.priority,
            "title": event.title,
            "message": event.message or "Alert event has no message.",
            "score": event.score,
            "risk_score": event.risk_score,
            "data_class": data_class,
        },
        requested_at=requested_at,
        metadata={
            "contract_version": EMAIL_QUEUE_CONTRACT_VERSION,
            "data_class": data_class,
            "alert_event_id": str(event.id),
            "event_key": event.event_key,
        },
        policy=QUEUE_DELIVERY_POLICY,
    )


def _serialize_record(row: EmailDeliveryRecord) -> dict:
    return {
        "id": row.id,
        "alert_event_id": row.alert_event_id,
        "message_id": row.message_id,
        "idempotency_key": row.idempotency_key,
        "input_signature": row.input_signature,
        "recipients": row.recipients or [],
        "template_name": row.template_name,
        "template_version": row.template_version,
        "status": row.status,
        "attempt_count": row.attempt_count,
        "claim_until": row.claim_until,
        "next_retry_at": row.next_retry_at,
        "provider_message_id": row.provider_message_id,
        "failure_kind": row.failure_kind,
        "error_code": row.error_code,
        "error_detail": row.error_detail,
        "last_attempt_at": row.last_attempt_at,
        "sent_at": row.sent_at,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
        "contract_version": EMAIL_QUEUE_CONTRACT_VERSION,
    }


def enqueue_alert_emails(
    db: Session,
    *,
    recipients: list[str],
    alert_event_ids: set[int] | None = None,
    data_class: str = "ALERT_EVENT",
    limit: int = 100,
    now: datetime | None = None,
) -> dict:
    """Create at most one durable email request per AlertEvent.

    The alert lifecycle is intentionally not changed. A dismissed/resolved
    event is skipped, and an existing queue row is reported as a duplicate even
    when the caller repeats the request with the same recipients.
    """

    limit = _bounded_limit(limit)
    if not recipients:
        raise ValueError("recipients must not be empty")
    normalized_data_class = _normalize_data_class(data_class)
    now = as_utc_naive(now or utc_now())
    acquire_email_delivery_lock(db)

    stmt = select(AlertEvent).order_by(AlertEvent.created_at, AlertEvent.id).limit(limit)
    if alert_event_ids is None:
        stmt = stmt.where(AlertEvent.status.in_(QUEUEABLE_ALERT_STATUSES))
    elif not alert_event_ids:
        return {"selected": 0, "created": 0, "duplicates": 0, "conflicts": 0, "skipped": 0, "missing": 0, "records": []}
    else:
        stmt = stmt.where(AlertEvent.id.in_(sorted(alert_event_ids)))
    events = db.scalars(stmt).all()
    existing = {
        row.alert_event_id: row
        for row in db.scalars(select(EmailDeliveryRecord).where(EmailDeliveryRecord.alert_event_id.in_([event.id for event in events]))).all()
    } if events else {}
    result = {
        "selected": len(events),
        "created": 0,
        "duplicates": 0,
        "conflicts": 0,
        "skipped": 0,
        "missing": 0,
        "records": [],
    }
    requested_ids = alert_event_ids or set()
    result["missing"] = len(requested_ids - {event.id for event in events}) if alert_event_ids is not None else 0
    for event in events:
        if event.status not in QUEUEABLE_ALERT_STATUSES:
            result["skipped"] += 1
            continue
        request = _request_for_event(
            event,
            recipients=list(recipients),
            data_class=normalized_data_class,
            requested_at=now,
        )
        input_signature = delivery_input_signature(request, policy=QUEUE_DELIVERY_POLICY)
        row = existing.get(event.id)
        if row is not None:
            if row.input_signature == input_signature:
                result["duplicates"] += 1
            else:
                result["conflicts"] += 1
            result["records"].append(_serialize_record(row))
            continue
        row = EmailDeliveryRecord(
            alert_event_id=event.id,
            message_id=request.message_id,
            idempotency_key=request.idempotency_key,
            input_signature=input_signature,
            recipients=request.recipients,
            template_name=request.template_name,
            template_version=request.template_version,
            request_payload=request.model_dump(mode="json"),
            status=EmailQueueStatus.QUEUED,
            attempt_count=0,
            next_retry_at=now,
            created_at=now,
            updated_at=now,
        )
        db.add(row)
        db.flush()
        result["created"] += 1
        result["records"].append(_serialize_record(row))
    db.flush()
    return result


def claim_email_deliveries(
    db: Session,
    *,
    limit: int = 100,
    now: datetime | None = None,
    lease_seconds: int = EMAIL_CLAIM_SECONDS,
) -> list[EmailDeliveryRecord]:
    """Atomically claim due rows and increment their attempt counters."""

    limit = _bounded_limit(limit)
    if lease_seconds < 30 or lease_seconds > 86_400:
        raise ValueError("lease_seconds must be between 30 and 86400")
    now = as_utc_naive(now or utc_now())
    due = or_(EmailDeliveryRecord.next_retry_at.is_(None), EmailDeliveryRecord.next_retry_at <= now)
    available = or_(
        EmailDeliveryRecord.status.in_([EmailQueueStatus.QUEUED, EmailQueueStatus.RETRY_WAIT]),
        and_(EmailDeliveryRecord.status == EmailQueueStatus.CLAIMED, EmailDeliveryRecord.claim_until <= now),
    )
    candidate_ids = db.scalars(
        select(EmailDeliveryRecord.id)
        .where(available, due)
        .order_by(EmailDeliveryRecord.created_at, EmailDeliveryRecord.id)
        .limit(limit)
    ).all()
    claimed_ids: list[int] = []
    for record_id in candidate_ids:
        changed = db.execute(
            update(EmailDeliveryRecord)
            .where(EmailDeliveryRecord.id == record_id, available, due)
            .values(
                status=EmailQueueStatus.CLAIMED,
                claim_until=now + timedelta(seconds=lease_seconds),
                attempt_count=EmailDeliveryRecord.attempt_count + 1,
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
        select(EmailDeliveryRecord)
        .where(EmailDeliveryRecord.id.in_(claimed_ids))
        .order_by(EmailDeliveryRecord.id)
        .execution_options(populate_existing=True)
    ).all()


def _exception_result(
    request: EmailDeliveryRequest,
    *,
    attempt: int,
    now: datetime,
) -> EmailDeliveryResult:
    if attempt < QUEUE_RETRY_POLICY.max_attempts:
        return build_delivery_result(
            request,
            status=EmailDeliveryStatus.RETRYABLE_FAILURE,
            attempt=attempt,
            failure_kind=EmailFailureKind.TRANSIENT_PROVIDER,
            error_code="PROVIDER_EXCEPTION",
            error_detail="email provider raised an exception",
            now=now,
            policy=QUEUE_RETRY_POLICY,
        )
    return build_delivery_result(
        request,
        status=EmailDeliveryStatus.PERMANENT_FAILURE,
        attempt=attempt,
        failure_kind=EmailFailureKind.UNKNOWN,
        error_code="RETRY_EXHAUSTED",
        error_detail="email provider failed after the maximum retry attempts",
        now=now,
        policy=QUEUE_RETRY_POLICY,
    )


def _apply_result(row: EmailDeliveryRecord, result: EmailDeliveryResult, *, now: datetime) -> str:
    if result.input_signature != row.input_signature:
        row.status = EmailQueueStatus.INVALID
        row.failure_kind = EmailFailureKind.UNKNOWN
        row.error_code = "INPUT_SIGNATURE_MISMATCH"
        row.error_detail = "provider result did not match the persisted request signature"
        row.next_retry_at = None
        row.claim_until = None
        row.updated_at = now
        return row.status
    if result.status == EmailDeliveryStatus.RETRYABLE_FAILURE:
        row.status = EmailQueueStatus.RETRY_WAIT if result.next_retry_at is not None else EmailQueueStatus.PERMANENT_FAILURE
        row.next_retry_at = result.next_retry_at
    elif result.status == EmailDeliveryStatus.ACCEPTED:
        row.status = EmailQueueStatus.ACCEPTED
        row.next_retry_at = None
    else:
        row.status = result.status.value
        row.next_retry_at = None
    row.attempt_count = max(row.attempt_count, result.attempt)
    row.provider_message_id = result.provider_message_id
    row.failure_kind = result.failure_kind.value if result.failure_kind else None
    row.error_code = result.error_code
    row.error_detail = (result.error_detail or "")[:2_000] or None
    row.claim_until = None
    row.updated_at = now
    if result.status == EmailDeliveryStatus.SENT:
        row.sent_at = result.observed_at
    return row.status


def process_email_delivery_queue(
    db: Session,
    *,
    limit: int = 100,
    port: EmailDeliveryPort | None = None,
    now: datetime | None = None,
    progress_callback: Callable[[], None] | None = None,
) -> dict:
    """Claim, deliver, and persist each row independently.

    A provider exception is converted into a retryable result until the bounded
    attempt limit is reached. No exception is reported as a successful send.
    """

    now = as_utc_naive(now or utc_now())
    port = port or get_default_email_delivery_port()
    records = claim_email_deliveries(db, limit=limit, now=now)
    results: list[dict] = []
    for row in records:
        observed_at = utc_now()
        try:
            request = EmailDeliveryRequest.model_validate(row.request_payload)
            provider_result = port.send(request)
            status = _apply_result(row, provider_result, now=observed_at)
            results.append({"id": row.id, "alert_event_id": row.alert_event_id, "status": status, "attempt": row.attempt_count})
        except ValueError as exc:
            row.status = EmailQueueStatus.INVALID
            row.failure_kind = EmailFailureKind.UNKNOWN
            row.error_code = "INVALID_REQUEST"
            row.error_detail = str(exc)[:2_000]
            row.next_retry_at = None
            row.claim_until = None
            row.updated_at = observed_at
            results.append({"id": row.id, "alert_event_id": row.alert_event_id, "status": row.status, "attempt": row.attempt_count, "error": str(exc)[:2_000]})
        except Exception as exc:  # provider boundary: convert to durable retry state
            request = EmailDeliveryRequest.model_validate(row.request_payload)
            provider_result = _exception_result(request, attempt=row.attempt_count, now=observed_at)
            status = _apply_result(row, provider_result, now=observed_at)
            results.append({"id": row.id, "alert_event_id": row.alert_event_id, "status": status, "attempt": row.attempt_count, "error": str(exc)[:2_000]})
        db.commit()
        if progress_callback is not None:
            progress_callback()
    return {
        "contract_version": EMAIL_QUEUE_CONTRACT_VERSION,
        "claimed": len(records),
        "processed": len(records),
        "sent": sum(1 for item in results if item["status"] == EmailQueueStatus.SENT),
        "retry_wait": sum(1 for item in results if item["status"] == EmailQueueStatus.RETRY_WAIT),
        "failed": sum(1 for item in results if item["status"] in {EmailQueueStatus.PERMANENT_FAILURE, EmailQueueStatus.INVALID}),
        "results": results,
    }


def list_email_delivery_records(
    db: Session,
    *,
    alert_event_id: int | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[dict]:
    stmt = select(EmailDeliveryRecord).order_by(EmailDeliveryRecord.created_at.desc(), EmailDeliveryRecord.id.desc()).limit(_bounded_limit(limit))
    if alert_event_id is not None:
        stmt = stmt.where(EmailDeliveryRecord.alert_event_id == alert_event_id)
    if status:
        stmt = stmt.where(EmailDeliveryRecord.status == status.strip().upper())
    return [_serialize_record(row) for row in db.scalars(stmt).all()]
