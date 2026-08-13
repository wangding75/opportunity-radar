# Weekly emerging-trend contract

Version 1 reports the most recent complete UTC week: Monday 00:00 (inclusive)
through the following Monday 00:00 (exclusive). The comparison baseline is the
immediately preceding complete seven-day interval. For an anchor on
2026-08-12, the report window is 2026-08-03 through 2026-08-10 and the baseline
is 2026-07-27 through 2026-08-03.

`app.domain.weekly_trends.WeeklyTrendReport` is the versioned output contract;
aggregation and persistence are separate tasks. Each item records current and
baseline observation/source counts, absolute delta, bounded momentum score,
selection reasons, last-seen time, a stable trend signature, and explicit
`OBSERVED`, `MOCK`, `SYNTHETIC`, or `MIXED` provenance.

The default selection policy requires at least three current observations, a
minimum absolute delta of one, and a 20% growth rate, with at most 20 items.
New signals with a zero baseline are allowed when configured and are represented
as `NEW_SIGNAL` with `growth_rate: null`; the contract never reports an
infinite or fabricated growth rate. `app.services.weekly_trends` aggregates the
bounded `KeywordTrendDaily` materialization over the two complete windows. It
uses distinct `KeywordMention.source_id` values when detail rows are available,
and falls back to the materialized daily source counts when only the bounded
trend table is present. Ranking is deterministic: momentum descending, delta
descending, current observations descending, then keyword ascending and ID.

The service reads provenance markers from linked `RawObservation.raw_payload`.
Unmarked rows are `OBSERVED`; a window containing multiple explicit markers is
`MIXED`. Candidates are capped at 100 before final selection, and a truncation
warning is retained in the report.

`EMPTY` is a valid zero-item result. `READY` requires at least one item, and
`DEGRADED` requires an explicit warning or generation error. The report stores
week/baseline boundaries, policy, algorithm/contract versions, generation time,
and an order-independent SHA-256 input signature over the bounded candidate
meaning.
