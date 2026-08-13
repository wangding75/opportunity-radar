from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db.session import SessionLocal
from app.services.archive import restore_raw_payload_archive


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore one cold RawObservation payload archive")
    parser.add_argument("archive_file", help="archive filename relative to RAW_PAYLOAD_ARCHIVE_DIR")
    parser.add_argument("--confirm-restore", action="store_true")
    args = parser.parse_args()
    if not args.confirm_restore:
        raise SystemExit("restore blocked: pass --confirm-restore")
    with SessionLocal() as db:
        result = restore_raw_payload_archive(db, args.archive_file)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
