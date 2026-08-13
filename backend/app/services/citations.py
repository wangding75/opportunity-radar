from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from app.domain.citations import evidence_id_for_row, validate_evidence_id


MAX_CITATION_SELECTION = 100
QUALITY_RANK = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1}


def _timestamp(value: Any) -> float:
    if isinstance(value, datetime):
        return value.timestamp()
    if value is None:
        return float("-inf")
    try:
        return datetime.fromisoformat(str(value)).timestamp()
    except (TypeError, ValueError, OverflowError):
        return float("-inf")


def _quality(value: Any) -> str:
    return str(value or "E").strip().upper()


def _candidate_key(row: Mapping[str, Any]) -> tuple[int, float, str, str, str]:
    return (
        QUALITY_RANK.get(_quality(row.get("quality") or row.get("evidence_quality")), 0),
        _timestamp(row.get("observed_at")),
        str(row.get("source") or row.get("source_id") or ""),
        str(row.get("type") or row.get("evidence_type") or ""),
        str(row.get("evidence_id") or ""),
    )


def _prepare(row: Mapping[str, Any]) -> dict[str, Any]:
    item = dict(row)
    item["evidence_id"] = validate_evidence_id(
        str(item["evidence_id"]) if item.get("evidence_id") else evidence_id_for_row(item)
    )
    source = str(item.get("source") or item.get("source_id") or "").strip()
    evidence_type = str(item.get("type") or item.get("evidence_type") or "").strip()
    if not source or not evidence_type:
        raise ValueError("citation candidate requires source and type")
    if item.get("observed_at") is None:
        raise ValueError(f"citation candidate {item['evidence_id']} requires observed_at")
    item["source"] = source
    item["type"] = evidence_type
    item["quality"] = _quality(item.get("quality") or item.get("evidence_quality"))
    item.setdefault("provenance", "OBSERVED")
    return item


def select_evidence_citations(
    rows: list[Mapping[str, Any]],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    """Screen, de-duplicate and deterministically rank evidence for citation.

    The first pass selects the strongest row for every source/type pair, which
    prevents one prolific source from crowding out independent evidence. The
    second pass fills remaining slots by the same quality/recency ordering.
    Duplicate IDs are resolved before either pass; this makes repeated refreshes
    idempotent and keeps provider requests stable.
    """

    bounded_limit = max(0, min(MAX_CITATION_SELECTION, int(limit)))
    if bounded_limit == 0 or not rows:
        return []

    best_by_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        candidate = _prepare(row)
        evidence_id = candidate["evidence_id"]
        previous = best_by_id.get(evidence_id)
        if previous is None or _candidate_key(candidate) > _candidate_key(previous):
            best_by_id[evidence_id] = candidate

    ordered = sorted(best_by_id.values(), key=_candidate_key, reverse=True)
    selected: list[tuple[dict[str, Any], str]] = []
    selected_ids: set[str] = set()
    selected_source_types: set[tuple[str, str]] = set()
    for candidate in ordered:
        key = (candidate["source"], candidate["type"])
        if key in selected_source_types:
            continue
        selected.append((candidate, "diverse_source_type"))
        selected_ids.add(candidate["evidence_id"])
        selected_source_types.add(key)
        if len(selected) >= bounded_limit:
            break
    if len(selected) < bounded_limit:
        for candidate in ordered:
            if candidate["evidence_id"] in selected_ids:
                continue
            selected.append((candidate, "additional_quality_recency"))
            selected_ids.add(candidate["evidence_id"])
            if len(selected) >= bounded_limit:
                break

    return [
        {
            **candidate,
            "citation_rank": rank,
            "citation_reason": reason,
        }
        for rank, (candidate, reason) in enumerate(selected, start=1)
    ]


def bind_citation_selection(
    rows: list[Mapping[str, Any]],
    *,
    binding_type: str,
    binding_id: int | str,
    limit: int,
) -> dict[str, Any]:
    """Attach selected citation rows to one auditable domain entity."""

    binding_type = str(binding_type or "").strip()
    if not binding_type:
        raise ValueError("binding_type must not be empty")
    return {
        "binding": {"entity_type": binding_type, "entity_id": str(binding_id)},
        "citations": select_evidence_citations(rows, limit=limit),
    }
