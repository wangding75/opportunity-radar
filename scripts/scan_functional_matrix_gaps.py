#!/usr/bin/env python3
"""Scan the functional matrix for broken implementation-chain links."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from validate_functional_matrix import validate_matrix
from validate_traceability import TRACEABILITY_PATH, validate_traceability


TRACE_ID_NA_UI = {
    "FM-DEL-001",
    "FM-DEL-002",
    "FM-DEL-003",
    "FM-DEL-004",
    "FM-ENT-001",
    "FM-ENT-002",
    "FM-ENT-003",
    "FM-ENT-004",
}
TRACE_ID_NA_API = {"FM-ENT-001", "FM-ENT-003", "FM-ENT-004"}
TRACE_ID_NA_WORKER = {"FM-OPP-003", "FM-DEL-004", "FM-ENT-002", "FM-SEC-001"}
NA_PREFIX = "N/A - "


def _all_explicit_na(targets: list[str]) -> bool:
    return bool(targets) and all(target.startswith(NA_PREFIX) for target in targets)


def scan_gaps() -> dict:
    matrix_result = validate_matrix()
    trace_result = validate_traceability()
    payload = json.loads(TRACEABILITY_PATH.read_text(encoding="utf-8"))
    gaps: list[dict[str, str]] = []
    entries = {str(entry["trace_id"]): entry for entry in payload["entries"]}

    for trace_id, entry in entries.items():
        for field in ("code_targets", "test_targets", "docs_targets"):
            if _all_explicit_na(entry[field]):
                gaps.append({"trace_id": trace_id, "field": field, "reason": "required evidence chain is entirely N/A"})
        if trace_id not in TRACE_ID_NA_API and _all_explicit_na(entry["api_targets"]):
            gaps.append({"trace_id": trace_id, "field": "api_targets", "reason": "product capability has no API target"})
        if trace_id not in TRACE_ID_NA_UI and _all_explicit_na(entry["ui_targets"]):
            gaps.append({"trace_id": trace_id, "field": "ui_targets", "reason": "user-facing capability has no UI target"})
        if trace_id not in TRACE_ID_NA_WORKER and _all_explicit_na(entry["worker_targets"]):
            gaps.append({"trace_id": trace_id, "field": "worker_targets", "reason": "asynchronous capability has no Worker target"})

    return {
        "matrix_rows": matrix_result["rows"],
        "traceability_entries": trace_result["entries"],
        "gaps": gaps,
        "gap_count": len(gaps),
    }


def main() -> int:
    try:
        result = scan_gaps()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FUNCTIONAL_GAP_SCAN_FAIL: {exc}", file=sys.stderr)
        return 1
    if result["gaps"]:
        print(f"FUNCTIONAL_GAP_SCAN_FAIL: {result['gap_count']} gaps")
        for gap in result["gaps"]:
            print(f"- {gap['trace_id']} {gap['field']}: {gap['reason']}")
        return 1
    print(f"FUNCTIONAL_GAP_SCAN_PASS: 0 gaps across {result['matrix_rows']} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
