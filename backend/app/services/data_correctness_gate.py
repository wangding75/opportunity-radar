"""Deterministic aggregate gate for the persisted data-correctness chain."""

from __future__ import annotations

from app.services.alert_replay_backtest_audit import audit_alert_replay_backtest
from app.services.keyword_trend_graph_audit import audit_keyword_trend_graph
from app.services.normalization_audit import audit_observation_normalization
from app.services.opportunity_score_lineage_audit import audit_opportunity_score_lineage


DATA_CORRECTNESS_GATE_VERSION = "data-correctness-v1"


def run_data_correctness_gate(db) -> dict:
    """Run all persisted-chain audits and return a stable, serializable result.

    No audit mutates the database and the aggregate deliberately contains no
    wall-clock timestamp. This makes the report suitable for deterministic
    regression comparisons while preserving each audit's detailed violations.
    """

    audits = {
        "observation_normalization": audit_observation_normalization(db),
        "keyword_trend_graph": audit_keyword_trend_graph(db),
        "opportunity_score_lineage": audit_opportunity_score_lineage(db),
        "alert_replay_backtest": audit_alert_replay_backtest(db),
    }
    violations = [
        {"audit": name, **violation}
        for name, result in audits.items()
        for violation in result.get("violations", [])
    ]
    real_data_collected = sum(int(result.get("summary", {}).get("real_data_collected", 0)) for result in audits.values())
    return {
        "gate_id": "opportunity-radar-data-correctness",
        "gate_version": DATA_CORRECTNESS_GATE_VERSION,
        "status": "PASS" if all(result.get("status") == "PASS" for result in audits.values()) else "FAIL",
        "checks": {name: result.get("status") == "PASS" for name, result in audits.items()},
        "violations": violations,
        "audits": {
            name: {
                "status": result.get("status"),
                "contract_version": result.get("contract_version"),
                "summary": result.get("summary", {}),
                "violation_count": len(result.get("violations", [])),
            }
            for name, result in audits.items()
        },
        "summary": {
            "audit_count": len(audits),
            "passed_audits": sum(result.get("status") == "PASS" for result in audits.values()),
            "violation_count": len(violations),
            "real_data_collected": real_data_collected,
            "data_policy": "SYNTHETIC_OR_MOCK_ONLY",
        },
    }
