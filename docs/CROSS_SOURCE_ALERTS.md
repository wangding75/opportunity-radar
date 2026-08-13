# Cross-source confirmation scoring and alerts

T110-03 reads the persisted `cross_source_confirmations` record, applies
`cross-source-score-v1`, and stores the score, risk, breakdown, and score input
signature on that record. Delivery is fail-closed: the record must be
`CONFIRMED`, meet the independent-source and unique-claim thresholds, score at
least 70, and have risk at most 40.

Eligible records create one `AlertEvent` linked to the opportunity and its
keyword. The event key hashes the opportunity, confirmation input signature,
and score signature, so two opportunities with identical counts cannot collide;
replaying the same record updates no human state and creates no second event.
The existing alert lifecycle endpoint can ACK or resolve the event.

Administrators can run `POST /api/v1/alerts/cross-source/evaluate` with an
optional `opportunity_id`; readers can inspect the persisted result through
`GET /api/v1/alerts/cross-source/records`. The alerts worker runs both
confirmation materialization and delivery in bounded batches. Tests use only
`MOCK`/`SYNTHETIC` evidence and cover confirmed, suppressed, duplicate, retry,
RBAC, and ACK paths.
