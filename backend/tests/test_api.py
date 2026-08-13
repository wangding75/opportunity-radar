from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_and_sources():
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/ready").json()["status"] == "ready"
    sources = client.get("/api/v1/sources")
    assert sources.status_code == 200
    ids = {x["source_id"] for x in sources.json()}
    assert {"github", "instrumented_app"}.issubset(ids)
    providers = client.get("/api/v1/analysis/providers")
    assert providers.status_code == 200
    by_id = {row["provider_id"]: row for row in providers.json()}
    assert {"heuristic", "http"}.issubset(by_id)
    assert "EVIDENCE_CITATION" in by_id["heuristic"]["capabilities"]
    route = client.get("/api/v1/analysis/providers/route")
    assert route.status_code == 200
    assert route.json()["selected_provider_id"] == "heuristic"


def test_import_pipeline_and_dedup():
    payload = {"records": [
        {"source_id":"test","query":"AI短剧","item_type":"PRODUCT","title":"AI短剧批量生成工具","text":"短剧 自动剪辑 矩阵发布","payload":{"price":99}},
        {"source_id":"jobs","query":"AI短剧","item_type":"JOB","title":"招聘 AI短剧 剪辑运营","text":"AI视频 短剧剪辑","payload":{}}
    ]}
    first = client.post("/api/v1/import", json=payload)
    assert first.status_code == 200
    assert first.json()["inserted"] == 2
    second = client.post("/api/v1/import", json=payload)
    assert second.status_code == 200
    assert second.json()["duplicates"] == 2
    keywords = client.get("/api/v1/keywords").json()
    assert any(x["canonical"] == "ai短剧" for x in keywords)
    dashboard = client.get("/api/v1/dashboard").json()
    assert dashboard["totals"]["observations"] >= 2
    assert dashboard["totals"]["sources"] >= 2


def test_instrumented_app_contract():
    payload = [{
        "source_id":"xianyu_app_research",
        "query":"短剧工具",
        "app_package":"com.example.research",
        "app_version":"1.0",
        "emulator_profile":"api35-x86_64",
        "instrumentation_version":"0.1",
        "session_id":"session-1",
        "title":"短剧工具公开搜索结果",
        "text":"下载 工具 素材",
        "payload":{"rank":1}
    }]
    r = client.post("/api/v1/instrumented-app/observations", json=payload)
    assert r.status_code == 200
    assert r.json()["inserted"] == 1


def test_push_only_connector_rejects_active_collect():
    response = client.post("/api/v1/collect/instrumented_app", json={"query": "anything", "limit": 1})
    assert response.status_code == 409
    assert "push-only" in response.json()["detail"]


def test_sources_expose_query_mode_and_google_trends_rss():
    sources = client.get("/api/v1/sources")
    assert sources.status_code == 200
    by_id = {row["source_id"]: row for row in sources.json()}
    assert by_id["instrumented_app"]["query_mode"] == "PUSH_ONLY"
    assert by_id["github"]["query_mode"] == "KEYWORD"
    assert by_id["google_trends_rss"]["query_mode"] == "REGION"


def test_manual_import_cannot_spoof_registered_connector_source_id():
    response = client.post(
        "/api/v1/import",
        json={"records": [{"source_id": "github", "query": "spoof", "item_type": "CONTENT", "title": "spoof"}]},
    )
    assert response.status_code == 409
    assert "registered connector source_id" in response.json()["detail"]


def test_ready_requires_exact_schema_revision():
    from sqlalchemy import text
    from app.db.session import engine
    from app.main import DB_SCHEMA_REVISION

    with engine.begin() as connection:
        connection.execute(text("UPDATE alembic_version SET version_num='0004_clusters_analysis_health'"))
    try:
        response = client.get("/ready")
        assert response.status_code == 503
        detail = response.json()["detail"]
        assert detail["required_revision"] == DB_SCHEMA_REVISION
    finally:
        with engine.begin() as connection:
            connection.execute(text("UPDATE alembic_version SET version_num=:revision"), {"revision": DB_SCHEMA_REVISION})


def test_opportunity_detail_bounds_evidence_and_exposes_summary():
    payload = {"records": [
        {"source_id": "detail_a", "query": "AI工具", "item_type": "PRODUCT", "title": "AI工具产品", "text": "x" * 500},
        {"source_id": "detail_b", "query": "AI工具", "item_type": "JOB", "title": "AI工具招聘", "text": "y" * 500},
    ]}
    assert client.post("/api/v1/import", json=payload).status_code == 200
    rows = client.get("/api/v1/opportunities", params={"min_score": 1}).json()
    assert rows
    detail = client.get(f"/api/v1/opportunities/{rows[0]['id']}", params={"evidence_limit": 1, "evidence_text_chars": 20})
    assert detail.status_code == 200
    body = detail.json()
    assert body["evidence_summary"]["returned"] == 1
    assert body["evidence_summary"]["stored"] >= 1
    assert len(body["evidence"][0]["text"]) <= 20
    assert body["evidence"][0]["quality"] in {"A", "B", "C", "D", "E"}
    assert body["evidence_contract"] == {"version": "1", "id_algorithm": "sha256-content-hash-v1"}
    assert body["evidence_binding"] == {"entity_type": "opportunity", "entity_id": str(rows[0]["id"])}
    assert body["evidence"][0]["evidence_id"].startswith("ev1_")
    assert body["evidence"][0]["citation_rank"] == 1
    assert body["analysis"]["citation_contract_version"] == "1"
    assert body["analysis"]["citations"]
    assert body["analysis"]["conflict"] == {}


def test_instrumented_app_cannot_spoof_registered_connector_source_id():
    response = client.post(
        "/api/v1/instrumented-app/observations",
        json=[{
            "source_id": "github",
            "query": "spoof",
            "app_package": "com.example.research",
            "title": "spoof",
        }],
    )
    assert response.status_code == 409
    assert "cannot impersonate registered connector" in response.json()["detail"]
