from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable


ANALYSIS_RESULT_FIELDS = (
    "summary",
    "target_user",
    "business_model",
    "monetization",
    "risk_notes",
)


@dataclass(frozen=True)
class ProviderResultCandidate:
    provider_id: str
    priority_rank: int
    result: Any


def _normalize(value: Any) -> str:
    return " ".join(str(value or "").strip().split()).casefold()


def _display(value: Any) -> str:
    return " ".join(str(value or "").strip().split())[:500]


def build_conflict_report(
    candidates: Iterable[ProviderResultCandidate],
    *,
    selected_provider_id: str,
    selection_policy: str,
    errors: Iterable[str] = (),
) -> dict[str, Any]:
    candidates = list(candidates)
    conflicts: dict[str, list[dict[str, str]]] = {}
    agreements: dict[str, int] = {}
    for field in ANALYSIS_RESULT_FIELDS:
        values: dict[str, str] = {}
        normalized_values: Counter[str] = Counter()
        for candidate in candidates:
            value = getattr(candidate.result, field, "")
            normalized = _normalize(value)
            normalized_values[normalized] += 1
            values[candidate.provider_id] = _display(value)
        agreements[field] = max(normalized_values.values(), default=0)
        if len(normalized_values) > 1:
            conflicts[field] = [
                {"provider_id": provider_id, "value": value}
                for provider_id, value in sorted(values.items())
            ]
    return {
        "status": "CONFLICT" if conflicts else "CONSISTENT",
        "selection_policy": selection_policy,
        "selected_provider_id": selected_provider_id,
        "provider_ids": [candidate.provider_id for candidate in candidates],
        "provider_count": len(candidates),
        "conflicting_fields": sorted(conflicts),
        "agreements": agreements,
        "conflicts": conflicts,
        "errors": [str(error)[:500] for error in errors][:10],
    }


def select_provider_result(
    candidates: Iterable[ProviderResultCandidate],
    *,
    selection_policy: str = "priority",
    errors: Iterable[str] = (),
) -> tuple[ProviderResultCandidate, dict[str, Any]]:
    candidates = sorted(
        list(candidates),
        key=lambda candidate: (candidate.priority_rank, candidate.provider_id),
    )
    if not candidates:
        raise ValueError("cannot select a result from no provider candidates")
    selection_policy = str(selection_policy or "priority").strip().lower()
    if selection_policy not in {"priority", "majority"}:
        raise ValueError(f"unsupported provider selection policy: {selection_policy}")

    if selection_policy == "priority":
        selected = candidates[0]
    else:
        scores: dict[str, int] = {}
        for candidate in candidates:
            score = 0
            for field in ANALYSIS_RESULT_FIELDS:
                normalized = _normalize(getattr(candidate.result, field, ""))
                votes = sum(
                    1
                    for other in candidates
                    if _normalize(getattr(other.result, field, "")) == normalized
                )
                score += votes
            scores[candidate.provider_id] = score
        selected = min(
            candidates,
            key=lambda candidate: (-scores[candidate.provider_id], candidate.priority_rank, candidate.provider_id),
        )

    report = build_conflict_report(
        candidates,
        selected_provider_id=selected.provider_id,
        selection_policy=selection_policy,
        errors=errors,
    )
    report["selection_score"] = (
        sum(
            sum(
                1
                for other in candidates
                if _normalize(getattr(other.result, field, ""))
                == _normalize(getattr(selected.result, field, ""))
            )
            for field in ANALYSIS_RESULT_FIELDS
        )
        if selection_policy == "majority"
        else None
    )
    return selected, report
