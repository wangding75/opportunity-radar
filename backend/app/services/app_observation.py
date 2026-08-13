from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import RawObservation
from app.domain.enums import AcquisitionMethod


def _schema_keys(payload: object, prefix: str = "", *, depth: int = 0) -> set[str]:
    if depth > 3 or not isinstance(payload, dict):
        return set()
    keys: set[str] = set()
    for key, value in payload.items():
        path = f"{prefix}.{key}" if prefix else str(key)
        keys.add(path)
        if isinstance(value, dict):
            keys.update(_schema_keys(value, path, depth=depth + 1))
    return keys


def schema_drift_report(db: Session, source_id: str) -> dict:
    rows = db.scalars(
        select(RawObservation)
        .where(
            RawObservation.source_id == source_id,
            RawObservation.acquisition_method == AcquisitionMethod.INSTRUMENTED_APP.value,
        )
        .order_by(RawObservation.observed_at)
    ).all()
    by_version: dict[str, dict[str, object]] = defaultdict(lambda: {"observations": 0, "keys": set()})
    for row in rows:
        version = row.app_version or "UNKNOWN"
        bucket = by_version[version]
        bucket["observations"] = int(bucket["observations"]) + 1
        keys = bucket["keys"]
        assert isinstance(keys, set)
        keys.update(_schema_keys(row.raw_payload))

    versions = []
    previous_keys: set[str] | None = None
    for version, bucket in by_version.items():
        keys = bucket["keys"]
        assert isinstance(keys, set)
        added = sorted(keys - previous_keys) if previous_keys is not None else []
        removed = sorted(previous_keys - keys) if previous_keys is not None else []
        versions.append(
            {
                "app_version": version,
                "observations": int(bucket["observations"]),
                "schema_keys": sorted(keys),
                "added_vs_previous": added,
                "removed_vs_previous": removed,
                "drift_detected": bool(added or removed),
            }
        )
        previous_keys = set(keys)
    return {"source_id": source_id, "versions": versions, "drift_detected": any(v["drift_detected"] for v in versions)}
