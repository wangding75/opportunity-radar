# Risk escalation detector

T112-02 provides a bounded, read-only detector over the latest two persisted
`OpportunityScoreSnapshot` rows for each non-`DORMANT` opportunity. It maps the
risk scores through `risk-escalation-v1`, supports `escalated_only` rule
matching, and returns versioned evaluations without writing records or alerts.

The API is `GET /api/v1/risk/escalations` with optional `opportunity_id`,
`escalated_only`, and bounded `limit` parameters. It uses the normal read/RBAC
boundary. T112-03 owns evidence/explanation persistence and state transition
records; this detector remains safe to retry because it has no write side
effects.
