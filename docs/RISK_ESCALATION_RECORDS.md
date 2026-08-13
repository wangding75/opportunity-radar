# Risk escalation evidence, explanation, and delivery state

T112-03 persists one `risk_escalation_records` row per stable evaluation input
signature. The row stores the versioned policy and model fields, previous and
current risk levels/scores/breakdowns, a structured change breakdown, reasons,
bounded evidence citations, and `delivery_status`.

`ESCALATED` evaluations with resolvable evidence become `DELIVERED` through a
single deterministic `AlertEvent`. Escalations without evidence are persisted
as `REJECTED_NO_EVIDENCE` and never create an alert. `STABLE`, `DE_ESCALATED`,
`NO_BASELINE`, `VERSION_MISMATCH`, and `INVALID_SEQUENCE` records are retained
with `SUPPRESSED` delivery state for auditability. Repeated execution is
idempotent and transaction rollback permits a clean retry.

Admins can run `POST /api/v1/alerts/risk/evaluate`; readers can inspect
`GET /api/v1/alerts/risk/records`. The alerts worker runs the same materializer
inside its existing lease/heartbeat transaction.

`POST /api/v1/alerts/risk/replay` performs a bounded, read-only evaluation at
an `as_of` timestamp. The checked-in `risk-escalation-mock-v1` fixture and
`python -m app.mock_risk_escalation` exercise the real snapshot/evidence path
using only explicitly `SYNTHETIC` data; fixture source IDs must use the
`synthetic-` or `mock-` prefix.
