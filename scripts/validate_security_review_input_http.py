#!/usr/bin/env python3
"""Validate the input/output, SSRF, XML and HTTP security review."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEW_PATH = ROOT / "validation" / "security_review_input_http.json"
REQUIRED_CONTROLS = {f"INPUT-{index:03d}" for index in range(1, 9)}


def validate_security_review(path: Path = REVIEW_PATH) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("review_id") != "opportunity-radar-input-output-ssrf-xml-http-review":
        raise ValueError("input/http security review ID is invalid")
    if payload.get("data_policy") != "SYNTHETIC_OR_MOCK_ONLY" or payload.get("real_data_collected") != 0:
        raise ValueError("input/http review must be SYNTHETIC/MOCK-only with zero real data")
    controls = payload.get("controls")
    if not isinstance(controls, list):
        raise ValueError("input/http review controls must be a list")
    control_ids: set[str] = set()
    for control in controls:
        if not isinstance(control, dict):
            raise ValueError("input/http review control must be an object")
        required = {"control_id", "control", "status", "code_targets", "test_targets", "evidence"}
        missing = required - set(control)
        if missing:
            raise ValueError(f"input/http review control is missing fields: {sorted(missing)}")
        control_id = str(control["control_id"])
        if control_id in control_ids or control["status"] != "PASS":
            raise ValueError(f"input/http review control is duplicate or not PASS: {control_id}")
        control_ids.add(control_id)
        for field, prefix in (("code_targets", None), ("test_targets", "backend/tests")):
            targets = control[field]
            if not isinstance(targets, list) or not targets:
                raise ValueError(f"{control_id} {field} must be a non-empty list")
            for target in targets:
                target_path = ROOT / str(target)
                if not target_path.is_file():
                    raise ValueError(f"{control_id} target does not exist: {target}")
                if prefix and not target_path.as_posix().startswith((ROOT / prefix).as_posix() + "/"):
                    raise ValueError(f"{control_id} test target is outside {prefix}: {target}")
        if not str(control["evidence"]).strip():
            raise ValueError(f"{control_id} has incomplete evidence")
    if control_ids != REQUIRED_CONTROLS:
        raise ValueError(f"input/http review control set mismatch: {sorted(control_ids)}")
    if payload.get("status") != "PASS":
        raise ValueError("input/http security review status is not PASS")
    return {"review_id": payload["review_id"], "controls": len(controls), "status": payload["status"]}


def main() -> int:
    try:
        result = validate_security_review()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"SECURITY_REVIEW_INPUT_HTTP_FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"SECURITY_REVIEW_INPUT_HTTP_PASS: {result['controls']} controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
