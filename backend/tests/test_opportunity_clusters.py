from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_related_keywords_merge_into_one_opportunity_cluster():
    payload = {
        "records": [
            {
                "source_id": "cluster_market",
                "query": "短剧自动化",
                "external_id": "c1",
                "item_type": "PRODUCT",
                "title": "短剧自动化工具",
                "text": "短剧矩阵 自动剪辑 工具",
            },
            {
                "source_id": "cluster_jobs",
                "query": "短剧自动化",
                "external_id": "c2",
                "item_type": "JOB",
                "title": "短剧矩阵运营招聘",
                "text": "短剧自动化 短剧矩阵 运营",
            },
            {
                "source_id": "cluster_trend",
                "query": "短剧自动化",
                "external_id": "c3",
                "item_type": "TREND",
                "title": "短剧矩阵搜索增长",
                "text": "短剧自动化 短剧矩阵",
            },
        ]
    }
    response = client.post("/api/v1/import", json=payload)
    assert response.status_code == 200

    opportunities = client.get("/api/v1/opportunities", params={"min_score": 1}).json()
    clustered = [row for row in opportunities if row["title"] == "短剧自动化"]
    assert clustered
    opportunity = clustered[0]
    assert opportunity["related_keyword_count"] >= 2
    assert opportunity["summary"]
    assert opportunity["analysis_status"] == "READY"

    detail = client.get(f"/api/v1/opportunities/{opportunity['id']}")
    assert detail.status_code == 200
    data = detail.json()
    names = {row["keyword"] for row in data["keywords"]}
    assert "短剧自动化" in names
    assert "短剧矩阵" in names
    assert data["analysis"]["business_model"]
    assert data["analysis"]["target_user"]
