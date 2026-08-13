from __future__ import annotations

from datetime import timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.time import utc_now
from app.db.models import AlertEvent, AuditLog, CollectionRun, RawObservation


def _count_before(db: Session, model, column, cutoff) -> int:
    return int(db.scalar(select(func.count()).select_from(model).where(column < cutoff)) or 0)


def run_retention(db: Session, *, dry_run: bool = True) -> dict:
    """Apply bounded hot-data retention policies.

    Raw observations are disabled by default because they are primary research
    evidence. Operators must explicitly opt in with RAW_OBSERVATION_RETENTION_DAYS.
    """
    now = utc_now()
    policies = [
        ("collection_runs", CollectionRun, CollectionRun.started_at, settings.collection_run_retention_days),
        ("audit_logs", AuditLog, AuditLog.created_at, settings.audit_log_retention_days),
        ("alert_events", AlertEvent, AlertEvent.created_at, settings.alert_event_retention_days),
        ("raw_observations", RawObservation, RawObservation.observed_at, settings.raw_observation_retention_days),
    ]
    results: dict[str, dict] = {}
    for name, model, column, days in policies:
        if days <= 0:
            results[name] = {"enabled": False, "retention_days": days, "eligible": 0, "deleted": 0}
            continue
        cutoff = now - timedelta(days=days)
        eligible = _count_before(db, model, column, cutoff)
        if name == "raw_observations":
            # Primary evidence rows are intentionally protected from destructive retention.
            # Large raw payload bodies can be cold-archived separately without deleting
            # the observation/evidence row or breaking derived relationships.
            results[name] = {
                "enabled": True,
                "protected": True,
                "retention_days": days,
                "cutoff": cutoff,
                "eligible": eligible,
                "deleted": 0,
                "reason": "primary evidence rows remain protected; raw payload bodies may be cold-archived separately",
            }
            continue
        deleted = 0
        if not dry_run and eligible:
            result = db.execute(delete(model).where(column < cutoff))
            deleted = int(result.rowcount or 0)
        results[name] = {
            "enabled": True,
            "retention_days": days,
            "cutoff": cutoff,
            "eligible": eligible,
            "deleted": deleted,
        }
    if not dry_run:
        db.commit()
    return {"dry_run": dry_run, "policies": results}
