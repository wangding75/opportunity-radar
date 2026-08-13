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
    fd, db_path = tempfile.mkstemp(prefix="opportunity-radar-upgrade-040-050-", suffix=".db")
    os.close(fd)
    try:
        db_url = f"sqlite:///{db_path}"
        run_alembic(db_url, "upgrade", "0004_clusters_analysis_health")
        with sqlite3.connect(db_path) as conn:
            now = "2026-08-12 05:00:00"
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
                 first_seen_at, last_seen_at, updated_at, summary, target_user, business_model,
                 monetization, risk_notes, analysis_provider, analysis_status, analyzed_at,
                 related_keyword_count, analysis_signature, analysis_error)
                VALUES (1, 'cluster:1', 1, 'Legacy Topic', 'PRODUCTIZING', 40.0, 10.0, 20.0,
                        0.0, 10.0, 0.0, 0.0, 4, ?, ?, ?, 'legacy summary', '', '', '', '',
                        'heuristic', 'READY', NULL, 1, 'abc', NULL)
                """,
                (now, now, now),
            )
            conn.execute(
                """
                INSERT INTO source_health_states
                (source_id, status, consecutive_failures, last_success_at, last_failure_at,
                 circuit_open_until, last_error, updated_at)
                VALUES ('legacy_source', 'HEALTHY', 0, ?, NULL, NULL, NULL, ?)
                """,
                (now, now),
            )
            conn.commit()

        run_alembic(db_url, "upgrade", "0005_analysis_queue_observability")
        with sqlite3.connect(db_path) as conn:
            row = conn.execute(
                "SELECT summary, analysis_attempt_count, analysis_last_attempt_at, analysis_next_retry_at "
                "FROM opportunities WHERE id=1"
            ).fetchone()
            if row != ("legacy summary", 0, None, None):
                raise AssertionError(f"unexpected 0.5 opportunity migration result: {row!r}")
            health = conn.execute(
                "SELECT total_runs, successful_runs, failed_runs, rate_limited_runs, avg_duration_ms, "
                "last_fetched, last_inserted FROM source_health_states WHERE source_id='legacy_source'"
            ).fetchone()
            if health != (0, 0, 0, 0, 0.0, 0, 0):
                raise AssertionError(f"unexpected 0.5 source health migration result: {health!r}")
            revision = conn.execute("SELECT version_num FROM alembic_version").fetchone()[0]
            if revision != "0005_analysis_queue_observability":
                raise AssertionError(f"unexpected head revision: {revision}")
        print("UPGRADE_040_TO_050_PASS")
        return 0
    finally:
        Path(db_path).unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
