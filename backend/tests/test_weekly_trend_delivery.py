from fastapi.testclient import TestClient

from app.connectors.registry import SourceRegistry
from app.main import app
from app.worker import run_once


def test_weekly_trend_worker_is_idempotent_and_persists_report():
    first = run_once(sync=False, limit=1, mode="weekly", worker_id="weekly-trend-worker-test", registry=SourceRegistry())
    second = run_once(sync=False, limit=1, mode="weekly", worker_id="weekly-trend-worker-test", registry=SourceRegistry())
    assert first["weekly_trends"]["status"] == "EMPTY"
    assert second["weekly_trends"]["input_signature"] == first["weekly_trends"]["input_signature"]


def test_weekly_trend_csv_export_returns_traceable_headers_or_not_found():
    run_once(sync=False, limit=1, mode="weekly", worker_id="weekly-trend-export-test", registry=SourceRegistry())
    client = TestClient(app)
    response = client.get("/api/v1/exports/trends/weekly.csv")
    assert response.status_code == 200
    assert "trend_signature" in response.text
    assert "evidence_provenance" in response.text
