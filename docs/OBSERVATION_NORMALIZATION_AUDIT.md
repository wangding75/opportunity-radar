# Observation normalization audit

`backend/app/services/normalization_audit.py` defines the `normalization-v1`
invariants at the raw Observation boundary:

- SHA-256 content hashes are valid, unique, and reproducible from the stored
  input payload and instrumented-app metadata;
- every raw observation has exactly one normalized item and no normalized item
  is orphaned;
- normalized query/title/text whitespace and UTC-naive timestamps match the
  normalizer contract, while source identity and URLs remain traceable;
- canonical item keys are reproducible; and
- keyword mentions remain idempotent through their database uniqueness contract.

Run the audit after the database migration with:

```text
python scripts/audit_observation_normalization.py
```

The deterministic report is written to
`validation/observation_normalization_audit.json`. It uses no external data;
the report declares `real_data_collected=0` and
`SYNTHETIC_OR_MOCK_ONLY`.
