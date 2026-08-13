"""SSRF and destination policy for outbound Webhook requests."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit

BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "ip6-localhost",
    "metadata",
    "metadata.google.internal",
    "instance-data.ec2.internal",
    "host.docker.internal",
}


class WebhookDestinationPolicyError(ValueError):
    """Raised when an outbound destination violates the SSRF policy."""


def _normalized_hostname(hostname: str) -> str:
    return hostname.strip().rstrip(".").lower()


def is_unsafe_ip(value: str) -> bool:
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return False
    return any(
        (
            address.is_private,
            address.is_loopback,
            address.is_link_local,
            address.is_multicast,
            address.is_reserved,
            address.is_unspecified,
        )
    )


def validate_webhook_url_syntax(url: str) -> str:
    """Validate URL shape and reject obvious local/metadata destinations."""

    if not isinstance(url, str):
        raise WebhookDestinationPolicyError("webhook endpoint URL must be text")
    value = url.strip()
    if "\r" in value or "\n" in value:
        raise WebhookDestinationPolicyError("webhook endpoint URL must not contain CR/LF")
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise WebhookDestinationPolicyError("webhook endpoint URL must be an http(s) URL with a host")
    if parsed.username or parsed.password or parsed.fragment:
        raise WebhookDestinationPolicyError("webhook endpoint URL must not contain credentials or a fragment")
    try:
        parsed.port
    except ValueError as exc:
        raise WebhookDestinationPolicyError("webhook endpoint URL contains an invalid port") from exc
    hostname = _normalized_hostname(parsed.hostname)
    if hostname in BLOCKED_HOSTNAMES or is_unsafe_ip(hostname):
        raise WebhookDestinationPolicyError("webhook endpoint URL must not target a local or reserved address")
    return value


def resolve_webhook_destination(url: str, *, allowed_hosts: tuple[str, ...] = ()) -> tuple[str, ...]:
    """Resolve all destination addresses and reject unsafe DNS answers.

    An explicit host allowlist is intended for controlled Docker/service-mesh
    receivers. It is exact-match only and never accepts a wildcard.
    """

    value = validate_webhook_url_syntax(url)
    parsed = urlsplit(value)
    hostname = _normalized_hostname(parsed.hostname or "")
    normalized_allowlist = {_normalized_hostname(item) for item in allowed_hosts if item.strip()}
    if hostname in normalized_allowlist:
        return (hostname,)
    try:
        infos = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise WebhookDestinationPolicyError("webhook endpoint hostname could not be resolved") from exc
    addresses = tuple(sorted({str(info[4][0]).split("%", 1)[0] for info in infos}))
    if not addresses:
        raise WebhookDestinationPolicyError("webhook endpoint hostname resolved to no addresses")
    unsafe = [address for address in addresses if is_unsafe_ip(address)]
    if unsafe:
        raise WebhookDestinationPolicyError("webhook endpoint hostname resolves to a local or reserved address")
    return addresses
