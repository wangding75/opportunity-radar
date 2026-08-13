from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

# Stable 64-bit application lock key for derived-analysis writes. The lock is
# transaction-scoped on PostgreSQL and therefore released automatically on
# commit/rollback. SQLite already serializes writers at the database level.
_DERIVED_ANALYSIS_LOCK_KEY = 0x4F50505241444152  # "OPPRADAR"
_ALERT_EVALUATION_LOCK_KEY = 0x4F5050414C455254  # "OPPALERT"
_EMAIL_DELIVERY_LOCK_KEY = 0x4F5050454D41494C  # "OPPEMAIL"
_WEBHOOK_DELIVERY_LOCK_KEY = 0x4F5050574542484B  # "OPPWEBHK"


def acquire_derived_analysis_lock(db: Session) -> None:
    bind = db.get_bind()
    if bind.dialect.name == "postgresql":
        db.execute(
            text("SELECT pg_advisory_xact_lock(:lock_key)"),
            {"lock_key": _DERIVED_ANALYSIS_LOCK_KEY},
        )


def acquire_alert_evaluation_lock(db: Session) -> None:
    """Serialize alert-event materialization on PostgreSQL.

    Queue claims prevent two workers from claiming the same opportunity, but a
    manual synchronous evaluation can legitimately run at the same time. A
    transaction lock keeps the unique event key as a final invariant rather than
    the normal concurrency-control mechanism.
    """
    bind = db.get_bind()
    if bind.dialect.name == "postgresql":
        db.execute(
            text("SELECT pg_advisory_xact_lock(:lock_key)"),
            {"lock_key": _ALERT_EVALUATION_LOCK_KEY},
        )


def acquire_email_delivery_lock(db: Session) -> None:
    """Serialize email queue materialization on PostgreSQL.

    The unique constraints remain the final idempotency invariant. This lock
    keeps concurrent API and worker materialization from relying on an
    IntegrityError for normal duplicate requests.
    """
    bind = db.get_bind()
    if bind.dialect.name == "postgresql":
        db.execute(
            text("SELECT pg_advisory_xact_lock(:lock_key)"),
            {"lock_key": _EMAIL_DELIVERY_LOCK_KEY},
        )


def acquire_webhook_delivery_lock(db: Session) -> None:
    """Serialize Webhook queue materialization on PostgreSQL."""
    bind = db.get_bind()
    if bind.dialect.name == "postgresql":
        db.execute(
            text("SELECT pg_advisory_xact_lock(:lock_key)"),
            {"lock_key": _WEBHOOK_DELIVERY_LOCK_KEY},
        )
