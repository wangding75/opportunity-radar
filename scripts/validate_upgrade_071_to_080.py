from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"

with tempfile.TemporaryDirectory(prefix="opp-upgrade-071-080-") as td:
    db = Path(td) / "upgrade.db"
    env = os.environ.copy(); env["DATABASE_URL"] = f"sqlite:///{db}"
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "0008_review_correctness"], cwd=BACKEND, env=env, check=True, stdout=subprocess.DEVNULL)
    con = sqlite3.connect(db)
    try:
        con.execute("INSERT INTO keywords(canonical,display_name,status,first_seen_at,last_seen_at,observation_count,source_count,score) VALUES('upgrade','upgrade','ACTIVE',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP,1,1,10)")
        keyword_id = con.execute("SELECT id FROM keywords WHERE canonical='upgrade'").fetchone()[0]
        con.execute("INSERT INTO opportunities(opportunity_key,keyword_id,title,stage,score,demand_score,supply_score,execution_score,cross_source_score,saturation_score,risk_score,evidence_count,first_seen_at,last_seen_at,updated_at,summary,target_user,business_model,monetization,risk_notes,analysis_provider,analysis_status,related_keyword_count,analysis_signature,analysis_attempt_count,cluster_signature,cluster_generation) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP,'','','','','','heuristic','READY',1,'',0,'',0)", ('opp:upgrade',keyword_id,'upgrade','EARLY',42,1,2,3,4,0,5,1))
        con.commit()
    finally:
        con.close()
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=BACKEND, env=env, check=True, stdout=subprocess.DEVNULL)
    con = sqlite3.connect(db)
    try:
        rev = con.execute("SELECT version_num FROM alembic_version").fetchone()[0]
        assert rev == "0009_product_hardening"
        row = con.execute("SELECT score,score_version FROM opportunities WHERE opportunity_key='opp:upgrade'").fetchone()
        assert row == (42.0, "score-v1")
        for table in ("users","user_sessions","api_tokens","opportunity_score_snapshots"):
            assert con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
    finally:
        con.close()
print("UPGRADE_071_TO_080_PASS")
