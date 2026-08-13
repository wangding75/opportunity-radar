#!/usr/bin/env python3
"""Audit alert lifecycle, replay cutoffs and score backtest boundaries."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db.session import SessionLocal  # noqa: E402
from app.services.alert_replay_backtest_audit import audit_alert_replay_backtest  # noqa: E402


REPORT_PATH = ROOT / "validation" / "alert_replay_backtest_audit.json"


def main() -> int:
    with SessionLocal() as db:
        result = audit_alert_replay_backtest(db)
    REPORT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"ALERT_REPLAY_BACKTEST_{result['status']}: "
        f"events={result['summary']['alert_events']} "
        f"snapshots={result['summary']['score_snapshots']} "
        f"violations={len(result['violations'])}"
    )
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
