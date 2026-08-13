# Docker PostgreSQL concurrency validation

T121-01 provides an isolated Docker environment for bounded PostgreSQL
concurrency testing:

```text
docker compose -f docker-compose.concurrency.yml -p opportunity-radar-t12101 up --build --abort-on-container-exit --exit-code-from concurrency-runner
docker compose -f docker-compose.concurrency.yml -p opportunity-radar-t12101 down -v --remove-orphans
```

The runner applies the real Alembic head, starts eight concurrent application
workers, and exercises the existing PostgreSQL advisory-lock/idempotency path
for score-jump materialization and alert-event creation. It requires exactly
one score-jump record, one alert event, and the original two score snapshots
after all workers commit. The fixture is synthetic only and collects zero real
external records.

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
