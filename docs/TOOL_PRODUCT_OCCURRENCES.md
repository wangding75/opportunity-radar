# Tool/Product First Appearance and Duplicate Recognition

T108-03 consumes the identified rows from T108-02 and materializes one
immutable occurrence classification per entity and normalized item. The
earliest observed evidence for an entity is `FIRST_SEEN`; every later evidence
row is `DUPLICATE`. Low-confidence, unresolved, and insufficient-evidence
entities are excluded from occurrence materialization so they cannot trigger a
false new-tool signal.

Occurrence rows retain the entity key, stable `ev1_` evidence ID, normalized item
ID, source, observed time, contract/algorithm versions, input signature, and
detection time. The `(entity_id, normalized_item_id)` and occurrence-key
constraints make retries safe. `POST
/api/v1/tool-products/normalize` runs both normalization and occurrence
materialization; `GET /api/v1/tool-products/occurrences` exposes the trace for
readers, while the explicit materialize endpoint is admin-only.

Tests use only `MOCK`/`SYNTHETIC` rows and cover chronological boundaries,
duplicates, retries, empty input, low confidence, and write authorization.
