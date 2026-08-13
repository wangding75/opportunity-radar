"""Run the bounded hiring-surge Mock acceptance fixture."""

from __future__ import annotations

import argparse
import json
from datetime import date

from app.db.session import SessionLocal
from app.services.hiring_surge_mock import seed_hiring_surge_mock


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed and evaluate the synthetic hiring-surge fixture")
    parser.add_argument("--window-end", type=date.fromisoformat, default=None)
    args = parser.parse_args()
    with SessionLocal() as db:
        result = seed_hiring_surge_mock(db, window_end=args.window_end)
        db.commit()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
