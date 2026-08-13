from __future__ import annotations

from app.main import app
from app.services.api_permissions import api_permission_inventory


def test_api_permission_inventory_is_deterministic_and_covers_live_routes():
    first = api_permission_inventory(app)
    second = api_permission_inventory(app)
    assert first == second
    assert first["summary"]["route_count"] >= 80
    assert first["summary"]["real_data_collected"] == 0


def test_api_permission_inventory_freezes_public_read_write_and_admin_boundaries():
    rows = {(method, entry["path"]): entry for entry in api_permission_inventory(app)["routes"] for method in entry["methods"]}
    assert rows[("GET", "/health")]["required_scope"] == "public"
    assert rows[("POST", "/api/v1/auth/login")]["required_scope"] == "public"
    assert rows[("GET", "/api/v1/dashboard")]["required_scope"] == "read"
    assert rows[("PATCH", "/api/v1/opportunities/{opportunity_id}/research")]["required_scope"] == "write"
    assert rows[("POST", "/api/v1/import")]["required_scope"] == "admin"
    assert rows[("POST", "/api/v1/auth/tokens")]["interactive_session_required"] is True
    assert rows[("POST", "/api/v1/watch-keywords")]["csrf_required_for_session"] is True
    assert rows[("GET", "/metrics")]["required_scope"] == "read"


def test_openapi_operations_expose_derived_rbac_extension():
    schema = app.openapi()
    dashboard = schema["paths"]["/api/v1/dashboard"]["get"]
    assert dashboard["x-rbac"]["required_scope"] == "read"
    assert dashboard["x-rbac"]["allowed_roles"] == ["OWNER", "ADMIN", "RESEARCHER", "VIEWER"]
