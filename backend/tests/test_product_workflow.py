from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _seed_opportunity():
    payload = {"records": [
        {"source_id": "market_a", "query": "AI短剧", "item_type": "PRODUCT", "title": "AI短剧 自动剪辑 工具", "text": "批量生成 软件 变现"},
        {"source_id": "jobs_a", "query": "AI短剧", "item_type": "JOB", "title": "AI短剧 剪辑运营 招聘", "text": "矩阵运营"},
        {"source_id": "trend_a", "query": "AI短剧", "item_type": "TREND", "title": "AI短剧 搜索热度", "text": "趋势增长"},
    ]}
    assert client.post("/api/v1/import", json=payload).status_code == 200
    rows = client.get("/api/v1/opportunities", params={"min_score": 1}).json()
    assert rows
    return rows[0]


def test_research_state_is_persistent_and_filterable():
    opp = _seed_opportunity()
    response = client.patch(
        f"/api/v1/opportunities/{opp['id']}/research",
        json={"status": "TRACKING", "starred": True, "priority": 5, "notes": "重点验证", "tags": ["短剧", "AI", "短剧"]},
    )
    assert response.status_code == 200
    state = response.json()
    assert state["status"] == "TRACKING"
    assert state["starred"] is True
    assert state["priority"] == 5
    assert state["tags"] == ["短剧", "AI"]

    detail = client.get(f"/api/v1/opportunities/{opp['id']}").json()
    assert detail["research"]["status"] == "TRACKING"
    assert detail["research"]["notes"] == "重点验证"
    filtered = client.get("/api/v1/opportunities", params={"research_status": "TRACKING", "starred": True}).json()
    assert [row["id"] for row in filtered] == [opp["id"]]


def test_alert_rule_creates_internal_event_and_acknowledges():
    opp = _seed_opportunity()
    rule = client.post(
        "/api/v1/alerts/rules",
        json={"name": "高分机会", "min_score": 1, "max_risk_score": 100, "min_evidence_count": 1, "cooldown_minutes": 60},
    )
    assert rule.status_code == 200
    evaluated = client.post("/api/v1/alerts/evaluate")
    assert evaluated.status_code == 200
    assert evaluated.json()["created"] >= 1
    events = client.get("/api/v1/alerts/events", params={"status": "NEW"}).json()
    event = next(row for row in events if row["opportunity_id"] == opp["id"])
    patched = client.patch(f"/api/v1/alerts/events/{event['id']}", json={"status": "ACKNOWLEDGED"})
    assert patched.status_code == 200
    assert patched.json()["status"] == "ACKNOWLEDGED"
    # Same evidence signature must not produce duplicate events.
    assert client.post("/api/v1/alerts/evaluate").json()["created"] == 0


def test_source_preference_disables_collection_and_probe_generation():
    response = client.patch("/api/v1/sources/github/preference", json={"enabled": False, "note": "manual pause"})
    assert response.status_code == 200
    sources = {row["source_id"]: row for row in client.get("/api/v1/sources").json()}
    assert sources["github"]["runtime_enabled"] is False
    assert sources["github"]["preference_note"] == "manual pause"
    collected = client.post("/api/v1/collect/github", json={"query": "test", "limit": 1})
    assert collected.status_code == 409
    assert "disabled" in collected.json()["detail"]


def test_observation_search_export_and_audit_log():
    _seed_opportunity()
    searched = client.get("/api/v1/observations", params={"q": "自动剪辑"})
    assert searched.status_code == 200
    assert searched.json()["total"] >= 1
    assert any("自动剪辑" in row["title"] for row in searched.json()["items"])

    csv_response = client.get("/api/v1/exports/opportunities.csv")
    assert csv_response.status_code == 200
    assert "text/csv" in csv_response.headers["content-type"]
    assert "title" in csv_response.text

    audit = client.get("/api/v1/audit").json()
    assert any(row["action"] == "POST" and row["resource"] == "/api/v1/import" for row in audit)


def test_dashboard_exposes_product_workflow_metrics():
    opp = _seed_opportunity()
    client.patch(f"/api/v1/opportunities/{opp['id']}/research", json={"status": "TRACKING", "starred": True})
    client.post("/api/v1/alerts/rules", json={"name": "dashboard-rule", "min_score": 1, "min_evidence_count": 1})
    client.post("/api/v1/alerts/evaluate")
    totals = client.get("/api/v1/dashboard").json()["totals"]
    assert totals["starred_opportunities"] == 1
    assert totals["tracking_opportunities"] == 1
    assert totals["unread_alerts"] >= 1


def test_watch_keyword_creates_monitoring_seed_and_probe_candidate():
    created = client.post("/api/v1/watch-keywords", json={"keyword": "短剧出海", "priority": 5, "notes": "长期监控"})
    assert created.status_code == 200
    row = created.json()
    assert row["canonical"] == "短剧出海"
    assert row["enabled"] is True
    keywords = client.get("/api/v1/keywords").json()
    watched = next(item for item in keywords if item["canonical"] == "短剧出海")
    assert watched["status"] == "WATCHING"
    assert watched["score"] >= 35
    plan = client.get("/api/v1/probes/plan").json()
    assert any(p["keyword"] == "短剧出海" for p in plan["probes"])

    patched = client.patch(f"/api/v1/watch-keywords/{row['id']}", json={"enabled": False})
    assert patched.status_code == 200
    assert patched.json()["enabled"] is False


def test_csv_export_neutralizes_spreadsheet_formulas():
    payload = {"records": [{"source_id": "csv-test", "query": "formula", "item_type": "PRODUCT", "title": "=HYPERLINK(\"https://evil\")", "text": "formula tool"}]}
    assert client.post("/api/v1/import", json=payload).status_code == 200
    response = client.get("/api/v1/exports/observations.csv")
    assert response.status_code == 200
    assert "'=HYPERLINK" in response.text
