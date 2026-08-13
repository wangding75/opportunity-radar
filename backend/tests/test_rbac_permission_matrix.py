from __future__ import annotations

from app.services.auth import Principal
from app.services.permissions import (
    CAPABILITY_MATRIX,
    ROLE_LEVEL,
    permission_matrix_snapshot,
    scopes_for_role,
)


def test_frozen_matrix_has_explicit_role_and_scope_contracts():
    matrix = permission_matrix_snapshot()
    assert matrix["matrix_version"] == "rbac-v1"
    assert matrix["role_order"] == ["OWNER", "ADMIN", "RESEARCHER", "VIEWER"]
    assert matrix["role_scopes"] == {
        "OWNER": ["admin", "read", "write"],
        "ADMIN": ["admin", "read", "write"],
        "RESEARCHER": ["read", "write"],
        "VIEWER": ["read"],
    }
    assert len(matrix["capabilities"]) == len(CAPABILITY_MATRIX)


def test_role_scopes_and_principal_permissions_are_upper_bounded_by_live_role():
    assert scopes_for_role("VIEWER") == frozenset({"read"})
    assert scopes_for_role("RESEARCHER") == frozenset({"read", "write"})
    assert ROLE_LEVEL["OWNER"] > ROLE_LEVEL["ADMIN"] > ROLE_LEVEL["RESEARCHER"] > ROLE_LEVEL["VIEWER"]

    demoted_token = Principal(
        actor="token:demoted/matrix",
        role="VIEWER",
        user_id=1,
        auth_type="api_token",
        scopes=frozenset({"read", "write", "admin"}),
    )
    assert demoted_token.has_scope("read")
    assert not demoted_token.has_scope("write")
    assert not demoted_token.has_scope("admin")


def test_owner_boundary_is_explicit_and_non_owner_capabilities_are_bounded():
    assert CAPABILITY_MATRIX["owner.manage"]["owner_only"] is True
    assert permission_matrix_snapshot()["capabilities"]["owner.manage"]["roles"] == ["OWNER"]
    assert permission_matrix_snapshot()["capabilities"]["users.manage"]["roles"] == ["OWNER", "ADMIN"]
