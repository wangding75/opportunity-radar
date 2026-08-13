#!/usr/bin/env python3
"""Audit keyword, trend and graph materializations in the current database."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db.session import SessionLocal  # noqa: E402
from app.services.keyword_trend_graph_audit import audit_keyword_trend_graph  # noqa: E402


REPORT_PATH = ROOT / "validation" / "keyword_trend_graph_audit.json"


def main() -> int:
    with SessionLocal() as db:
        result = audit_keyword_trend_graph(db)
    REPORT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"KEYWORD_TREND_GRAPH_{result['status']}: "
        f"keywords={result['summary']['keywords']} relations={result['summary']['graph_relations']} "
        f"violations={len(result['violations'])}"
    )
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
