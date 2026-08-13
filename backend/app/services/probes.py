from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from collections.abc import Callable
import os

from sqlalchemy import desc, or_, select, update
from sqlalchemy.orm import Session

from app.connectors.registry import SourceRegistry
from app.core.time import utc_now
from app.db.models import CollectionRun, Keyword, ProbeTask
from app.domain.enums import Capability, CollectionRunStatus, KeywordStatus, QueryMode
from app.domain.schemas import CollectorQuery
from app.services.execution import execute_collection
from app.services.source_preferences import source_enabled


@dataclass(frozen=True)
class ProbeTemplate:
    suffix_zh: str
    suffix_en: str
    intent: str


TEMPLATES = (
    ProbeTemplate("工具", "tool", "SUPPLY"),
    ProbeTemplate("教程", "tutorial", "SUPPLY"),
    ProbeTemplate("招聘", "jobs", "EXECUTION"),
    ProbeTemplate("变现", "monetization", "DEMAND"),
)


def _is_ascii(value: str) -> bool:
    return all(ord(ch) < 128 for ch in value)


def _supports_intent(capabilities: set[Capability], intent: str) -> bool:
    if intent == "BASE":
        return bool({Capability.SEARCH, Capability.SEARCH_OBSERVATION, Capability.REPOSITORY} & capabilities)
    if intent == "SUPPLY":
        return bool({Capability.PRODUCT, Capability.REPOSITORY, Capability.SEARCH_OBSERVATION} & capabilities)
    if intent == "EXECUTION":
        return bool({Capability.JOB, Capability.SEARCH_OBSERVATION} & capabilities)
    if intent == "DEMAND":
        return bool({Capability.TREND, Capability.RELATED_KEYWORD, Capability.SEARCH_OBSERVATION} & capabilities)
    return False


def _interval_minutes(keyword: Keyword) -> int:
    if keyword.status == KeywordStatus.TRENDING.value or keyword.score >= 75:
        return 12 * 60
    if keyword.status == KeywordStatus.ACTIVE.value or keyword.score >= 45:
        return 24 * 60
    return 72 * 60


def build_probe_plan(
    db: Session,
    registry: SourceRegistry,
    *,
    keyword_limit: int = 20,
    max_queries: int = 60,
) -> dict:
    keywords = db.scalars(
        select(Keyword)
        .where(Keyword.status.in_([KeywordStatus.TRENDING.value, KeywordStatus.ACTIVE.value, KeywordStatus.WATCHING.value]))
        .order_by(Keyword.score.desc(), Keyword.last_seen_at.desc())
        .limit(keyword_limit)
    ).all()
    connectors = [
        c for c in registry.list()
        if c.descriptor.enabled
        and source_enabled(db, c.descriptor.source_id, default=c.descriptor.enabled)
        and c.descriptor.query_mode == QueryMode.KEYWORD
    ]
    searchable_sources = [
        c.descriptor.source_id
        for c in connectors
        if _supports_intent(c.descriptor.capabilities, "BASE")
    ]
    probes: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for keyword in keywords:
        base = keyword.display_name.strip()
        candidates = [(base, "BASE")]
        for template in TEMPLATES:
            suffix = template.suffix_en if _is_ascii(base) else template.suffix_zh
            candidates.append((f"{base} {suffix}", template.intent))
        for query, intent in candidates:
            for connector in connectors:
                if not _supports_intent(connector.descriptor.capabilities, intent):
                    continue
                source_id = connector.descriptor.source_id
                key = (source_id, query.lower())
                if key in seen:
                    continue
                seen.add(key)
                probes.append(
                    {
                        "source_id": source_id,
                        "query": query,
                        "intent": intent,
                        "keyword_id": keyword.id,
                        "keyword": keyword.display_name,
                        "keyword_score": keyword.score,
                        "interval_minutes": _interval_minutes(keyword),
                        "priority": round(min(100.0, keyword.score + (10 if intent != "BASE" else 0)), 2),
                    }
                )
                if len(probes) >= max_queries:
                    break
            if len(probes) >= max_queries:
                break
        if len(probes) >= max_queries:
            break
    probes.sort(key=lambda row: row["priority"], reverse=True)
    return {"count": len(probes), "sources": searchable_sources, "probes": probes}


def sync_probe_tasks(
    db: Session,
    registry: SourceRegistry,
    *,
    keyword_limit: int = 20,
    max_queries: int = 60,
) -> dict:
    now = utc_now()
    plan = build_probe_plan(db, registry, keyword_limit=keyword_limit, max_queries=max_queries)
    scheduled_probes = list(plan["probes"])
    for connector in registry.list():
        if not connector.descriptor.enabled or not source_enabled(db, connector.descriptor.source_id, default=connector.descriptor.enabled):
            continue
        for scheduled in connector.scheduled_queries():
            scheduled_probes.append(
                {
                    "source_id": connector.descriptor.source_id,
                    "query": scheduled.query,
                    "intent": scheduled.intent,
                    "keyword_id": None,
                    "keyword": None,
                    "keyword_score": 0.0,
                    "interval_minutes": scheduled.interval_minutes,
                    "priority": scheduled.priority,
                }
            )
    existing = db.scalars(select(ProbeTask)).all()
    by_key = {(row.source_id, row.query.lower(), row.intent): row for row in existing}
    generated_keys: set[tuple[str, str, str]] = set()
    created = 0
    updated = 0

    for probe in scheduled_probes:
        key = (probe["source_id"], probe["query"].lower(), probe["intent"])
        generated_keys.add(key)
        task = by_key.get(key)
        if task is None:
            task = ProbeTask(
                source_id=probe["source_id"],
                query=probe["query"],
                intent=probe["intent"],
                keyword_id=probe["keyword_id"],
                priority=probe["priority"],
                interval_minutes=probe["interval_minutes"],
                active=True,
                next_run_at=now,
                created_at=now,
                updated_at=now,
            )
            db.add(task)
            created += 1
        else:
            task.keyword_id = probe["keyword_id"]
            task.priority = probe["priority"]
            task.interval_minutes = probe["interval_minutes"]
            was_inactive = not task.active
            task.active = True
            if was_inactive and task.next_run_at > now:
                task.next_run_at = now
            task.updated_at = now
            updated += 1

    paused = 0
    for task in existing:
        key = (task.source_id, task.query.lower(), task.intent)
        if task.active and key not in generated_keys:
            task.active = False
            task.updated_at = now
            paused += 1
    db.commit()
    return {"created": created, "updated": updated, "paused": paused, "active": len(scheduled_probes), "keyword_probes": plan["count"], "source_scheduled_probes": len(scheduled_probes) - plan["count"]}


def list_probe_tasks(db: Session, *, active_only: bool = False, limit: int = 200) -> list[dict]:
    stmt = select(ProbeTask)
    if active_only:
        stmt = stmt.where(ProbeTask.active.is_(True))
    rows = db.scalars(stmt.order_by(desc(ProbeTask.active), ProbeTask.next_run_at, desc(ProbeTask.priority)).limit(limit)).all()
    return [
        {
            "id": row.id,
            "source_id": row.source_id,
            "query": row.query,
            "intent": row.intent,
            "keyword_id": row.keyword_id,
            "priority": row.priority,
            "interval_minutes": row.interval_minutes,
            "active": row.active,
            "next_run_at": row.next_run_at,
            "last_run_at": row.last_run_at,
            "last_status": row.last_status,
            "failure_count": row.failure_count,
            "last_error": row.last_error,
            "lease_owner": row.lease_owner,
            "lease_until": row.lease_until,
        }
        for row in rows
    ]


COLLECTION_STALE_MINUTES = 30
PROBE_CLAIM_LEASE_MINUTES = COLLECTION_STALE_MINUTES + 5


def _recover_stale_runs(db: Session, *, now) -> int:
    cutoff = now - timedelta(minutes=COLLECTION_STALE_MINUTES)
    stale = db.scalars(
        select(CollectionRun).where(
            CollectionRun.status == CollectionRunStatus.RUNNING.value,
            CollectionRun.started_at < cutoff,
        )
    ).all()
    for run in stale:
        run.status = CollectionRunStatus.FAILED.value
        run.finished_at = now
        run.error = f"collection worker interrupted or exceeded {COLLECTION_STALE_MINUTES} minute stale-run threshold"
        if run.probe_task_id is not None:
            task = db.get(ProbeTask, run.probe_task_id)
            if task is not None and task.active:
                task.last_run_at = now
                task.last_status = CollectionRunStatus.FAILED.value
                task.failure_count = int(task.failure_count or 0) + 1
                task.last_error = run.error
                backoff = min(12 * 60, 15 * (2 ** min(task.failure_count - 1, 6)))
                task.next_run_at = now + timedelta(minutes=backoff)
                task.lease_owner = None
                task.lease_until = None
                task.updated_at = now
    if stale:
        db.commit()
    return len(stale)


def _normalize_worker_id(worker_id: str | None) -> str:
    normalized = (worker_id or f"collection-worker:{os.getpid()}").strip()[:200]
    if not normalized:
        raise ValueError("worker_id must not be empty")
    return normalized


def _claim_due_task(db: Session, task_id: int, *, now, worker_id: str | None = None) -> bool:
    worker_id = _normalize_worker_id(worker_id)
    lease_until = now + timedelta(minutes=PROBE_CLAIM_LEASE_MINUTES)
    result = db.execute(
        update(ProbeTask)
        .where(
            ProbeTask.id == task_id,
            ProbeTask.active.is_(True),
            ProbeTask.next_run_at <= now,
            or_(ProbeTask.lease_until.is_(None), ProbeTask.lease_until <= now),
        )
        .values(lease_owner=worker_id, lease_until=lease_until, updated_at=now)
    )
    db.commit()
    return result.rowcount == 1


def _release_task_claim(
    db: Session,
    task_id: int,
    *,
    worker_id: str,
    next_run_at,
    last_run_at,
    last_status: str,
    failure_count: int,
    last_error: str | None,
    updated_at,
) -> bool:
    result = db.execute(
        update(ProbeTask)
        .where(ProbeTask.id == task_id, ProbeTask.lease_owner == worker_id)
        .values(
            next_run_at=next_run_at,
            last_run_at=last_run_at,
            last_status=last_status,
            failure_count=failure_count,
            last_error=last_error,
            lease_owner=None,
            lease_until=None,
            updated_at=updated_at,
        )
    )
    db.commit()
    return result.rowcount == 1


def run_due_probe_tasks(
    db: Session,
    registry: SourceRegistry,
    *,
    limit: int = 10,
    worker_id: str | None = None,
    progress_callback: Callable[[], None] | None = None,
) -> dict:
    worker_id = _normalize_worker_id(worker_id)
    now = utc_now()
    recovered_stale_runs = _recover_stale_runs(db, now=now)
    task_ids = db.scalars(
        select(ProbeTask.id)
        .where(
            ProbeTask.active.is_(True),
            ProbeTask.next_run_at <= now,
            or_(ProbeTask.lease_until.is_(None), ProbeTask.lease_until <= now),
        )
        .order_by(desc(ProbeTask.priority), ProbeTask.next_run_at)
        .limit(limit)
    ).all()
    results: list[dict] = []
    claimed = 0
    for task_id in task_ids:
        claim_time = utc_now()
        if not _claim_due_task(db, task_id, now=claim_time, worker_id=worker_id):
            continue
        claimed += 1
        task = db.get(ProbeTask, task_id)
        if task is None or not task.active:
            continue
        task_failure_count = int(task.failure_count or 0)
        try:
            result = execute_collection(
                db,
                registry,
                source_id=task.source_id,
                query=CollectorQuery(query=task.query),
                intent=task.intent,
                probe_task_id=task.id,
                worker_id=worker_id,
            )
            completed = utc_now()
            if result.get("status") == CollectionRunStatus.SKIPPED.value:
                status = CollectionRunStatus.SKIPPED.value
                error = "source circuit open"
                open_until = result.get("circuit_open_until")
                next_run_at = open_until if open_until and open_until > completed else completed + timedelta(minutes=15)
            else:
                status = CollectionRunStatus.SUCCEEDED.value
                error = None
                next_run_at = completed + timedelta(minutes=task.interval_minutes)
            released = _release_task_claim(
                db,
                task_id,
                worker_id=worker_id,
                next_run_at=next_run_at,
                last_run_at=completed,
                last_status=status,
                failure_count=0 if status == CollectionRunStatus.SUCCEEDED.value else task_failure_count,
                last_error=error,
                updated_at=completed,
            )
            results.append({"task_id": task_id, "worker_id": worker_id, "lease_lost": not released, **result})
            if progress_callback is not None:
                progress_callback()
        except Exception as exc:
            db.rollback()
            failed = utc_now()
            # bounded exponential backoff: 15m, 30m, 60m, ... up to 12h
            failure_count = task_failure_count + 1
            backoff = min(12 * 60, 15 * (2 ** min(failure_count - 1, 6)))
            error = str(exc)[:20_000]
            released = _release_task_claim(
                db,
                task_id,
                worker_id=worker_id,
                next_run_at=failed + timedelta(minutes=backoff),
                last_run_at=failed,
                last_status=CollectionRunStatus.FAILED.value,
                failure_count=failure_count,
                last_error=error,
                updated_at=failed,
            )
            results.append({"task_id": task_id, "worker_id": worker_id, "lease_lost": not released, "status": "FAILED", "error": error})
            if progress_callback is not None:
                progress_callback()
    return {
        "due": len(task_ids),
        "claimed": claimed,
        "worker_id": worker_id,
        "executed": len(results),
        "recovered_stale_runs": recovered_stale_runs,
        "results": results,
    }
