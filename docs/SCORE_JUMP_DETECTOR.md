# Score jump detector

T111-02 reads the existing `opportunity_score_snapshots` history and compares
the latest two snapshots for up to 100 non-dormant opportunities per run. Each
comparison is persisted in `score_jump_records` with contract/algorithm/policy
versions, snapshot signatures, versions/times, deltas, status, reasons, and a
stable evaluation signature.

The detector is idempotent on that evaluation signature. Missing history and
model-version changes are persisted as suppressed states and cannot create a
positive signal. A transaction rollback removes the record and a retry can
recreate it. Admins can run `POST /api/v1/scoring/score-jumps/evaluate`; readers
can inspect `GET /api/v1/scoring/score-jumps/records`. T111-04 materializes an
evidence-backed `AlertEvent` for each eligible record and links it through
`alert_event_id`.
