from __future__ import annotations

import base64
import json
from datetime import datetime


def encode_cursor(payload: dict) -> str:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_cursor(value: str | None) -> dict | None:
    if not value:
        return None
    try:
        padded = value + "=" * (-len(value) % 4)
        data = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8"))
    except Exception as exc:
        raise ValueError("invalid pagination cursor") from exc
    if not isinstance(data, dict):
        raise ValueError("invalid pagination cursor")
    return data


def opportunity_cursor(score: float, last_seen_at: datetime, row_id: int) -> str:
    return encode_cursor({"score": score, "last_seen_at": last_seen_at.isoformat(), "id": row_id})


def observation_cursor(observed_at: datetime, row_id: int) -> str:
    return encode_cursor({"observed_at": observed_at.isoformat(), "id": row_id})
