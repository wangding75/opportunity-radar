from dataclasses import replace

from fastapi.testclient import TestClient

from app.core import security
from app.db.models import WebhookEndpoint
from app.db.session import SessionLocal
from app.main import app


client = TestClient(app)
SECRET = "synthetic-webhook-secret-0123456789"


def test_webhook_endpoint_crud_is_persistent_and_secret_is_write_only():
    created = client.post(
        "/api/v1/webhooks/endpoints",
        json={
            "name": "synthetic-receiver",
            "url": "https://receiver.synthetic.invalid/hooks/alerts",
            "secret": SECRET,
            "event_types": ["alert.event"],
            "description": "SYNTHETIC receiver",
        },
    )
    assert created.status_code == 200
    body = created.json()
    endpoint_id = body["id"]
    assert body["enabled"] is True
    assert body["event_types"] == ["alert.event"]
    assert body["secret_fingerprint"]
    assert "secret" not in body
    assert SECRET not in created.text

    listed = client.get("/api/v1/webhooks/endpoints")
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == endpoint_id
    assert SECRET not in listed.text
    with SessionLocal() as db:
        row = db.get(WebhookEndpoint, endpoint_id)
        assert row is not None
        assert row.secret == SECRET

    patched = client.patch(
        f"/api/v1/webhooks/endpoints/{endpoint_id}",
        json={"enabled": False, "secret": "synthetic-webhook-secret-rotated-123", "description": "disabled synthetic"},
    )
    assert patched.status_code == 200
    assert patched.json()["enabled"] is False
    assert patched.json()["secret_fingerprint"] != body["secret_fingerprint"]
    assert "secret" not in patched.json()

    deleted = client.delete(f"/api/v1/webhooks/endpoints/{endpoint_id}")
    assert deleted.status_code == 200
    assert deleted.json() == {"id": endpoint_id, "deleted": True}
    assert client.get("/api/v1/webhooks/endpoints").json() == []


def test_webhook_endpoint_validation_duplicates_and_missing_rows():
    invalid = client.post(
        "/api/v1/webhooks/endpoints",
        json={"name": "bad name\n", "url": "file:///tmp/hook", "secret": "short"},
    )
    assert invalid.status_code == 422

    payload = {"name": "duplicate-synthetic", "url": "https://receiver.synthetic.invalid/hook", "secret": SECRET}
    assert client.post("/api/v1/webhooks/endpoints", json=payload).status_code == 200
    duplicate = client.post("/api/v1/webhooks/endpoints", json={**payload, "name": " DUPLICATE-SYNTHETIC "})
    assert duplicate.status_code == 409
    empty_events = client.patch("/api/v1/webhooks/endpoints/1", json={"event_types": []})
    assert empty_events.status_code == 422
    assert client.patch("/api/v1/webhooks/endpoints/99999", json={"enabled": False}).status_code == 404
    assert client.delete("/api/v1/webhooks/endpoints/99999").status_code == 404


def test_webhook_endpoint_mutations_require_admin_scope(monkeypatch):
    original = security.settings
    monkeypatch.setattr(security, "settings", replace(original, auth_mode="rbac", api_key=None, allow_legacy_api_key=False))
    try:
        response = client.post(
            "/api/v1/webhooks/endpoints",
            json={"name": "unauthorized", "url": "https://receiver.synthetic.invalid/hook", "secret": SECRET},
        )
        assert response.status_code == 401
    finally:
        monkeypatch.setattr(security, "settings", original)
