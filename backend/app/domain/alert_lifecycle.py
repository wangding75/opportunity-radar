from __future__ import annotations

from enum import IntEnum, StrEnum


class AlertPriority(IntEnum):
    """Stable display and routing priority for a materialized alert event."""

    INFO = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5


class AlertEventStatus(StrEnum):
    NEW = "NEW"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    DISMISSED = "DISMISSED"
    RESOLVED = "RESOLVED"


VALID_ALERT_EVENT_STATUSES = {status.value for status in AlertEventStatus}

# Terminal states are intentionally not reopenable. A new analysis revision
# creates a new event key, so a dismissed/resolved event remains an immutable
# record of the human decision that was made for that signal.
ALERT_STATUS_TRANSITIONS: dict[str, frozenset[str]] = {
    AlertEventStatus.NEW.value: frozenset({AlertEventStatus.NEW.value, AlertEventStatus.ACKNOWLEDGED.value, AlertEventStatus.DISMISSED.value}),
    AlertEventStatus.ACKNOWLEDGED.value: frozenset({AlertEventStatus.ACKNOWLEDGED.value, AlertEventStatus.DISMISSED.value, AlertEventStatus.RESOLVED.value}),
    AlertEventStatus.DISMISSED.value: frozenset({AlertEventStatus.DISMISSED.value}),
    AlertEventStatus.RESOLVED.value: frozenset({AlertEventStatus.RESOLVED.value}),
}


def normalize_alert_status(value: str) -> str:
    normalized = str(value).strip().upper()
    if normalized not in VALID_ALERT_EVENT_STATUSES:
        raise ValueError(f"invalid alert event status: {value}")
    return normalized


def validate_alert_status_transition(current: str, target: str) -> tuple[str, str]:
    current_status = normalize_alert_status(current)
    target_status = normalize_alert_status(target)
    if target_status not in ALERT_STATUS_TRANSITIONS[current_status]:
        raise ValueError(f"alert event cannot transition from {current_status} to {target_status}")
    return current_status, target_status


def derive_alert_priority(*, score: float, risk_score: float, evidence_count: int, high_signal: bool = False) -> int:
    """Derive a bounded priority from the same signal facts used by alerts."""

    if high_signal:
        return AlertPriority.CRITICAL.value
    if score >= 90 and risk_score <= 30 and evidence_count >= 5:
        return AlertPriority.CRITICAL.value
    if score >= 80 and risk_score <= 40 and evidence_count >= 3:
        return AlertPriority.HIGH.value
    if score >= 70 and risk_score <= 60 and evidence_count >= 2:
        return AlertPriority.MEDIUM.value
    if score >= 60:
        return AlertPriority.LOW.value
    return AlertPriority.INFO.value
