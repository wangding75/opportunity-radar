#!/usr/bin/env python3
"""Validate that frontend visibility rules match backend RBAC route contracts."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "validation" / "rbac_permission_matrix.json"
INVENTORY_PATH = ROOT / "validation" / "api_permission_inventory.json"
REPORT_PATH = ROOT / "validation" / "frontend_rbac_consistency.json"


def _route(inventory: dict, method: str, path: str) -> dict:
    for entry in inventory["routes"]:
        if method in entry["methods"] and entry["path"] == path:
            return entry
    raise ValueError(f"missing backend route {method} {path}")


def validate_frontend_rbac(*, check_node: bool | None = None) -> dict:
    if check_node is None:
        check_node = shutil.which("node") is not None
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    source = (ROOT / "frontend" / "src" / "main.ts").read_text(encoding="utf-8")
    permissions = (ROOT / "frontend" / "src" / "permissions.ts").read_text(encoding="utf-8")
    html = (ROOT / "backend" / "app" / "static" / "index.html").read_text(encoding="utf-8")
    compiled = [ROOT / "backend" / "app" / "static" / "js" / name for name in ("main.js", "client.js", "permissions.js")]
    checks: dict[str, bool] = {}

    checks["matrix_version"] = f'PERMISSION_MATRIX_VERSION = "{matrix["matrix_version"]}"' in permissions
    checks["role_levels"] = all(f"{role}: {level}" in permissions for role, level in matrix["role_level"].items())
    checks["frontend_role_helpers"] = all(name in source for name in ("canRoleWrite", "isAdminRole", "isOwnerRole"))
    checks["admin_view_guard"] = "id==='users'||id==='operations'" in source and "isAdmin()" in source
    checks["compiled_permission_module"] = all(path.exists() for path in compiled) and 'from "./permissions.js"' in compiled[0].read_text(encoding="utf-8")

    expected_admin_actions = {
        "generate-digest": ("POST", "/api/v1/digests/daily/generate"),
        "generate-weekly": ("POST", "/api/v1/trends/weekly/generate"),
        "evaluate-alerts": ("POST", "/api/v1/alerts/evaluate"),
        "sync-probes": ("POST", "/api/v1/probes/sync"),
        "preview-retention": ("POST", "/api/v1/maintenance/retention"),
    }
    expected_write_actions = {
        "create-rule": ("POST", "/api/v1/alerts/rules"),
        "add-watch": ("POST", "/api/v1/watch-keywords"),
        "save-research": ("PATCH", "/api/v1/opportunities/{opportunity_id}/research"),
        "alert-status": ("PATCH", "/api/v1/alerts/events/{event_id}"),
        "toggle-watch": ("PATCH", "/api/v1/watch-keywords/{watch_id}"),
    }
    action_contracts = {**expected_admin_actions, **expected_write_actions}
    action_checks = []
    for action, (method, path) in action_contracts.items():
        route = _route(inventory, method, path)
        if action in expected_admin_actions:
            ui_marker = action in {"preview-retention"} and "ADMIN_ACTIONS" in source or f'data-action="{action}" data-admin-only="true"' in html
            action_checks.append(ui_marker and route["required_scope"] == "admin")
        else:
            marker = f'data-action="{action}" data-write-only="true"' in html
            dynamic = action in {"save-research", "alert-status", "toggle-watch"} and "canWrite()" in source
            action_checks.append((marker or dynamic) and route["required_scope"] == "write")
    checks["admin_actions_match_backend"] = all(action_checks[: len(expected_admin_actions)])
    checks["write_actions_match_backend"] = all(action_checks[len(expected_admin_actions) :])
    checks["no_browser_credential_storage"] = "localStorage" not in source and all("localStorage" not in path.read_text(encoding="utf-8") for path in compiled)

    if check_node:
        for path in compiled:
            subprocess.run(["node", "--check", str(path)], check=True)
    if not all(checks.values()):
        raise ValueError(f"frontend RBAC consistency failed: {checks}")
    report = {
        "report_id": "opportunity-radar-frontend-rbac-consistency",
        "report_version": "1.0",
        "status": "PASS",
        "checks": checks,
        "summary": {
            "backend_routes_checked": len(inventory["routes"]),
            "admin_actions_checked": len(expected_admin_actions),
            "write_actions_checked": len(expected_write_actions),
            "permission_matrix_version": matrix["matrix_version"],
            "node_syntax_check": "PASS" if check_node else "ENVIRONMENT_BLOCKED",
            "real_data_collected": 0,
            "data_policy": "SYNTHETIC_OR_MOCK_ONLY",
        },
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    try:
        result = validate_frontend_rbac()
    except (OSError, ValueError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        print(f"FRONTEND_RBAC_FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(f"FRONTEND_RBAC_PASS: {sum(result['checks'].values())}/{len(result['checks'])} checks")
