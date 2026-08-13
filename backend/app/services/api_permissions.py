"""Derive API authorization metadata from the live FastAPI dependency graph."""

from __future__ import annotations

from typing import Any

from fastapi.routing import APIRoute

from app.services.permissions import ROLE_LEVEL, VALID_ROLES, required_role_for_scope, role_can

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
AUTH_DEPENDENCY_TO_SCOPE = {
    "require_read_auth": "read",
    "require_write_auth": "write",
    "require_admin_auth": "admin",
}
SCOPE_ORDER = {"public": 0, "read": 1, "write": 2, "admin": 3}


def _dependency_names(dependant: Any) -> list[str]:
    names: list[str] = []
    for dependency in getattr(dependant, "dependencies", ()):
        name = getattr(dependency.call, "__name__", "")
        if name:
            names.append(name)
        names.extend(_dependency_names(dependency))
    return names


def _scope_for_dependencies(names: list[str]) -> str:
    scopes = [AUTH_DEPENDENCY_TO_SCOPE[name] for name in names if name in AUTH_DEPENDENCY_TO_SCOPE]
    return max(scopes, key=lambda scope: SCOPE_ORDER[scope], default="public")


def route_permission_contract(route: APIRoute) -> dict[str, Any]:
    methods = sorted(str(method).upper() for method in (route.methods or ()))
    dependency_names = sorted(set(_dependency_names(route.dependant)))
    scope = _scope_for_dependencies(dependency_names)
    is_mutation = any(method not in SAFE_METHODS for method in methods)
    contract: dict[str, Any] = {
        "methods": methods,
        "path": route.path,
        "operation_id": route.operation_id,
        "route_name": route.name,
        "auth_dependency": next(
            (name for name in ("require_admin_auth", "require_write_auth", "require_read_auth") if name in dependency_names),
            None,
        ),
        "dependency_names": dependency_names,
        "required_scope": scope,
        "minimum_role": None,
        "allowed_roles": ["ANONYMOUS"],
        "csrf_required_for_session": False,
        "interactive_session_required": False,
    }
    if scope != "public":
        minimum_role = required_role_for_scope(scope)
        contract["minimum_role"] = minimum_role
        contract["allowed_roles"] = [role for role in VALID_ROLES if role_can(role, minimum_role)]
        contract["csrf_required_for_session"] = is_mutation and scope in {"write", "admin"}
    if route.path == "/api/v1/auth/tokens" and "POST" in methods:
        contract["interactive_session_required"] = True
    return contract


def api_permission_inventory(app: Any) -> dict[str, Any]:
    routes = [route for route in app.routes if isinstance(route, APIRoute)]
    entries = [route_permission_contract(route) for route in routes]
    entries.sort(key=lambda row: (row["path"], row["methods"]))
    seen: set[tuple[str, str]] = set()
    for entry in entries:
        for method in entry["methods"]:
            key = (method, entry["path"])
            if key in seen:
                raise ValueError(f"duplicate API route: {method} {entry['path']}")
            seen.add(key)
    protected = [entry for entry in entries if entry["required_scope"] != "public"]
    return {
        "inventory_id": "opportunity-radar-api-permission-inventory",
        "inventory_version": "1.0",
        "status": "PASS",
        "source": "FastAPI APIRoute dependency graph",
        "routes": entries,
        "summary": {
            "route_count": len(entries),
            "protected_route_count": len(protected),
            "public_route_count": len(entries) - len(protected),
            "read_route_count": sum(entry["required_scope"] == "read" for entry in entries),
            "write_route_count": sum(entry["required_scope"] == "write" for entry in entries),
            "admin_route_count": sum(entry["required_scope"] == "admin" for entry in entries),
            "real_data_collected": 0,
            "data_policy": "SYNTHETIC_OR_MOCK_ONLY",
        },
    }


def attach_openapi_permissions(app: Any) -> None:
    """Add the same derived contract to every generated OpenAPI operation."""

    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        extra = dict(route.openapi_extra or {})
        extra["x-rbac"] = route_permission_contract(route)
        route.openapi_extra = extra
