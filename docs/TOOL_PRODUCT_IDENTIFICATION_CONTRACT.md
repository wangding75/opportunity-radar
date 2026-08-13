# Tool/product identification contract

T108-01 defines `tool-product-identification-v1`. The input is a bounded list
of at most 20 evidence items, each carrying the existing `ev1_<sha256>` ID,
source, timestamp, provenance, and bounded text. Duplicate evidence IDs are
removed before scoring and do not inflate source/evidence counts.

The output records policy and algorithm versions, normalized display name,
stable `tp1_<sha256>` entity key, `TOOL`/`PRODUCT`/`SERVICE`/`UNKNOWN` kind,
confidence, distinct sources, ordered evidence IDs, first/last seen times,
human-readable reasons, and a stable input signature. Status is one of
`IDENTIFIED`, `LOW_CONFIDENCE`, `INSUFFICIENT_EVIDENCE`, or `UNRESOLVED`.
Unresolved and insufficient results never receive an entity key. Low-confidence
results may receive a provisional key for later review but are not an alert by
themselves.

The default policy requires two deduplicated evidence items, one source, and
0.65 confidence. T108-02 consumes this contract for cross-source entity
normalization; T108-03 uses the identified/new state and evidence IDs for
alerting. No real external data is required for the contract tests.
