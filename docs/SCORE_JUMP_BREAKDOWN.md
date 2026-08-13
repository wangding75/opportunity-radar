# Score jump breakdown and evidence binding

T111-03 extends `score_jump_records` with the previous and current score
breakdowns, a structured change breakdown, and bounded evidence citations.
Evidence is read from the opportunity's `OpportunityEvidence` chain back to
`NormalizedItem` and `RawObservation`, and is limited to the open interval
`(previous_snapshot.calculated_at, current_snapshot.calculated_at]`. This keeps
the explanation reproducible and prevents future or boundary observations from
being attributed to a jump.

Each bound citation contains its stable `ev1_<sha256>` ID, source metadata,
quality/acquisition fields, provenance, text/title/URL, and observation time.
Invalid content hashes are skipped fail-closed. The record remains useful when
there is no evidence: its evidence arrays are empty rather than fabricated.

The service remains idempotent on the existing score-jump input signature, and
the read endpoint exposes `previous_breakdown`, `current_breakdown`,
`change_breakdown`, `evidence_ids`, and `evidence` for audit and UI consumers.
