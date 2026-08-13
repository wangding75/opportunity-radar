from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db.session import SessionLocal
from app.services.archive import archive_raw_payloads


def main() -> int:
    parser = argparse.ArgumentParser(description="Cold-archive old RawObservation payloads without deleting evidence rows")
    parser.add_argument("--older-than-days", type=int, default=90)
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--apply", action="store_true", help="write archive; default is dry-run")
    args = parser.parse_args()
    with SessionLocal() as db:
        result = archive_raw_payloads(db, older_than_days=args.older_than_days, limit=args.limit, dry_run=not args.apply)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
