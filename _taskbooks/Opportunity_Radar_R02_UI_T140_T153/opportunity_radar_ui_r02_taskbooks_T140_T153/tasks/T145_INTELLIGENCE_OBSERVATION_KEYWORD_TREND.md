# T145 — Batch B: Observation, Keyword Discovery, Watch Keywords and Trend (P06–P10)

## Objective

Implement the first core intelligence workflow as one cohesive batch because these pages share query filters, keyword context, evidence navigation, and trend state.

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

Pages P06–P10.

## Required references

- `dependencies/ui_reference_r02/screens/P06_observation_list.png`
- `dependencies/ui_reference_r02/screens/P07_observation_detail.png`
- `dependencies/ui_reference_r02/screens/P08_keyword_discovery.png`
- `dependencies/ui_reference_r02/screens/P09_watch_keywords.png`
- `dependencies/ui_reference_r02/screens/P10_trend_analysis.png`
- `docs/ui-r02/RESOLVED_UI_BACKEND_BINDINGS.json`

## Execution steps

1. Implement P06 list filters/sort/pagination and read-only evidence behavior using actual Observation schema.
2. Implement P07 detail with source/keyword/opportunity links and safe external-source link behavior. Do not add edit/delete of raw evidence.
3. Implement P08 Keyword Discovery and conditional follow/watch actions exactly per T140 status.
4. Implement P09 Watch Keyword list/editor using only actual schema fields. Hide any unsupported write/schedule actions instead of stubbing them.
5. Implement P10 trend range controls using only backend-supported windows/parameters; client-only filtering is allowed only on data already returned.
6. Preserve list filter/query context when drilling into P07/P10 and navigating back where practical.
7. Test loading/empty/no-result/partial/stale/error states and all cross-page links in this batch.

## Acceptance gates

- [ ] P06–P10 use shared table/filter/drawer/status primitives.
- [ ] Raw Observation remains read-only.
- [ ] Unsupported Watch Keyword writes are omitted/guarded, not fake-wired.
- [ ] Trend does not send unsupported query parameters.
- [ ] Cross-page evidence/keyword navigation works and tests pass.

## Required outputs

- `validation/ui_r02/T145_PAGE_REVIEW.md`
- `validation/ui_r02/T145_INTERACTION_TESTS.md`
- `validation/ui_r02/T145_TEST_REPORT.md`

## Commit / stop rule

After all acceptance gates pass, create one local commit for this task with a clear message and proceed to the next task automatically. Do **not** push. If there are unresolved `DEFERRED_UNAVAILABLE` UI/backend gaps, include them in the required registry and still PASS if the implemented UI safely omits/guards those capabilities.
