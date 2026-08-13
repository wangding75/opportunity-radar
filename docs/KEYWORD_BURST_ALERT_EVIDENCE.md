# Keyword burst alert evidence and explanation

T107-03 persists every detector result in `keyword_burst_records`. An
anomalous result is materialized as a `KEYWORD_BURST` alert only when the
bounded current/baseline window can resolve at least one original
`RawObservation`. Each evidence item uses the existing `ev1_<sha256>` identity
and stores source, type, quality, provenance, title, text, URL, and observation
time. At most 20 evidence rows are retained per evaluation.

The record also stores the contract and algorithm versions, policy, window
boundaries, counts, means, standard deviation, delta, growth, z-score,
comparison, reasons, evidence IDs, and input signature. The alert message
contains the same trace key and evidence IDs so the existing Alerts UI can show
the signal without inventing a second event model.

When trend materialization reports an anomaly but no raw evidence is resolvable,
the record is `REJECTED_NO_EVIDENCE` and no alert event is created. This is an
intentional fail-closed boundary for synthetic/manual trend rows and prevents a
derived count from being presented as an evidence-backed business alert.

Administrators can materialize the bounded detector through
`POST /api/v1/alerts/keyword-burst/evaluate`; authenticated readers can inspect
records through `GET /api/v1/alerts/keyword-burst/records`. The alerts worker
executes the same service during its normal alert iteration, so manual and
scheduled evaluation share the same signature and idempotency boundary.
