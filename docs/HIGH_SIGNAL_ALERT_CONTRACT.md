# High-signal alert contract

T106-01 defines a deterministic, versioned eligibility decision before any
event or notification lifecycle runs. `HighSignalTriggerPolicy` defaults to:

- score at least 80;
- risk score at most 40;
- at least 3 evidence items;
- cross-source score at least 5 (the scoring model's two-source signal);
- an updated signal no older than 48 hours;
- non-dormant stage and `READY` or `DEGRADED` analysis status.

`evaluate_high_signal` evaluates every condition, returns `eligible`, and keeps
human-readable `trigger_reasons` or `failed_conditions`. It is fail-closed:
future timestamps, excluded stages, stale signals, failed analysis, insufficient
evidence, high risk, low score, or weak cross-source support are not eligible.

`high_signal_dedupe_key` hashes only meaningful signal state: contract and
algorithm versions, policy version, stable opportunity key, score/analysis
versions and signatures, stage, scores, evidence count, cross-source score, and
analysis status. Timestamps are deliberately excluded, so retrying evaluation
of the same state cannot create a new business event; a meaningful signal state
or policy change produces a new key. Event persistence, cooldown, ACK, and
delivery are implemented by subsequent T106 tasks.

T106-02 materializes eligible evaluations through the existing
`AlertEvent`/`AlertRule` tables under the `HIGH_SIGNAL_IMMEDIATE` system rule.
The same dedupe key is unique for a meaningful signal state. A changed state is
still suppressed during the policy cooldown (default 24 hours); after cooldown
expiry it can create one new event. The event message contains the trigger
reasons and dedupe key, and PostgreSQL evaluations use the existing advisory
alert lock. The admin endpoint is `POST /api/v1/alerts/high-signal/evaluate`;
the existing full alert evaluation includes high-signal materialization too.

## T106-03 priority and ACK lifecycle

Materialized alert events carry a bounded priority from `1` (info) through `5`
(critical). High-signal events are always priority `5`; ordinary rules derive
priority from score, risk, and evidence count. The API returns the priority and
all lifecycle audit fields.

The lifecycle is `NEW -> ACKNOWLEDGED -> RESOLVED`, with `DISMISSED` available
from `NEW` or `ACKNOWLEDGED`. Repeating the current state is idempotent;
terminal `DISMISSED` and `RESOLVED` events cannot be reopened. Each transition
records the UTC timestamp and authenticated actor in its corresponding
`*_at`/`*_by` fields. Existing events remain readable: their priority defaults
to `1` and legacy ACK timestamps are preserved.
