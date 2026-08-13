from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return timezone-naive UTC for DB portability."""
    return datetime.now(UTC).replace(tzinfo=None)


def as_utc_naive(value: datetime) -> datetime:
    """Normalize external timestamps to timezone-naive UTC before persistence."""
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)
