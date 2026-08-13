import socket

import pytest

from app.services.webhook_security import (
    WebhookDestinationPolicyError,
    is_unsafe_ip,
    resolve_webhook_destination,
    validate_webhook_url_syntax,
)


@pytest.mark.parametrize(
    "address",
    ["127.0.0.1", "10.0.0.4", "172.16.0.5", "192.168.1.2", "169.254.169.254", "::1", "ff02::1", "0.0.0.0"],
)
def test_private_loopback_link_local_multicast_and_unspecified_addresses_are_blocked(address):
    assert is_unsafe_ip(address)
    with pytest.raises(WebhookDestinationPolicyError):
        validate_webhook_url_syntax(f"https://[{address}]/hook" if ":" in address else f"https://{address}/hook")


def test_metadata_and_local_hostnames_are_blocked():
    for hostname in ("localhost", "metadata.google.internal", "instance-data.ec2.internal", "host.docker.internal"):
        with pytest.raises(WebhookDestinationPolicyError):
            validate_webhook_url_syntax(f"https://{hostname}/hook")


def test_dns_answers_are_checked_and_exact_allowlist_is_explicit(monkeypatch):
    def unsafe_answers(*args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.168.1.10", 443))]

    monkeypatch.setattr(socket, "getaddrinfo", unsafe_answers)
    with pytest.raises(WebhookDestinationPolicyError, match="resolves"):
        resolve_webhook_destination("https://receiver.synthetic.invalid/hook")
    assert resolve_webhook_destination("https://mock-webhook:8083/hook", allowed_hosts=("mock-webhook",)) == ("mock-webhook",)


def test_dns_failure_is_a_policy_failure(monkeypatch):
    def missing(*args, **kwargs):
        raise socket.gaierror("SYNTHETIC DNS failure")

    monkeypatch.setattr(socket, "getaddrinfo", missing)
    with pytest.raises(WebhookDestinationPolicyError, match="resolved"):
        resolve_webhook_destination("https://receiver.synthetic.invalid/hook")
