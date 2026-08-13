# Hiring surge Mock acceptance

`backend/app/fixtures/hiring_surge_mock.json` is a bounded 19-record fixture: six baseline job records, twelve distinct current jobs, and one same-day duplicate. Every record is marked `SYNTHETIC`, uses a `synthetic-` source ID, and points to `synthetic.invalid`; it is not production collection data.

The acceptance loader uses the real path:

`fixture -> store_collected -> normalize/discover keywords -> graph/opportunity refresh -> HiringSurge detector -> HiringSurgeRecord -> AlertEvent`

Run it locally against the configured database with:

```text
python -m app.mock_hiring_surge
```

Run it against the Compose PostgreSQL API image after migrations with:

```text
docker compose run --rm api python -m app.mock_hiring_surge
```

The command prints a JSON result containing the fixture class, import counts, linked keyword/opportunity IDs, and alert materialization counts. Re-running the command reports duplicate ingestion and an idempotent alert evaluation rather than creating a second `AlertEvent`. The loader refuses unmarked fixtures and source IDs that do not start with `synthetic-` or `mock-`.

Automated coverage is in `backend/tests/test_hiring_surge_mock_acceptance.py`. No real external data is collected by this task.
