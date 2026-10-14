# UI Reference Policy

## Authoritative use

- PNG screenshots define visual composition, hierarchy, density, spacing, alignment, and intended component placement.
- `DESIGN.md` defines the common visual token baseline.
- `ui_metadata_r02` defines intended interaction/navigation semantics and marks many backend actions as conditional.
- Actual repository code defines routes, API contracts, schema, permissions, business semantics, and backend capability.

## Non-authoritative content

The screenshots contain mock names, values, providers, channels, versions, URLs, status counts, and sometimes speculative controls. These are **visual examples only**. Never implement them as business facts without T140 verification.

## Mandatory conflict handling

If a screen requires data/action not exposed by the current backend:

1. First determine whether the underlying business capability already exists and only an API exposure/response field is missing.
2. If yes, add the smallest safe backend interface necessary, preserving current domain semantics and authorization. Add tests.
3. If safe supplementation is impossible or the business capability itself does not exist, record it as `DEFERRED_UNAVAILABLE`, hide/disable/omit the UI action as appropriate, and continue the UI program. This condition must **not block** subsequent taskbooks.
4. Never invent new domain logic solely to make the visual prototype appear complete.
