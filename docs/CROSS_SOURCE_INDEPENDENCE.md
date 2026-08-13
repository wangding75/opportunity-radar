# Source independence and evidence deduplication

T110-02 materializes `CROSS_SOURCE_CONFIRMATION` records from the existing `OpportunityEvidence -> NormalizedItem -> RawObservation` chain. It does not create an alert. Each bounded evaluation stores the contract/algorithm/policy versions, stable input signature, evidence IDs, source endpoints, claim fingerprints, freshness counts, reasons, and the selected citation rows.

The service uses `source_endpoint_key` from T110-01: pages on one hostname are one source, `www.` is normalized, and an invalid/missing URL falls back to the normalized source ID. Identical evidence IDs are removed, and normalized title/text fingerprints collapse syndicated copies. The evaluation is confirmed only when both the independent endpoint and unique claim thresholds pass. Invalid content hashes and empty evidence are stored as `NO_EVIDENCE`; they never become a positive signal.

`materialize_cross_source_confirmations` is transaction-scoped and idempotent on `input_signature`. A rollback removes the derived record and a retry can recreate it; an unchanged replay reports a duplicate. The alerts worker evaluates up to 100 non-dormant opportunities per run using the existing derived-analysis lock. T110-03 scores only `CONFIRMED` records, persists the score/risk breakdown, and creates the linked AlertEvent when delivery gates pass.
