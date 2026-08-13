# Deterministic Data-Correctness Gate

T120-05 aggregates the four persisted-chain correctness audits into
`run_data_correctness_gate`:

- observation normalization;
- keyword, trend and graph materializations;
- opportunity score, evidence, cluster and lineage state;
- alert lifecycle, delivery, replay and backtest boundaries.

The gate is read-only and emits no wall-clock timestamp. Repeating it against
the same database state therefore produces the same JSON result. Any child
audit failure propagates to the aggregate `FAIL` status with the audit name and
rule included in `violations`.

Run it with:

```text
python scripts/validate_data_correctness_gate.py
```

The report is synthetic/mock-only and records `real_data_collected: 0`.
