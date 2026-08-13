# Score jump replay and alert delivery

T111-04 completes the score-jump delivery path. The alert materializer reads
persisted `SCORE_JUMP` records, requires a non-empty, internally consistent
evidence binding, and creates one `AlertEvent` with a deterministic event key.
Missing evidence is reported as `evidence_missing` and cannot be presented as
a successful alert. Repeated worker or API runs link to the existing event and
do not duplicate side effects.

Admins can run `POST /api/v1/scoring/score-jumps/evaluate` to detect jumps and
deliver alerts in one transaction. The existing AlertEvent status API provides
the acceptance lifecycle (`NEW` -> `ACKNOWLEDGED` -> `RESOLVED`, or dismissal).

Admins can run `POST /api/v1/scoring/score-jumps/replay` with an opportunity ID
and `as_of` timestamp. Replay reads the latest two persisted snapshots at or
before that timestamp, returns the same contract/algorithm evaluation plus
breakdown and evidence bindings, and persists neither score-jump records nor
alerts. The replay is therefore bounded, deterministic, auditable, and safe to
retry.
