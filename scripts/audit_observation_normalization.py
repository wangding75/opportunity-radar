#!/usr/bin/env python3
"""Audit persisted observations and normalized items against normalization-v1."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db.session import SessionLocal  # noqa: E402
from app.services.normalization_audit import audit_observation_normalization  # noqa: E402


REPORT_PATH = ROOT / "validation" / "observation_normalization_audit.json"


def main() -> int:
    with SessionLocal() as db:
        result = audit_observation_normalization(db)
    REPORT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"OBSERVATION_NORMALIZATION_{result['status']}: "
        f"raw={result['summary']['raw_observations']} normalized={result['summary']['normalized_items']} "
        f"violations={len(result['violations'])}"
    )
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
