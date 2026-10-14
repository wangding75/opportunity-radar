# T149 — Batch F: Alert Inbox and Alert Rules (P24–P25)

## Objective

Implement triggered-alert inspection separately from rule configuration. The inbox is event/history oriented; rules are configuration oriented. Do not mix or invent notification channels.

## Mandatory execution rules

- Repository root: `D:\github\opportunity-radar` unless the actual working directory is already the repository root.
- Read this taskbook, `../dependencies/ui_reference_r02/UI_REFERENCE_POLICY.md`, relevant PNGs, and the relevant R02 metadata before editing.
- Do not treat Stitch mock data or labels as backend truth.
- Ordinary build/test/lint/type/API mismatches must be diagnosed and fixed in the same task.
- Missing UI-required backend capability is **not a blocker**: first attempt a minimal safe backend-interface supplement; if that is not safe/possible, register `DEFERRED_UNAVAILABLE`, adapt/hide the UI, and continue.
- Backend supplementation may expose an already-existing business capability, but must not create new business semantics, scoring logic, permission semantics, worker behavior, scheduling meaning, alert meaning, or audit meaning just to satisfy UI.
- Preserve authorization checks and audit requirements on every newly exposed write interface.
- Existing UI visual implementation is deprecated. Do not copy old visual markup/CSS merely to save time. Reusable non-visual API clients, domain types, state/query utilities, validators, and tests may be retained only after review.
- No fake completion: no hardcoded success states, fake API responses in production paths, placeholder buttons wired to no-op handlers, or tests that only assert source strings.
- For every page, implement Loading/Empty/Error/Permission/No Result/Partial states where applicable, not only the happy path.
- Do not push to any remote. Local commits are allowed as task checkpoints; never amend/rebase/squash/force-push during this sequence.
- Final result for each task is exactly `PASS` or `BLOCKED`. `BLOCKED` is reserved for a genuine external blocker that prevents safe repository work; deferred backend gaps are not blockers.


## Scope

Pages P24–P25.

## Required references

- `dependencies/ui_reference_r02/screens/P24_alert_inbox.png`
- `dependencies/ui_reference_r02/screens/P25_alert_rules.png`
- `docs/ui-r02/RESOLVED_UI_BACKEND_BINDINGS.json`

## Execution steps

1. Implement P24 status/filter/list and Alert Detail Drawer using actual alert-inbox fields.
2. Implement read/unread/all-read actions only when confirmed; otherwise hide them and keep inbox useful as a read view.
3. Implement P25 rule table and schema-driven Rule Editor. Render only actual trigger-rule fields and actual notification channels from T140.
4. Do not copy screenshot mock rule names, cloud/score examples, Slack icons, or speculative test/delete controls into production behavior.
5. Use confirm dialog for destructive rule deletion only if deletion is actually supported.
6. Wire P24 -> P13/P25 and P25 -> P24 with rule filter context.
7. Test invalid configuration/channel warning/delivery failure and form validation states.

## Acceptance gates

- [ ] Inbox and rule management are distinct but cross-linked.
- [ ] No unverified channel/provider is implemented.
- [ ] Unsupported test/delete/read-state operations are hidden.
- [ ] Rule schema matches backend exactly.
- [ ] Batch tests pass.

## Required outputs

- `validation/ui_r02/T149_PAGE_REVIEW.md`
- `validation/ui_r02/T149_INTERACTION_TESTS.md`
- `validation/ui_r02/T149_TEST_REPORT.md`

## Commit / stop rule

After all acceptance gates pass, create one local commit for this task with a clear message and proceed to the next task automatically. Do **not** push. If there are unresolved `DEFERRED_UNAVAILABLE` UI/backend gaps, include them in the required registry and still PASS if the implemented UI safely omits/guards those capabilities.
