# Docker PostgreSQL concurrency validation

T121-01 provides an isolated Docker environment for bounded PostgreSQL
concurrency testing:

```text
docker compose -f docker-compose.concurrency.yml -p opportunity-radar-t12101 up --build --abort-on-container-exit --exit-code-from concurrency-runner
docker compose -f docker-compose.concurrency.yml -p opportunity-radar-t12101 down -v --remove-orphans
```

The runner applies the real Alembic head and executes
`scripts/validate_postgres_runtime_e2e.py` against the same PostgreSQL service.
It reports the PostgreSQL version and migration revision, then uses independent
SQLAlchemy sessions to verify the T131 OWNER invariant, an exclusive
`ProbeTask` lease, durable email queue idempotency under eight concurrent
workers, and dispose/reconnect recovery. Every fixture row is prefixed with a
unique run ID and is deleted in a `finally` cleanup block.

The PostgreSQL service is health-gated before the runner starts, and its named
volume is separate from the production compose volume.

T121-02 adds a real collection-worker lease and owner contract. Run its isolated
check with:

```text
docker compose -f docker-compose.collection-concurrency.yml -p opportunity-radar-t12102 up --build --abort-on-container-exit --exit-code-from collection-concurrency-runner
docker compose -f docker-compose.collection-concurrency.yml -p opportunity-radar-t12102 down -v --remove-orphans
```

The runner starts eight application workers against one due `ProbeTask`. The
database lease allows exactly one claim; the selected worker records one
`CollectionRun`, one synthetic raw observation and one normalized item, and
releases the lease. The other workers observe no due task. The fixture is
Synthetic-only and collects zero real external records.
