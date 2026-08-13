#!/usr/bin/env python3
"""Exercise shared login throttling with independent PostgreSQL workers."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from threading import Barrier
from uuid import uuid4

from alembic import command
from alembic.config import Config
from sqlalchemy import delete, func, select, text

from app.core.time import utc_now
from app.db.models import LoginRateLimit
from app.db.session import SessionLocal
from app.services.auth import _login_rate_limit_keys, login_rate_limit_retry_after, record_login_failure
from app.services.auth import settings


WORKERS = 8


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _migrate(root: Path) -> None:
    config = Config(str(root / "backend" / "alembic.ini"))
    config.set_main_option("script_location", str(root / "backend" / "alembic"))
    command.upgrade(config, "head")


def main() -> int:
    _migrate(_root())
    prefix = f"t137-{uuid4().hex}"
    client_ip = f"198.51.100.{(int(uuid4().hex[:2], 16) % 200) + 1}"
    username = f"{prefix}@example.invalid"
    barrier = Barrier(WORKERS)
    started = utc_now()

    def worker() -> str:
        barrier.wait()
        with SessionLocal() as db:
            record_login_failure(db, client_ip, username)
            db.commit()
        return "committed"

    results = []
    try:
        with SessionLocal() as db:
            postgres_version = db.execute(text("SELECT current_setting('server_version')")).scalar_one()
            revision = db.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        with ThreadPoolExecutor(max_workers=WORKERS) as executor:
            results = list(executor.map(lambda _index: worker(), range(WORKERS)))
        with SessionLocal() as db:
            throttled = login_rate_limit_retry_after(db, client_ip, username) is not None
            rows = db.scalar(
                select(func.count())
                .select_from(LoginRateLimit)
                .where(LoginRateLimit.key.in_(_login_rate_limit_keys(client_ip, username)))
            ) or 0
            recovered = login_rate_limit_retry_after(
                db,
                client_ip,
                username,
                now=started + timedelta(seconds=settings.login_rate_limit_window_seconds + 1),
            ) is None
        checks = {
            "migration_head": revision == "0031_login_rate_limits",
            "shared_counter_visible": rows == 2,
            "throttle_after_concurrent_failures": throttled,
            "window_recovery": recovered,
        }
        report = {
            "status": "PASS" if all(checks.values()) and all(result == "committed" for result in results) else "FAIL",
            "postgres_version": postgres_version,
            "migration_revision": revision,
            "workers": WORKERS,
            "attempts": len(results),
            "client_ip_digest_only": True,
            "checks": checks,
            "real_data_collected": 0,
        }
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 0 if report["status"] == "PASS" else 1
    finally:
        with SessionLocal() as db:
            db.execute(delete(LoginRateLimit).where(LoginRateLimit.key.in_(_login_rate_limit_keys(client_ip, username))))
            db.commit()


if __name__ == "__main__":
    raise SystemExit(main())
