# Frontend/backend RBAC consistency

`scripts/validate_frontend_rbac.py` compares the frozen `rbac-v1` role levels,
the live API permission inventory, frontend visibility markers, and compiled
static JavaScript. It checks both static buttons and dynamically rendered
research/alert/watch actions, then runs `node --check` on every compiled module
when Node is available. Python-only production images report that optional
syntax check as `ENVIRONMENT_BLOCKED`; the frontend build gate runs it in the
Node build environment.

The check writes `validation/frontend_rbac_consistency.json` and is part of
`scripts/validate_product.sh`. It uses no external or real data.
