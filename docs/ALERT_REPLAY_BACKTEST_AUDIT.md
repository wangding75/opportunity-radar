# Alert / Replay / Backtest Temporal Audit

T120-04 adds `audit_alert_replay_backtest`, a read-only audit of the persisted
alert and historical-evaluation chain. It validates alert rule bounds, event
keys and lifecycle timestamps, queue leases and revisions, email/webhook
delivery identities and references, score-jump/risk/keyword-burst record
links, and replay cutoffs.

Score replay is checked at the first and last persisted snapshot boundary and
must return the latest snapshot at or before `as_of` with
`replay_mode=persisted_snapshot`. Backtests use only the active score model,
exclude snapshots newer than the evaluation clock, and expose bounded
candidate/immature/persisted counts with a mathematically consistent
persistence rate. Future snapshots are invalid state and are never allowed to
become backtest candidates.

Run the audit with:

```text
python scripts/audit_alert_replay_backtest.py
```

The report is synthetic/mock-only (`real_data_collected: 0`) and the tests
verify normal, empty, duplicate/read-only, tampered, future-time and lifecycle
failure cases.
