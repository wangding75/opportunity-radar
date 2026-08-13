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
    subprocess.run([sys.executable, "-m", "alembic", *args], cwd=BACKEND, env=env, check=True, stdout=subprocess.DEVNULL)


def main() -> int:
    fd, db_path = tempfile.mkstemp(prefix="opportunity-radar-upgrade-060-070-", suffix=".db")
    os.close(fd)
    try:
        db_url = f"sqlite:///{db_path}"
        run_alembic(db_url, "upgrade", "0006_product_workflow_alerts")
        with sqlite3.connect(db_path) as conn:
            now = "2026-08-12 06:00:00"
            conn.execute("INSERT INTO keywords (id,canonical,display_name,status,first_seen_at,last_seen_at,observation_count,source_count,score) VALUES (1,'legacy','legacy','ACTIVE',?,?,3,2,25)", (now, now))
            conn.execute("INSERT INTO opportunities (id,opportunity_key,keyword_id,title,stage,score,demand_score,supply_score,execution_score,cross_source_score,saturation_score,risk_score,evidence_count,first_seen_at,last_seen_at,updated_at,summary,target_user,business_model,monetization,risk_notes,analysis_provider,analysis_status,related_keyword_count,analysis_signature,analysis_attempt_count) VALUES (1,'cluster:1',1,'legacy','DISCOVERY',25,5,5,5,5,0,0,3,?,?,?,'','','','','','heuristic','READY',1,'abc',0)", (now, now, now))
            conn.execute("INSERT INTO opportunity_keywords (opportunity_id,keyword_id,role,weight) VALUES (1,1,'PRIMARY',25)")
            conn.execute("INSERT INTO opportunity_research (opportunity_id,status,starred,priority,notes,tags,created_at,updated_at) VALUES (1,'TRACKING',1,5,'keep','[]',?,?)", (now, now))
            conn.commit()
        run_alembic(db_url, "upgrade", "0007_scale_correctness")
        with sqlite3.connect(db_path) as conn:
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            required = {"keyword_relation_sources", "opportunity_cluster_versions", "opportunity_lineage", "alert_evaluation_queue", "worker_heartbeats"}
            assert required <= tables, sorted(required - tables)
            assert conn.execute("SELECT notes FROM opportunity_research WHERE opportunity_id=1").fetchone()[0] == "keep"
            row = conn.execute("SELECT cluster_signature,cluster_generation FROM opportunities WHERE id=1").fetchone()
            assert row == ("", 0), row
            assert conn.execute("SELECT version_num FROM alembic_version").fetchone()[0] == "0007_scale_correctness"
        print("UPGRADE_060_TO_070_PASS")
        return 0
    finally:
        Path(db_path).unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
