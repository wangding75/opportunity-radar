# Opportunity / Score / Lineage Correctness Audit

The T120-03 audit reads the persisted product chain and reports drift without
refreshing or mutating opportunities. It is implemented by
`app.services.opportunity_score_lineage_audit.audit_opportunity_score_lineage`
and exposed for repeatable validation through
`scripts/audit_opportunity_score_lineage.py`.

The audit verifies:

- every opportunity has a valid primary keyword link, bounded score/risk, and
  an evidence count equal to its persisted evidence rows;
- evidence points to an existing normalized item and preserves its observed
  timestamp; keyword/evidence rows are idempotent;
- score breakdowns match the opportunity fields, and current `score-v1`
  inputs reproduce the stored total and components;
- every score snapshot has a stable SHA-256 input signature, a matching model
  version, bounded values, and an idempotent key;
- cluster signatures hash their canonical keyword IDs, generations are
  contiguous, historical intervals are ordered, and the current opportunity
  state matches its latest version;
- lineage references existing opportunities, forbids self-edges and duplicate
  edges, and remains acyclic.

Empty databases are a valid PASS. The generated report records
`real_data_collected: 0` and `SYNTHETIC_OR_MOCK_ONLY`; tests use only synthetic
rows. A populated production opportunity must have its persisted score,
evidence, keyword links, cluster version and score snapshot before it can pass.
