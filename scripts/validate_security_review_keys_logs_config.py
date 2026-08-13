#!/usr/bin/env python3
"""Validate keys, logs, configuration and container security controls."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEW_PATH = ROOT / "validation" / "security_review_keys_logs_config_container.json"
REQUIRED_CONTROLS = {f"KEY-{index:03d}" for index in range(1, 9)}


def validate_security_review(path: Path = REVIEW_PATH) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("review_id") != "opportunity-radar-keys-logs-config-container-review":
        raise ValueError("keys/logs/config/container review ID is invalid")
    if payload.get("data_policy") != "SYNTHETIC_OR_MOCK_ONLY" or payload.get("real_data_collected") != 0:
        raise ValueError("keys/logs/config/container review must be SYNTHETIC/MOCK-only with zero real data")
    controls = payload.get("controls")
    if not isinstance(controls, list):
        raise ValueError("keys/logs/config/container review controls must be a list")
    control_ids: set[str] = set()
    for control in controls:
        required = {"control_id", "control", "status", "code_targets", "test_targets", "evidence"}
        if not isinstance(control, dict) or required - set(control):
            raise ValueError("keys/logs/config/container control is incomplete")
        control_id = str(control["control_id"])
        if control_id in control_ids or control["status"] != "PASS":
            raise ValueError(f"keys/logs/config/container control is duplicate or not PASS: {control_id}")
        control_ids.add(control_id)
        for field in ("code_targets", "test_targets"):
            targets = control[field]
            if not isinstance(targets, list) or not targets:
                raise ValueError(f"{control_id} {field} must be a non-empty list")
            for target in targets:
                if not (ROOT / str(target)).is_file():
                    raise ValueError(f"{control_id} target does not exist: {target}")
        if not str(control["evidence"]).strip():
            raise ValueError(f"{control_id} has incomplete evidence")
    if control_ids != REQUIRED_CONTROLS:
        raise ValueError(f"keys/logs/config/container control set mismatch: {sorted(control_ids)}")
    if payload.get("status") != "PASS":
        raise ValueError("keys/logs/config/container review status is not PASS")
    return {"review_id": payload["review_id"], "controls": len(controls), "status": payload["status"]}


def main() -> int:
    try:
        result = validate_security_review()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"SECURITY_REVIEW_KEYS_LOGS_CONFIG_FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"SECURITY_REVIEW_KEYS_LOGS_CONFIG_PASS: {result['controls']} controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
