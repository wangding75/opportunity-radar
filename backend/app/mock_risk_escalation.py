"""Run the bounded synthetic risk escalation acceptance fixture."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.db.session import SessionLocal
from app.services.risk_escalation_mock import seed_risk_escalation_mock


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed and evaluate the synthetic risk escalation fixture")
    parser.add_argument("--fixture", type=Path, default=None)
    args = parser.parse_args()
    with SessionLocal() as db:
        result = seed_risk_escalation_mock(db, fixture_path=args.fixture)
        db.commit()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
