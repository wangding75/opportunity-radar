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
    fd, db_path = tempfile.mkstemp(prefix="opportunity-radar-upgrade-070-071-", suffix=".db")
    os.close(fd)
    try:
        db_url = f"sqlite:///{db_path}"
        run_alembic(db_url, "upgrade", "0007_scale_correctness")
        with sqlite3.connect(db_path) as conn:
            now = "2026-08-12 06:00:00"
            conn.execute(
                "INSERT INTO keywords (id,canonical,display_name,status,first_seen_at,last_seen_at,observation_count,source_count,score) "
                "VALUES (1,'upgrade-071','upgrade-071','ACTIVE',?,?,3,2,20)",
                (now, now),
            )
            conn.execute(
                "INSERT INTO opportunities (id,opportunity_key,keyword_id,title,stage,score,demand_score,supply_score,execution_score,cross_source_score,saturation_score,risk_score,evidence_count,first_seen_at,last_seen_at,updated_at,summary,target_user,business_model,monetization,risk_notes,analysis_provider,analysis_status,related_keyword_count,analysis_signature,analysis_attempt_count,cluster_signature,cluster_generation) "
                "VALUES (1,'upgrade-071',1,'upgrade-071','DISCOVERY',20,0,0,0,0,0,0,0,?,?,?,'','','','','','heuristic','READY',1,'',0,'',0)",
                (now, now, now),
            )
            conn.execute(
                "INSERT INTO alert_evaluation_queue (opportunity_id,reason,queued_at,attempt_count,last_error) "
                "VALUES (1,'UPGRADE_TEST',?,2,'old-error')",
                (now,),
            )
            conn.commit()
        run_alembic(db_url, "upgrade", "0008_review_correctness")
        with sqlite3.connect(db_path) as conn:
            row = conn.execute(
                "SELECT attempt_count,revision,claim_until,next_retry_at FROM alert_evaluation_queue WHERE reason='UPGRADE_TEST'"
            ).fetchone()
            assert row == (2, 0, None, None), row
            assert conn.execute("SELECT version_num FROM alembic_version").fetchone()[0] == "0008_review_correctness"
        print("UPGRADE_070_TO_071_PASS")
        return 0
    finally:
        Path(db_path).unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
