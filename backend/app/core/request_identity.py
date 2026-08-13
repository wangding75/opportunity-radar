from __future__ import annotations

import hashlib
import ipaddress

from fastapi import Request

from app.core.config import settings


def _peer_ip(request: Request) -> str:
    return ((request.client.host if request.client else None) or "unknown").strip().lower()


def is_trusted_proxy(request: Request) -> bool:
    peer = _peer_ip(request)
    try:
        peer_address = ipaddress.ip_address(peer)
    except ValueError:
        return False
    for network in settings.trusted_proxy_cidrs:
        try:
            if peer_address in ipaddress.ip_network(network, strict=False):
                return True
        except ValueError:
            continue
    return False


def client_ip_from_request(request: Request) -> str:
    """Resolve the source only through an explicitly trusted proxy boundary."""
    if is_trusted_proxy(request):
        forwarded = request.headers.get("X-Forwarded-For", "")
        candidate = forwarded.split(",", 1)[0].strip()
        try:
            return str(ipaddress.ip_address(candidate))
        except ValueError:
            return _peer_ip(request)
    return _peer_ip(request)


def normalized_login_subject(username: str) -> str:
    normalized = username.strip().lower()[:120]
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def audit_actor_from_request(request: Request) -> str:
    principal = getattr(request.state, "principal", None)
    if principal is not None and getattr(principal, "actor", None):
        return str(principal.actor)[:200]
    if settings.audit_trusted_proxy_actor and is_trusted_proxy(request):
        proxy_actor = request.headers.get(settings.audit_actor_header, "")
        proxy_actor = " ".join(proxy_actor.split())[:160]
        if proxy_actor:
            return f"proxy:{proxy_actor}"
    login_subject = getattr(request.state, "login_subject", None)
    if login_subject:
        return f"login:{normalized_login_subject(str(login_subject))}"
    return "anonymous"
