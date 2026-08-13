from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"


def run_alembic(db_url: str, *args: str) -> None:
    env = os.environ.copy()
    env["DATABASE_URL"] = db_url
    subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=BACKEND,
        env=env,
        check=True,
        stdout=subprocess.DEVNULL,
    )


def main() -> int:
    fd, db_path = tempfile.mkstemp(prefix="opportunity-radar-upgrade-", suffix=".db")
    os.close(fd)
    try:
        db_url = f"sqlite:///{db_path}"
        run_alembic(db_url, "upgrade", "0003_probe_scheduler_and_runs")
        with sqlite3.connect(db_path) as conn:
            now = "2026-08-12 04:00:00"
            conn.execute(
                """
                INSERT INTO keywords
                (id, canonical, display_name, status, first_seen_at, last_seen_at, observation_count, source_count, score)
                VALUES (1, 'legacy-topic', 'Legacy Topic', 'ACTIVE', ?, ?, 4, 2, 30.0)
                """,
                (now, now),
            )
            conn.execute(
                """
                INSERT INTO opportunities
                (id, opportunity_key, keyword_id, title, stage, score, demand_score, supply_score,
                 execution_score, cross_source_score, saturation_score, risk_score, evidence_count,
                 first_seen_at, last_seen_at, updated_at)
                VALUES (1, 'keyword:legacy-topic', 1, 'Legacy Topic', 'PRODUCTIZING', 40.0, 10.0, 20.0,
                        0.0, 10.0, 0.0, 0.0, 4, ?, ?, ?)
                """,
                (now, now, now),
            )
            conn.commit()

        run_alembic(db_url, "upgrade", "0004_clusters_analysis_health")
        with sqlite3.connect(db_path) as conn:
            row = conn.execute(
                "SELECT title, summary, analysis_provider, analysis_status, related_keyword_count, analysis_signature "
                "FROM opportunities WHERE id=1"
            ).fetchone()
            if row != ("Legacy Topic", "", "heuristic", "READY", 1, ""):
                raise AssertionError(f"unexpected migrated opportunity row: {row!r}")
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            required = {"opportunity_keywords", "source_health_states"}
            if not required <= tables:
                raise AssertionError(f"missing 0.4 tables: {sorted(required - tables)}")
        print("UPGRADE_030_TO_040_PASS")
        return 0
    finally:
        Path(db_path).unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
