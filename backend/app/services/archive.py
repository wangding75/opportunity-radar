from __future__ import annotations

import gzip
import hashlib
import json
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.time import utc_now
from app.db.models import RawObservation


def _archive_root() -> Path:
    root = Path(settings.raw_payload_archive_dir).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def archive_raw_payloads(db: Session, *, older_than_days: int = 90, limit: int = 1000, dry_run: bool = True) -> dict:
    if not 1 <= older_than_days <= 36500:
        raise ValueError("older_than_days must be between 1 and 36500")
    limit = max(1, min(10_000, limit))
    cutoff = utc_now() - timedelta(days=older_than_days)
    rows = db.scalars(
        select(RawObservation)
        .where(RawObservation.observed_at < cutoff, RawObservation.raw_payload_archived_at.is_(None))
        .order_by(RawObservation.observed_at, RawObservation.id)
        .limit(limit)
    ).all()
    bytes_total = sum(
        int(row.raw_payload_bytes or 0)
        or len(json.dumps(row.raw_payload or {}, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))
        for row in rows
    )
    if dry_run or not rows:
        return {"dry_run": dry_run, "eligible": len(rows), "payload_bytes": bytes_total, "archive_file": None}

    stamp = utc_now().strftime("%Y%m%dT%H%M%S%f")
    final = _archive_root() / f"raw-payloads-{stamp}-{rows[0].id}-{rows[-1].id}-{uuid4().hex[:8]}.jsonl.gz"
    tmp = final.with_suffix(final.suffix + ".tmp")
    digest = hashlib.sha256()
    with gzip.open(tmp, "wt", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            record = {"id": row.id, "content_hash": row.content_hash, "raw_payload": row.raw_payload}
            line = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
            fh.write(line)
    with open(tmp, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    checksum = digest.hexdigest()
    tmp.replace(final)
    archived_at = utc_now()
    rel = str(final.relative_to(_archive_root()))
    try:
        for row in rows:
            row.raw_payload = {"_archived": True, "archive_file": rel, "content_hash": row.content_hash}
            row.raw_payload_archived_at = archived_at
            row.raw_payload_archive_file = rel
            row.raw_payload_archive_sha256 = checksum
        db.commit()
    except Exception:
        db.rollback()
        final.unlink(missing_ok=True)
        raise
    return {"dry_run": False, "eligible": len(rows), "archived": len(rows), "payload_bytes": bytes_total, "archive_file": str(final), "sha256": checksum}


def restore_raw_payload_archive(db: Session, archive_file: str) -> dict:
    root = _archive_root()
    path = (root / archive_file).resolve()
    if root not in path.parents or not path.is_file():
        raise FileNotFoundError("archive file is outside configured archive root or missing")
    digest = hashlib.sha256()
    with path.open("rb") as raw:
        for chunk in iter(lambda: raw.read(1024 * 1024), b""):
            digest.update(chunk)
    file_hash = digest.hexdigest()
    records: list[dict] = []
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                records.append(json.loads(line))
    candidates: list[tuple[RawObservation, dict]] = []
    for record in records:
        row = db.get(RawObservation, int(record["id"]))
        if row is None or row.content_hash != record.get("content_hash"):
            continue
        if row.raw_payload_archive_sha256 != file_hash:
            raise ValueError(f"archive checksum mismatch for raw observation {row.id}")
        candidates.append((row, record))
    restored = 0
    for row, record in candidates:
        row.raw_payload = record.get("raw_payload") or {}
        row.raw_payload_archived_at = None
        row.raw_payload_archive_file = None
        row.raw_payload_archive_sha256 = None
        restored += 1
    db.commit()
    return {"archive_file": str(path), "sha256": file_hash, "records": len(records), "restored": restored}
