# Hiring surge alerts

`HIRING_SURGE` is the evidence-backed alert materialization layer for the read-only hiring surge detector. It evaluates bounded JOB windows, persists the versioned comparison, and creates an `AlertEvent` only when the detector's evidence IDs resolve back to stored `RawObservation` and `NormalizedItem` rows.

## State and association

Each evaluation is stored in `hiring_surge_records` with the contract version, algorithm version, policy, current/baseline windows, job/source/evidence counts, diversity metrics, explanation, evidence citations, and stable `detection_signature`. A non-dormant opportunity linked through `OpportunityKeyword` is associated deterministically by highest opportunity score and then lowest ID. The resulting alert carries both `keyword_id` and `opportunity_id` so the existing alert acknowledgement lifecycle can be used without a separate workflow.

## Safety and retry behavior

- A surge with no resolvable raw evidence is persisted as `REJECTED_NO_EVIDENCE`; no alert event is emitted.
- `detection_signature` is unique, so an unchanged evaluation is a duplicate and cannot create a second event.
- The alert rule and event creation happen in the caller's transaction. A rollback removes the record and event together, allowing a later worker retry to recreate exactly one pair.
- The worker evaluates hiring alerts in `all` and `alerts` modes. Operators can run `POST /api/v1/alerts/hiring/evaluate` (admin scope) and inspect records with `GET /api/v1/alerts/hiring/records` (read scope).

All test fixtures are explicitly `MOCK`/`SYNTHETIC`; production materialization reads only already-ingested job observations.
