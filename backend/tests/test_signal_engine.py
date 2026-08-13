from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.core.time import utc_now
from app.main import app

client = TestClient(app)


def _iso(days_ago: int) -> str:
    return (datetime.now(UTC) - timedelta(days=days_ago)).isoformat()


def test_cross_day_observations_are_not_deduplicated_and_trend_windows_exist():
    base = {
        "source_id": "trend_source",
        "query": "AI视频自动化",
        "external_id": "stable-item-1",
        "item_type": "TREND",
        "title": "AI视频自动化",
        "text": "AI视频 自动化 生成",
        "payload": {},
    }
    records = [dict(base, observed_at=_iso(days)) for days in (0, 1, 8, 31, 61)]
    response = client.post("/api/v1/import", json={"records": records})
    assert response.status_code == 200
    assert response.json()["inserted"] == 5

    keywords = client.get("/api/v1/keywords").json()
    keyword = next(row for row in keywords if row["canonical"] == "ai视频自动化")
    trend = client.get(f"/api/v1/keywords/{keyword['id']}/trend")
    assert trend.status_code == 200
    data = trend.json()
    assert data["windows"]["7d"] >= 2
    assert data["windows"]["30d"] >= 3
    assert data["windows"]["90d"] >= 5
    assert len(data["points"]) >= 5


def test_timezone_aware_input_is_normalized_and_pipeline_remains_comparable():
    payload = {
        "records": [
            {
                "source_id": "tz_source",
                "query": "跨境工具",
                "external_id": "tz-1",
                "item_type": "PRODUCT",
                "title": "跨境工具",
                "text": "自动化工具",
                "observed_at": "2026-08-12T10:00:00+08:00",
            },
            {
                "source_id": "tz_source_2",
                "query": "跨境工具",
                "external_id": "tz-2",
                "item_type": "JOB",
                "title": "跨境工具运营招聘",
                "text": "跨境 自动化",
                "observed_at": "2026-08-12T02:30:00Z",
            },
        ]
    }
    response = client.post("/api/v1/import", json=payload)
    assert response.status_code == 200
    assert response.json()["inserted"] == 2


def test_keyword_graph_opportunity_and_probe_plan_are_generated():
    payload = {
        "records": [
            {
                "source_id": "marketplace",
                "query": "短剧自动化",
                "external_id": "p-1",
                "item_type": "PRODUCT",
                "title": "短剧自动化工具",
                "text": "短剧 批量剪辑 工具 软件",
                "observed_at": _iso(0),
            },
            {
                "source_id": "jobs",
                "query": "短剧自动化",
                "external_id": "j-1",
                "item_type": "JOB",
                "title": "短剧自动化运营招聘",
                "text": "短剧 自动剪辑 矩阵运营",
                "observed_at": _iso(0),
            },
            {
                "source_id": "search_trend",
                "query": "短剧自动化",
                "external_id": "t-1",
                "item_type": "TREND",
                "title": "短剧自动化搜索增长",
                "text": "短剧 自动化 变现",
                "observed_at": _iso(1),
            },
        ]
    }
    response = client.post("/api/v1/import", json=payload)
    assert response.status_code == 200
    assert response.json()["inserted"] == 3

    keywords = client.get("/api/v1/keywords").json()
    keyword = next(row for row in keywords if row["canonical"] == "短剧自动化")

    graph = client.get("/api/v1/keyword-graph", params={"keyword_id": keyword["id"]})
    assert graph.status_code == 200
    assert graph.json()["edges"]

    opportunities = client.get("/api/v1/opportunities", params={"min_score": 1})
    assert opportunities.status_code == 200
    opportunity = next(row for row in opportunities.json() if row["title"] == "短剧自动化")
    assert opportunity["score"] > 0
    assert opportunity["demand_score"] > 0
    assert opportunity["supply_score"] > 0
    assert opportunity["execution_score"] > 0
    assert opportunity["cross_source_score"] > 0

    detail = client.get(f"/api/v1/opportunities/{opportunity['id']}")
    assert detail.status_code == 200
    assert len(detail.json()["evidence"]) >= 3

    probes = client.get("/api/v1/probes/plan", params={"keyword_limit": 10, "max_queries": 40})
    assert probes.status_code == 200
    data = probes.json()
    assert "github" in data["sources"]
    assert any(row["keyword"] == "短剧自动化" for row in data["probes"])
    github_intents = {row["intent"] for row in data["probes"] if row["source_id"] == "github"}
    assert github_intents <= {"BASE", "SUPPLY"}


def test_same_day_retry_is_idempotent():
    timestamp = utc_now().replace(hour=1, minute=2, second=3, microsecond=0).isoformat()
    record = {
        "source_id": "idempotent_source",
        "query": "同日幂等",
        "external_id": "same-1",
        "item_type": "CONTENT",
        "title": "同日幂等测试",
        "text": "同一条数据",
        "observed_at": timestamp,
    }
    first = client.post("/api/v1/import", json={"records": [record]})
    second = client.post("/api/v1/import", json={"records": [record]})
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["inserted"] == 1
    assert second.json()["duplicates"] == 1


def test_stale_keyword_is_archived_and_not_promoted_to_opportunity():
    old = (datetime.now(UTC) - timedelta(days=120)).isoformat()
    payload = {"records": [
        {
            "source_id": source,
            "query": "过期机会词",
            "external_id": f"old-{idx}",
            "item_type": "PRODUCT",
            "title": "过期机会词 工具",
            "text": "历史信号",
            "observed_at": old,
        }
        for idx, source in enumerate(("old_a", "old_b", "old_c"), start=1)
    ]}
    response = client.post("/api/v1/import", json=payload)
    assert response.status_code == 200
    keyword = next(row for row in client.get("/api/v1/keywords").json() if row["canonical"] == "过期机会词")
    assert keyword["status"] == "ARCHIVED"
    opportunities = client.get("/api/v1/opportunities").json()
    assert all(row["title"] != "过期机会词" for row in opportunities)


def test_business_risk_is_separate_from_opportunity_score():
    payload = {"records": [
        {
            "source_id": "risk_market",
            "query": "版权检测工具",
            "external_id": "risk-p",
            "item_type": "PRODUCT",
            "title": "版权检测工具",
            "text": "用于版权投诉和侵权风险检测",
            "observed_at": _iso(0),
            "evidence_quality": "C",
        },
        {
            "source_id": "risk_job",
            "query": "版权检测工具",
            "external_id": "risk-j",
            "item_type": "JOB",
            "title": "版权检测工具运营招聘",
            "text": "合规产品运营",
            "observed_at": _iso(0),
            "evidence_quality": "B",
        },
    ]}
    response = client.post("/api/v1/import", json=payload)
    assert response.status_code == 200
    opportunity = next(row for row in client.get("/api/v1/opportunities").json() if row["title"] == "版权检测工具")
    assert opportunity["score"] > 0
    assert opportunity["risk_score"] > 0


def test_same_day_metric_change_is_preserved():
    timestamp = utc_now().replace(hour=2, minute=0, second=0, microsecond=0).isoformat()
    base = {
        "source_id": "metric_source",
        "query": "repo metric",
        "external_id": "repo-1",
        "item_type": "REPOSITORY",
        "title": "demo/repo",
        "text": "automation",
        "observed_at": timestamp,
    }
    first = client.post("/api/v1/import", json={"records": [dict(base, payload={"stars": 10})]})
    second = client.post("/api/v1/import", json={"records": [dict(base, payload={"stars": 25})]})
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["inserted"] == 1
    assert second.json()["inserted"] == 1


def test_instrumented_observation_is_sanitized_and_schema_drift_is_reported():
    from app.db.models import RawObservation
    from app.db.session import SessionLocal

    common = {
        "source_id": "research_app",
        "query": "AI工具",
        "app_package": "com.example.app",
        "emulator_profile": "api35",
        "instrumentation_version": "1",
        "external_id": "item-1",
        "title": "联系 13800138000 test@example.com",
        "text": "公开结果",
        "url": "https://example.invalid/item?id=1&token=secret",
    }
    v1 = dict(common, app_version="1.0", payload={"rank": 1, "token": "secret", "user": {"email": "x@y.com"}})
    v2 = dict(common, app_version="2.0", payload={"rank": 1, "price": 99, "cookie": "secret"})
    first = client.post("/api/v1/instrumented-app/observations", json=[v1])
    second = client.post("/api/v1/instrumented-app/observations", json=[v2])
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["inserted"] == 1
    assert second.json()["inserted"] == 1

    with SessionLocal() as db:
        rows = db.query(RawObservation).filter(RawObservation.source_id == "research_app").order_by(RawObservation.id).all()
        assert len(rows) == 2
        assert "13800138000" not in rows[0].title
        assert "test@example.com" not in rows[0].title
        assert "token" not in rows[0].source_url
        assert "token" not in rows[0].raw_payload
        assert "email" not in rows[0].raw_payload.get("user", {})
        assert "cookie" not in rows[1].raw_payload

    drift = client.get("/api/v1/instrumented-app/schema-drift", params={"source_id": "research_app"})
    assert drift.status_code == 200
    data = drift.json()
    assert data["drift_detected"] is True
    assert len(data["versions"]) == 2
    assert "price" in data["versions"][1]["added_vs_previous"]


def test_manual_import_cannot_claim_official_api_evidence_quality():
    payload = {"records": [{
        "source_id": "spoofed",
        "query": "test",
        "item_type": "CONTENT",
        "title": "test",
        "evidence_quality": "A"
    }]}
    response = client.post("/api/v1/import", json=payload)
    assert response.status_code == 422
