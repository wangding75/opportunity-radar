"""Frozen product permission matrix shared by auth, API validation and audits."""

from __future__ import annotations

from copy import deepcopy

PERMISSION_MATRIX_VERSION = "rbac-v1"

VALID_ROLES = ("OWNER", "ADMIN", "RESEARCHER", "VIEWER")
ROLE_LEVEL = {"VIEWER": 10, "RESEARCHER": 20, "ADMIN": 30, "OWNER": 40}
SCOPE_MINIMUM_ROLE = {"read": "VIEWER", "write": "RESEARCHER", "admin": "ADMIN"}

# The minimum role is the backend authorization boundary. The explicit role list
# in the serialized snapshot is intentional: it is the reviewable contract that
# UI, API and audit checks can compare without reimplementing role inheritance.
CAPABILITY_MATRIX = {
    "product.read": {"scope": "read", "minimum_role": "VIEWER"},
    "auth.me": {"scope": "read", "minimum_role": "VIEWER"},
    "auth.tokens.read": {"scope": "read", "minimum_role": "VIEWER"},
    "auth.tokens.write": {"scope": "write", "minimum_role": "RESEARCHER", "interactive_session": True},
    "research.write": {"scope": "write", "minimum_role": "RESEARCHER"},
    "alerts.rules.write": {"scope": "write", "minimum_role": "RESEARCHER"},
    "data.ingest": {"scope": "admin", "minimum_role": "ADMIN"},
    "data.collect": {"scope": "admin", "minimum_role": "ADMIN"},
    "analysis.execute": {"scope": "admin", "minimum_role": "ADMIN"},
    "alerts.evaluate": {"scope": "admin", "minimum_role": "ADMIN"},
    "operations.read": {"scope": "admin", "minimum_role": "ADMIN"},
    "operations.write": {"scope": "admin", "minimum_role": "ADMIN"},
    "source.manage": {"scope": "admin", "minimum_role": "ADMIN"},
    "users.manage": {"scope": "admin", "minimum_role": "ADMIN"},
    "owner.manage": {"scope": "admin", "minimum_role": "OWNER", "owner_only": True},
    "exports.read": {"scope": "read", "minimum_role": "VIEWER"},
    "metrics.read": {"scope": "read", "minimum_role": "VIEWER"},
}


def role_can(role: str, minimum_role: str) -> bool:
    """Return whether a role reaches a matrix boundary."""

    return ROLE_LEVEL.get(role, -1) >= ROLE_LEVEL[minimum_role]


def scopes_for_role(role: str) -> frozenset[str]:
    """Return the maximum token/session scopes granted by a live role."""

    return frozenset(scope for scope, minimum_role in SCOPE_MINIMUM_ROLE.items() if role_can(role, minimum_role))


def roles_for_capability(capability: str) -> tuple[str, ...]:
    """Return the roles explicitly allowed by one frozen capability entry."""

    entry = CAPABILITY_MATRIX[capability]
    if entry.get("owner_only"):
        return ("OWNER",)
    minimum_role = entry["minimum_role"]
    return tuple(role for role in VALID_ROLES if role_can(role, minimum_role))


def permission_matrix_snapshot() -> dict:
    """Return a JSON-safe, reviewable copy of the frozen matrix."""

    capabilities = {}
    for capability, entry in CAPABILITY_MATRIX.items():
        row = deepcopy(entry)
        row["roles"] = list(roles_for_capability(capability))
        capabilities[capability] = row
    return {
        "matrix_id": "opportunity-radar-rbac-permission-matrix",
        "matrix_version": PERMISSION_MATRIX_VERSION,
        "role_order": list(VALID_ROLES),
        "role_level": dict(ROLE_LEVEL),
        "scope_minimum_role": dict(SCOPE_MINIMUM_ROLE),
        "role_scopes": {role: sorted(scopes_for_role(role)) for role in VALID_ROLES},
        "capabilities": capabilities,
        "invariants": [
            "A live role is an upper bound for every session or personal-token scope.",
            "Only OWNER may create or mutate an OWNER account.",
            "The last enabled OWNER cannot be removed or disabled.",
            "Session write and admin mutations require a valid CSRF token.",
            "Production authentication defaults fail closed through AUTH_MODE=rbac.",
        ],
    }


def required_role_for_scope(scope: str) -> str:
    return SCOPE_MINIMUM_ROLE[scope]
