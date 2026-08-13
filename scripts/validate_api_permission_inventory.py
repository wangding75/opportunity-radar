#!/usr/bin/env python3
"""Validate that the committed API permission inventory matches live routes."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.main import app  # noqa: E402
from app.services.api_permissions import api_permission_inventory  # noqa: E402


INVENTORY_PATH = ROOT / "validation" / "api_permission_inventory.json"


def validate_inventory() -> dict:
    committed = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    runtime = api_permission_inventory(app)
    if committed != runtime:
        raise ValueError("committed API permission inventory differs from live FastAPI routes")
    if committed["summary"]["route_count"] < 80:
        raise ValueError("API permission inventory is unexpectedly incomplete")
    for entry in committed["routes"]:
        if entry["required_scope"] == "public":
            assert entry["minimum_role"] is None
            assert entry["allowed_roles"] == ["ANONYMOUS"]
        else:
            assert entry["minimum_role"] in {"VIEWER", "RESEARCHER", "ADMIN"}
            assert set(entry["allowed_roles"]).issubset({"OWNER", "ADMIN", "RESEARCHER", "VIEWER"})
            assert entry["auth_dependency"] is not None
    return committed


if __name__ == "__main__":
    try:
        result = validate_inventory()
    except (AssertionError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"API_PERMISSION_INVENTORY_FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(f"API_PERMISSION_INVENTORY_PASS: {result['summary']['route_count']} live routes matched")
