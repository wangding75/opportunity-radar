#!/usr/bin/env python3
"""Run the complete repository security regression gate."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from validate_dependency_supply_chain_review import validate_dependency_review
from validate_false_completion_gate import run_gate as run_false_completion_gate
from validate_security_review_auth import validate_security_review as validate_auth_review
from validate_security_review_input_http import validate_security_review as validate_input_http_review
from validate_security_review_keys_logs_config import validate_security_review as validate_keys_review


ROOT = Path(__file__).resolve().parents[1]
GATE_REPORT_PATH = ROOT / "validation" / "security_gate.json"


def run_security_gate() -> dict:
    auth = validate_auth_review()
    input_http = validate_input_http_review()
    keys = validate_keys_review()
    dependency = validate_dependency_review()
    false_completion = run_false_completion_gate()
    checks = {
        "auth_session_csrf_token": auth["status"] == "PASS" and auth["controls"] == 8,
        "input_output_ssrf_xml_http": input_http["status"] == "PASS" and input_http["controls"] == 8,
        "keys_logs_config_container": keys["status"] == "PASS" and keys["controls"] == 8,
        "dependency_supply_chain": dependency["status"] == "PASS" and dependency["controls"] == 6,
        "false_completion_regression": false_completion["status"] == "PASS" and all(false_completion["checks"].values()),
    }
    if not all(checks.values()):
        raise ValueError(f"security gate failed: {checks}")
    result = {
        "gate_id": "opportunity-radar-security-gate",
        "gate_version": "1.0",
        "status": "PASS",
        "checks": checks,
        "summary": {
            "security_controls": auth["controls"] + input_http["controls"] + keys["controls"] + dependency["controls"],
            "false_completion_checks": sum(false_completion["checks"].values()),
            "false_completion_violations": false_completion["summary"]["scan_violations"],
            "functional_gaps": false_completion["summary"]["functional_gaps"],
            "real_data_collected": 0,
        },
        "artifacts": [
            "validation/security_review_auth.json",
            "validation/security_review_input_http.json",
            "validation/security_review_keys_logs_config_container.json",
            "validation/security_review_dependency_supply_chain.json",
            "validation/false_completion_gate.json",
        ],
    }
    GATE_REPORT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    try:
        result = run_security_gate()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"SECURITY_GATE_FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"SECURITY_GATE_PASS: {sum(result['checks'].values())}/{len(result['checks'])} checks, controls={result['summary']['security_controls']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
