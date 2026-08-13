# Evidence Citation Contract v1

This document freezes the evidence representation shared by Opportunity Radar's
analysis providers and citation consumers.

## Evidence identity

The public `evidence_id` is derived from the unique ingestion
`RawObservation.content_hash`:

```text
evidence_id = "ev1_" + lowercase(content_hash)
```

`content_hash` is the existing SHA-256 ingestion identity and includes the source,
query, observation content, item type, payload, observation day, and relevant app
metadata. The database-local `RawObservation.id`, `NormalizedItem.id`, and
`OpportunityEvidence.id` must never be used as citation identities. The same
observation therefore keeps the same citation ID when it is attached to multiple
opportunities or restored into another database.

The `ev1_` prefix freezes the ID algorithm version. A future algorithm must use a
new prefix and must not silently reinterpret existing IDs.

## Provider contract

HTTP analysis requests contain `citation_contract_version: "1"`. Every evidence
row contains these fields:

- `evidence_id`: stable `ev1_<64 lowercase hex characters>` identity;
- `source`, `type`, `item_type`, `quality`, and `acquisition_method`: provenance
  and classification fields;
- `title`, `text`, `url`, and `observed_at`: the bounded citation material;
- `provenance`: `OBSERVED`, `MOCK`, or `SYNTHETIC`.

`MOCK` and `SYNTHETIC` are explicit non-real data classes. They must not be
reported as real external evidence quality. An ingestion payload can mark them
with `_provenance`, `provenance`, `_data_class`, or `data_class`.

Provider failures remain failures. A provider result without the frozen contract
version or stable evidence IDs cannot be treated as a successful citation-aware
analysis result.

## Analysis output

An analysis provider must return the five structured analysis fields plus a
`citations` array. Each item is `{ "evidence_id": "ev1_...", "claim": "..." }`.
The ID must occur exactly once in the request's evidence array; unknown, duplicate,
missing, or empty citations are rejected when evidence was supplied. Validated
citations are persisted with the Opportunity analysis result, so a later API read
does not need to call the provider again.

When more than one analysis provider is explicitly configured, the executor runs
each eligible provider, compares the five structured fields, and records a
`conflict` report with the selected provider, policy, conflicting fields, and
bounded provider values. `priority` selects the first successful provider in the
configured order; `majority` selects the successful result with the greatest
field-level agreement, breaking ties by priority. If every provider fails, the
analysis remains failed/degraded through the existing retry queue.
