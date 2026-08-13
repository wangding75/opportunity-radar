from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_signal_words_do_not_become_standalone_topic_keywords():
    response = client.post(
        "/api/v1/import",
        json={"records": [{
            "source_id": "jobs",
            "query": "AI视频自动化",
            "external_id": "quality-1",
            "item_type": "JOB",
            "title": "招聘 AI视频自动化 运营",
            "text": "兼职 变现 收益 教程 工具",
        }]},
    )
    assert response.status_code == 200
    keywords = {row["canonical"] for row in client.get("/api/v1/keywords").json()}
    assert "ai视频自动化" in keywords
    assert not ({"招聘", "兼职", "变现", "收益", "教程"} & keywords)
