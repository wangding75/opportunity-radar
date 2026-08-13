#!/usr/bin/env python3
"""Scan the functional matrix for broken implementation-chain links."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from validate_functional_matrix import ROOT, validate_matrix
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

IMPORTANT_API_MODULES = tuple(
    f"backend/app/api/{path.name}"
    for path in sorted((ROOT / "backend" / "app" / "api").glob("*.py"))
    if path.name != "__init__.py"
)
IMPORTANT_CONNECTOR_MODULES = tuple(
    f"backend/app/connectors/{path.name}"
    for path in sorted((ROOT / "backend" / "app" / "connectors").glob("*.py"))
    if path.name not in {"__init__.py", "base.py"}
)
CORE_SERVICE_MODULES = (
    "backend/app/services/auth.py",
    "backend/app/services/dashboard.py",
    "backend/app/services/digest.py",
    "backend/app/services/digest_persistence.py",
    "backend/app/services/execution.py",
    "backend/app/services/ingestion.py",
    "backend/app/services/normalizer.py",
    "backend/app/services/opportunities.py",
    "backend/app/services/probes.py",
    "backend/app/services/scoring.py",
    "backend/app/services/source_health.py",
    "backend/app/services/weekly_trends.py",
    "backend/app/services/weekly_trend_persistence.py",
    "backend/app/services/worker_health.py",
)
IMPORTANT_WORKER_MODULES = ("backend/app/worker.py",)


def _all_explicit_na(targets: list[str]) -> bool:
    return bool(targets) and all(target.startswith(NA_PREFIX) for target in targets)


def _reverse_coverage(entries: list[dict]) -> dict:
    registered_code_targets = {
        target
        for entry in entries
        for target in entry["code_targets"]
        if not target.startswith(NA_PREFIX)
    }

    def unregistered(targets: tuple[str, ...], kind: str) -> list[dict[str, str]]:
        return [
            {
                "kind": kind,
                "target": target,
                "reason": "important implementation target is not referenced by any functional matrix traceability entry",
            }
            for target in targets
            if target not in registered_code_targets
        ]

    return {
        "api_modules": unregistered(IMPORTANT_API_MODULES, "api_module"),
        "connectors": unregistered(IMPORTANT_CONNECTOR_MODULES, "connector"),
        "core_services": unregistered(CORE_SERVICE_MODULES, "core_service"),
        "workers": unregistered(IMPORTANT_WORKER_MODULES, "worker"),
    }


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

    reverse_coverage = _reverse_coverage(list(entries.values()))
    reverse_findings = [finding for findings in reverse_coverage.values() for finding in findings]

    return {
        "matrix_rows": matrix_result["rows"],
        "traceability_entries": trace_result["entries"],
        "gaps": gaps,
        "gap_count": len(gaps),
        "reverse_coverage": reverse_coverage,
        "reverse_unregistered": reverse_findings,
        "reverse_unregistered_count": len(reverse_findings),
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
    print(
        "FUNCTIONAL_GAP_SCAN_REPORT: "
        f"chain_gaps={result['gap_count']}, "
        f"reverse_unregistered={result['reverse_unregistered_count']} across {result['matrix_rows']} rows"
    )
    for finding in result["reverse_unregistered"]:
        print(f"- {finding['kind']} {finding['target']}: {finding['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
