#!/usr/bin/env python3
"""Audit persisted opportunity, score and lineage correctness."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db.session import SessionLocal  # noqa: E402
from app.services.opportunity_score_lineage_audit import audit_opportunity_score_lineage  # noqa: E402


REPORT_PATH = ROOT / "validation" / "opportunity_score_lineage_audit.json"


def main() -> int:
    with SessionLocal() as db:
        result = audit_opportunity_score_lineage(db)
    REPORT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"OPPORTUNITY_SCORE_LINEAGE_{result['status']}: "
        f"opportunities={result['summary']['opportunities']} "
        f"snapshots={result['summary']['score_snapshots']} "
        f"violations={len(result['violations'])}"
    )
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
