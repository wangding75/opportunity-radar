# High-signal alert acceptance

`backend/tests/test_high_signal_alert_acceptance.py` is the deterministic
synthetic acceptance path for T106-04. It exercises the business chain in one
test:

1. the versioned mock analysis contract returns a `MOCK` result and a bound
   citation for a synthetic evidence item;
2. a high-signal opportunity is inserted with five evidence items, cross-source
   support, a ready analysis state, and the mock analysis output;
3. the real alerts worker claims `AlertEvaluationQueue`, materializes exactly
   one priority-5 `HIGH_SIGNAL_IMMEDIATE` event, and records the dedupe key;
4. a second worker pass is empty and produces no duplicate event;
5. the API lists the event and persists the authenticated lifecycle transition
   to `ACKNOWLEDGED`.

Run the test with:

```text
cd backend
python -m pytest tests/test_high_signal_alert_acceptance.py -q
```

For the external-process contract check, start the repository mock service with
`docker compose up -d mock-analysis`, call `GET /health` and `POST /v1/analyze`,
then stop it with `docker compose down`. The fixture is explicitly `MOCK` or
`SYNTHETIC`; no real external data is collected.
