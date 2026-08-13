#!/usr/bin/env python3
"""Execute real PostgreSQL runtime, migration, concurrency, and recovery checks."""

from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from threading import Barrier
from urllib.parse import urlsplit
from uuid import uuid4

from alembic import command
from alembic.config import Config
from fastapi import HTTPException
from sqlalchemy import create_engine, delete, func, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.api import auth as auth_api
from app.core.time import utc_now
from app.db.models import (
    AlertEvent,
    AlertRule,
    ApiToken,
    EmailDeliveryRecord,
    ProbeTask,
    User,
    UserSession,
)
from app.domain.schemas import UserPatch
from app.services.auth import Principal, create_user
from app.services.email_delivery_queue import enqueue_alert_emails
from app.services.probes import _claim_due_task


WORKERS = 8
REQUIRED_REVISION = "0031_login_rate_limits"


def _migrate(root: Path) -> None:
    config = Config(str(root / "backend" / "alembic.ini"))
    config.set_main_option("script_location", str(root / "backend" / "alembic"))
    command.upgrade(config, "head")


def _owner_principal() -> Principal:
    return Principal(
        actor="postgres-runtime-owner",
        role="OWNER",
        user_id=None,
        auth_type="runtime_e2e",
        scopes=frozenset({"read", "write", "admin"}),
    )


def _create_fixture(factory: sessionmaker, prefix: str) -> tuple[list[int], int, int]:
    now = utc_now()
    with factory() as db:
        owners = [
            create_user(db, f"{prefix}-owner-{index}", "RuntimeOwnerPassword-2026!", role="OWNER")
            for index in range(3)
        ]
        task = ProbeTask(
            source_id=f"runtime-{prefix}",
            query="postgres runtime claim",
            intent="BASE",
            priority=10,
            interval_minutes=60,
            active=True,
            next_run_at=now - timedelta(seconds=1),
            created_at=now,
            updated_at=now,
        )
        rule = AlertRule(
            name=f"runtime-rule-{prefix}",
            enabled=True,
            min_score=0,
            max_risk_score=100,
            min_evidence_count=0,
            stages=[],
            keyword_contains=[],
            cooldown_minutes=0,
            created_at=now,
            updated_at=now,
        )
        event = AlertEvent(
            alert_rule_id=None,
            event_key=f"runtime-event-{prefix}",
            status="NEW",
            priority=1,
            title="PostgreSQL runtime event",
            message="Runtime queue idempotency verification",
            score=80,
            risk_score=10,
            created_at=now,
        )
        db.add_all([*owners, task, rule])
        db.flush()
        event.alert_rule_id = rule.id
        db.add(event)
        db.flush()
        db.commit()
        return [owner.id for owner in owners], task.id, event.id


def _patch_owner(factory: sessionmaker, user_id: int, barrier: Barrier) -> str:
    barrier.wait()
    with factory() as db:
        try:
            auth_api.admin_patch_user(
                user_id,
                UserPatch(role="ADMIN"),
                principal=_owner_principal(),
                db=db,
            )
            return "committed"
        except HTTPException as exc:
            db.rollback()
            return f"http-{exc.status_code}"


def _claim_task(factory: sessionmaker, task_id: int, worker_index: int, barrier: Barrier) -> bool:
    barrier.wait()
    with factory() as db:
        return _claim_due_task(
            db,
            task_id,
            now=utc_now(),
            worker_id=f"postgres-runtime-worker-{worker_index}",
        )


def _enqueue_email(factory: sessionmaker, event_id: int, barrier: Barrier) -> dict:
    barrier.wait()
    with factory() as db:
        result = enqueue_alert_emails(
            db,
            recipients=["runtime@example.invalid"],
            alert_event_ids={event_id},
            data_class="ALERT_EVENT",
        )
        db.commit()
        return result


def _enabled_owner_count(factory: sessionmaker, prefix: str) -> int:
    with factory() as db:
        return db.scalar(
            select(func.count()).select_from(User).where(
                User.username.like(f"{prefix}-owner-%"),
                User.role == "OWNER",
                User.enabled.is_(True),
            )
        ) or 0


def _cleanup(factory: sessionmaker, prefix: str) -> None:
    with factory() as db:
        user_ids = list(db.scalars(select(User.id).where(User.username.like(f"{prefix}-owner-%"))))
        event_ids = list(db.scalars(select(AlertEvent.id).where(AlertEvent.event_key == f"runtime-event-{prefix}")))
        db.execute(delete(EmailDeliveryRecord).where(EmailDeliveryRecord.alert_event_id.in_(event_ids)))
        db.execute(delete(AlertEvent).where(AlertEvent.id.in_(event_ids)))
        db.execute(delete(AlertRule).where(AlertRule.name == f"runtime-rule-{prefix}"))
        db.execute(delete(ProbeTask).where(ProbeTask.source_id == f"runtime-{prefix}"))
        if user_ids:
            db.execute(delete(UserSession).where(UserSession.user_id.in_(user_ids)))
            db.execute(delete(ApiToken).where(ApiToken.user_id.in_(user_ids)))
            db.execute(delete(User).where(User.id.in_(user_ids)))
        db.commit()


def main() -> int:
    database_url = os.getenv("DATABASE_URL", "")
    report: dict = {
        "status": "FAIL",
        "database_url_scheme": database_url.split(":", 1)[0] if ":" in database_url else "",
        "workers": WORKERS,
        "concurrency_attempts": 0,
        "checks": {},
    }
    if not database_url.startswith("postgresql"):
        report["error"] = "DATABASE_URL must use PostgreSQL"
        print(json.dumps(report, sort_keys=True))
        return 1

    root = Path(__file__).resolve().parents[1]
    prefix = f"pg-e2e-{uuid4().hex}"
    expected_database = urlsplit(database_url).path.lstrip("/")
    if not expected_database:
        report["error"] = "DATABASE_URL must include a target database name"
        print(json.dumps(report, sort_keys=True))
        return 1
    engine = create_engine(database_url, future=True, pool_pre_ping=True, pool_size=WORKERS, max_overflow=WORKERS)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    try:
        _migrate(root)
        with factory() as db:
            postgres_version = db.execute(text("SELECT current_setting('server_version')")).scalar_one()
            revision = db.execute(text("SELECT version_num FROM alembic_version")).scalar_one_or_none()
            database_name = db.execute(text("SELECT current_database()")).scalar_one()
        report.update(
            {
                "postgres_version": postgres_version,
                "migration_revision": revision,
                "database": database_name,
                "expected_database": expected_database,
            }
        )
        report["checks"]["fresh_migration"] = revision == REQUIRED_REVISION
        report["checks"]["application_connection"] = database_name == expected_database

        owner_ids, task_id, event_id = _create_fixture(factory, prefix)

        owner_barrier = Barrier(len(owner_ids))
        with ThreadPoolExecutor(max_workers=len(owner_ids)) as executor:
            owner_results = list(
                executor.map(
                    lambda args: _patch_owner(factory, args[0], owner_barrier),
                    [(user_id,) for user_id in owner_ids],
                )
            )
        owner_count = _enabled_owner_count(factory, prefix)
        report["owner_concurrency"] = {"workers": len(owner_ids), "results": sorted(owner_results), "enabled_owners": owner_count}
        report["checks"]["owner_invariant"] = sorted(owner_results) == ["committed", "committed", "http-409"] and owner_count == 1

        claim_barrier = Barrier(WORKERS)
        with ThreadPoolExecutor(max_workers=WORKERS) as executor:
            claim_results = list(
                executor.map(
                    lambda index: _claim_task(factory, task_id, index, claim_barrier),
                    range(WORKERS),
                )
            )
        claim_count = sum(claim_results)
        report["task_claim_concurrency"] = {"workers": WORKERS, "claimed": claim_count}
        report["checks"]["exclusive_task_claim"] = claim_count == 1

        queue_barrier = Barrier(WORKERS)
        with ThreadPoolExecutor(max_workers=WORKERS) as executor:
            queue_results = list(
                executor.map(
                    lambda _index: _enqueue_email(factory, event_id, queue_barrier),
                    range(WORKERS),
                )
            )
        with factory() as db:
            queue_count = db.scalar(select(func.count()).select_from(EmailDeliveryRecord).where(EmailDeliveryRecord.alert_event_id == event_id)) or 0
        created_count = sum(result["created"] for result in queue_results)
        duplicate_count = sum(result["duplicates"] for result in queue_results)
        report["queue_idempotency"] = {"workers": WORKERS, "rows": queue_count, "created": created_count, "duplicates": duplicate_count}
        report["checks"]["queue_idempotency"] = queue_count == 1 and created_count == 1 and duplicate_count == WORKERS - 1

        engine.dispose()
        with factory() as db:
            recovered_database = db.execute(text("SELECT current_database()")).scalar_one()
        report["checks"]["connection_recovery"] = recovered_database == expected_database
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        try:
            _cleanup(factory, prefix)
        finally:
            engine.dispose()

    report["concurrency_attempts"] = 3 + WORKERS + WORKERS
    report["status"] = "PASS" if report["checks"] and all(report["checks"].values()) else "FAIL"
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
