# Keyword burst replay and Mock acceptance

T107-04 adds `replay_keyword_bursts`, a bounded read-only service over the
existing daily trend materialization. It re-evaluates complete seven-day
window endpoints using the T107-01 contract, returns each versioned result and
input signature, and never creates `KeywordBurstRecord`, `AlertEvent`, or ACK
side effects. The range is capped at 52 windows and rejects reversed or
unbounded requests.

Administrators can run a replay through
`POST /api/v1/alerts/keyword-burst/replay?keyword_id=...&start_window_end=YYYY-MM-DD&end_window_end=YYYY-MM-DD`.
The result includes the number of windows, anomalous-window count, policy,
contract/algorithm versions, and all historical evaluations. The endpoint is
admin-only because replay can inspect historical signal evidence and is an
operational action; the service itself is deterministic and read-only.

Acceptance tests use only `MOCK`/`SYNTHETIC`-labelled fixtures. The Docker
Compose migration, API, and alerts worker are verified separately against the
repository PostgreSQL service; no real external data is collected.
