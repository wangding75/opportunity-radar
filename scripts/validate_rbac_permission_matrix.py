#!/usr/bin/env python3
"""Verify the committed RBAC matrix matches the runtime authorization contract."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.permissions import permission_matrix_snapshot  # noqa: E402


MATRIX_PATH = ROOT / "validation" / "rbac_permission_matrix.json"


def validate_matrix() -> dict:
    artifact = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    runtime = permission_matrix_snapshot()
    if artifact != runtime:
        raise ValueError("committed RBAC matrix differs from runtime permission contract")
    if artifact["role_order"] != ["OWNER", "ADMIN", "RESEARCHER", "VIEWER"]:
        raise ValueError("role order is not frozen")
    if len(artifact["capabilities"]) < 10:
        raise ValueError("permission matrix is incomplete")
    return {
        "status": "PASS",
        "matrix_version": artifact["matrix_version"],
        "roles": len(artifact["role_order"]),
        "capabilities": len(artifact["capabilities"]),
        "real_data_collected": 0,
        "data_policy": "SYNTHETIC_OR_MOCK_ONLY",
    }


if __name__ == "__main__":
    try:
        result = validate_matrix()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"RBAC_PERMISSION_MATRIX_FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(f"RBAC_PERMISSION_MATRIX_PASS: {result['roles']} roles, {result['capabilities']} capabilities")
