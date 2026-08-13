#!/usr/bin/env python3
"""Validate the deterministic aggregate data-correctness gate."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db.session import SessionLocal  # noqa: E402
from app.services.data_correctness_gate import run_data_correctness_gate  # noqa: E402


REPORT_PATH = ROOT / "validation" / "data_correctness_gate.json"


def main() -> int:
    with SessionLocal() as db:
        result = run_data_correctness_gate(db)
    REPORT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"DATA_CORRECTNESS_GATE_{result['status']}: "
        f"audits={result['summary']['passed_audits']}/{result['summary']['audit_count']} "
        f"violations={result['summary']['violation_count']}"
    )
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
