from __future__ import annotations

from sqlalchemy import select

from app.db.models import Keyword
from app.db.session import SessionLocal
from app.services.data_correctness_gate import run_data_correctness_gate


def test_data_correctness_gate_is_empty_pass_and_deterministic():
    with SessionLocal() as db:
        first = run_data_correctness_gate(db)
        second = run_data_correctness_gate(db)
        assert first == second
        assert first["status"] == "PASS"
        assert first["summary"] == {
            "audit_count": 4,
            "data_policy": "SYNTHETIC_OR_MOCK_ONLY",
            "passed_audits": 4,
            "real_data_collected": 0,
            "violation_count": 0,
        }


def test_data_correctness_gate_propagates_keyword_metric_drift():
    with SessionLocal() as db:
        keyword = Keyword(canonical="synthetic-gate-drift", display_name="Synthetic gate drift", observation_count=0, source_count=0)
        db.add(keyword)
        db.flush()
        keyword.observation_count = 1
        db.flush()
        result = run_data_correctness_gate(db)
        assert result["status"] == "FAIL"
        assert result["checks"]["keyword_trend_graph"] is False
        assert any(row["audit"] == "keyword_trend_graph" and row["rule"] == "keyword_observation_count" for row in result["violations"])
        assert db.scalar(select(Keyword.observation_count).where(Keyword.id == keyword.id)) == 1
