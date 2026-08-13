from __future__ import annotations

import os
import tempfile
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
fd, db_path = tempfile.mkstemp(prefix="opp-radar-upgrade-050-060-", suffix=".db")
os.close(fd)
try:
    url = f"sqlite:///{db_path}"
    os.environ["DATABASE_URL"] = url
    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "0005_analysis_queue_observability")
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO keywords (canonical, display_name, status, first_seen_at, last_seen_at, observation_count, source_count, score) VALUES ('seed','seed','WATCHING',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP,0,0,10)"))
        keyword_id = conn.execute(text("SELECT id FROM keywords WHERE canonical='seed'" )).scalar_one()
        conn.execute(text("INSERT INTO opportunities (opportunity_key, keyword_id, title, stage, score, demand_score, supply_score, execution_score, cross_source_score, saturation_score, risk_score, evidence_count, first_seen_at, last_seen_at, updated_at, summary, target_user, business_model, monetization, risk_notes, analysis_provider, analysis_status, related_keyword_count, analysis_signature, analysis_attempt_count) VALUES ('upgrade-test', :keyword_id, 'upgrade test','DISCOVERY',10,0,0,0,0,0,0,0,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP,'','','','','','heuristic','READY',1,'',0)"), {"keyword_id": keyword_id})
    command.upgrade(cfg, "0006_product_workflow_alerts")
    with engine.connect() as conn:
        tables = set(inspect(conn).get_table_names())
        required = {"opportunity_research", "alert_rules", "alert_events", "source_preferences", "audit_logs", "seed_keywords"}
        assert required <= tables, sorted(required - tables)
        assert conn.execute(text("SELECT count(*) FROM opportunities WHERE opportunity_key='upgrade-test'" )).scalar_one() == 1
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "0006_product_workflow_alerts"
    print("UPGRADE_050_TO_060_PASS")
finally:
    Path(db_path).unlink(missing_ok=True)
