#!/usr/bin/env python3
"""Generate the auditable API-to-RBAC inventory from live application routes."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.main import app  # noqa: E402
from app.services.api_permissions import api_permission_inventory  # noqa: E402


INVENTORY_PATH = ROOT / "validation" / "api_permission_inventory.json"


def generate_inventory() -> dict:
    inventory = api_permission_inventory(app)
    INVENTORY_PATH.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return inventory


if __name__ == "__main__":
    try:
        result = generate_inventory()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"API_PERMISSION_INVENTORY_FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
    summary = result["summary"]
    print(
        "API_PERMISSION_INVENTORY_PASS: "
        f"{summary['route_count']} routes, {summary['protected_route_count']} protected, "
        f"{summary['public_route_count']} public"
    )
