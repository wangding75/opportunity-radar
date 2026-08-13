#!/usr/bin/env python3
"""Validate the itemized false-completion remediation ledger."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from validate_false_completion import ROOT, scan_false_completion


LEDGER_PATH = ROOT / "validation" / "false_completion_fix_ledger.json"
SCAN_REPORT_PATH = ROOT / "validation" / "false_completion_scan.json"
ALLOWED_STATUSES = {"FIXED", "VERIFIED_ABSENT", "EXPLICIT_CONTRACT"}


def validate_fix_ledger(
    ledger_path: Path = LEDGER_PATH,
    scan_report_path: Path = SCAN_REPORT_PATH,
) -> dict:
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    if ledger.get("ledger_id") != "opportunity-radar-false-completion-fixes":
        raise ValueError("false-completion ledger ID is invalid")
    if ledger.get("source_ruleset") != "validation/false_completion_rules.json":
        raise ValueError("false-completion ledger source ruleset is invalid")
    entries = ledger.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ValueError("false-completion ledger must contain entries")
    finding_ids: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("false-completion ledger entries must be objects")
        required = {"finding_id", "detector", "status", "scope", "file", "resolution", "verification", "test_targets"}
        missing = required - set(entry)
        if missing:
            raise ValueError(f"ledger entry is missing fields: {sorted(missing)}")
        finding_id = str(entry["finding_id"])
        if not finding_id or finding_id in finding_ids:
            raise ValueError(f"duplicate ledger finding_id: {finding_id}")
        finding_ids.add(finding_id)
        if entry["status"] not in ALLOWED_STATUSES:
            raise ValueError(f"{finding_id} has an invalid remediation status")
        target = ROOT / str(entry["file"])
        if not target.is_file():
            raise ValueError(f"{finding_id} file target does not exist: {entry['file']}")
        if not str(entry["resolution"]).strip() or not str(entry["scope"]).strip():
            raise ValueError(f"{finding_id} has an incomplete resolution or scope")
        if str(entry["verification"]) != "validation/false_completion_scan.json":
            raise ValueError(f"{finding_id} must cite the scan report")
        tests = entry["test_targets"]
        if not isinstance(tests, list) or not tests:
            raise ValueError(f"{finding_id} must cite at least one test")
        for test in tests:
            if not (ROOT / str(test)).is_file():
                raise ValueError(f"{finding_id} test target does not exist: {test}")

    scan = scan_false_completion()
    if scan["status"] != "PASS" or scan["violation_count"] != 0:
        raise ValueError("current false-completion scan is not clean")
    persisted_scan = json.loads(scan_report_path.read_text(encoding="utf-8"))
    if persisted_scan.get("status") != "PASS" or persisted_scan.get("violation_count") != 0:
        raise ValueError("persisted false-completion scan is not clean")
    status_counts = {status: sum(entry["status"] == status for entry in entries) for status in sorted(ALLOWED_STATUSES)}
    return {"ledger_id": ledger["ledger_id"], "entries": len(entries), "status_counts": status_counts, "scan_violations": scan["violation_count"]}


def main() -> int:
    try:
        result = validate_fix_ledger()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FALSE_COMPLETION_FIX_LEDGER_FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"FALSE_COMPLETION_FIX_LEDGER_PASS: {result['entries']} items, scan violations={result['scan_violations']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
