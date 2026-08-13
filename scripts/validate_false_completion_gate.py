#!/usr/bin/env python3
"""Run the complete false-completion regression gate."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from generate_functional_audit_report import build_report
from scan_functional_matrix_gaps import scan_gaps
from validate_false_completion import ROOT, scan_false_completion
from validate_false_completion_fixes import validate_fix_ledger
from validate_traceability import validate_traceability


GATE_REPORT_PATH = ROOT / "validation" / "false_completion_gate.json"


def run_gate() -> dict:
    scan = scan_false_completion()
    ledger = validate_fix_ledger()
    traceability = validate_traceability()
    gaps = scan_gaps()
    audit = build_report()
    checks = {
        "false_completion_scan": scan["status"] == "PASS" and scan["violation_count"] == 0,
        "itemized_fix_ledger": ledger["scan_violations"] == 0,
        "functional_traceability": traceability["entries"] == traceability["matrix_rows"],
        "functional_gap_scan": gaps["gap_count"] == 0,
        "functional_audit_report": audit["report_status"] == "PASS" and audit["summary"]["gap_count"] == 0,
        "safe_data_policy": audit["data_policy"] == "SYNTHETIC_OR_MOCK_ONLY" and audit["real_data_collected"] == 0,
    }
    if not all(checks.values()):
        raise ValueError(f"false-completion gate failed: {checks}")
    result = {
        "gate_id": "opportunity-radar-false-completion-gate",
        "gate_version": "1.0",
        "status": "PASS",
        "checks": checks,
        "summary": {
            "scanned_files": scan["scanned_files"],
            "scan_violations": scan["violation_count"],
            "ledger_items": ledger["entries"],
            "traceability_entries": traceability["entries"],
            "functional_rows": gaps["matrix_rows"],
            "functional_gaps": gaps["gap_count"],
            "real_data_collected": audit["real_data_collected"],
        },
        "artifacts": [
            "validation/false_completion_rules.json",
            "validation/false_completion_scan.json",
            "validation/false_completion_fix_ledger.json",
            "validation/functional_traceability.json",
            "validation/functional_audit_report.json",
        ],
    }
    GATE_REPORT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    try:
        result = run_gate()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FALSE_COMPLETION_GATE_FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"FALSE_COMPLETION_GATE_PASS: {sum(result['checks'].values())}/{len(result['checks'])} checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
