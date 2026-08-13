# Daily opportunity digest contract

Version 1 defines a daily digest as a UTC calendar-day snapshot. Its window is
`[digest_date 00:00:00, digest_date + 1 day 00:00:00)` using the project’s
timezone-naive UTC database convention. `generated_at` records when the
snapshot was produced; it does not change the window.

The contract is implemented by `app.domain.digest.DailyDigest` and
`DigestItem`. It is intentionally separate from generation, persistence, API,
and UI code.

Business rules:

- `DORMANT` opportunities are excluded by the default selection policy.
- The default minimum score is 60, the default minimum evidence count is 1,
  and the default maximum is 20 items.
- Ranking is deterministic: score descending, risk ascending, last-seen
  descending, then stable opportunity key ascending.
- An opportunity can appear at most once. Item ranks are contiguous from 1.
- `EMPTY` is a valid result with zero items and zero candidates; it is not a
  fake successful result.
- `DEGRADED` requires a warning or generation error. A `READY` result must have
  at least one item.

Every item carries its stable opportunity identity, score/risk context,
analysis provider and signature, selection reasons, evidence IDs, and explicit
`OBSERVED`, `MOCK`, `SYNTHETIC`, or `MIXED` evidence provenance. The digest
also carries `contract_version`, `algorithm_version`, a selection policy, and a
SHA-256 `input_signature` over the bounded candidate meaning. The signature is
independent of database row order and changes when candidate meaning changes.

T104-02 consumes this contract to generate a digest; T104-03 persists and
serves it; T104-04 owns UI and scheduled Docker acceptance.

T104-03 persists one upserted row per UTC `digest_date` in `daily_digests`.
The read endpoints are `GET /api/v1/digests/daily` (latest when no date is
given), `GET /api/v1/digests/daily?digest_date=YYYY-MM-DD`, and the equivalent
date path. `POST /api/v1/digests/daily/generate` is an admin-only, audited
generation/upsert operation; missing snapshots return 404 rather than an
invented empty response. The `digest-daily` Compose worker runs this same
generator every `DIGEST_INTERVAL_SECONDS` (default 86400) and writes the
snapshot through the same idempotent persistence service.
