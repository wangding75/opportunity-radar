from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
MOCK_SERVICES = {
    "mock-mail",
    "mock-webhook",
    "mock-enterprise-messaging",
    "mock-analysis",
}


def _compose(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_production_compose_has_no_mock_services_or_mock_dependencies():
    production = _compose(ROOT / "docker-compose.yml")
    services = production["services"]
    assert not MOCK_SERVICES.intersection(services)

    for name, service in services.items():
        assert not any(mock_name in name.lower() for mock_name in MOCK_SERVICES)
        dependencies = service.get("depends_on", {})
        assert not MOCK_SERVICES.intersection(dependencies)
        environment = service.get("environment", {})
        environment_text = "\n".join(
            f"{key}={value}" for key, value in environment.items()
        ) if isinstance(environment, dict) else "\n".join(environment)
        assert "mock-mail" not in environment_text
        assert "mock-webhook" not in environment_text

    assert set(services["api"]["depends_on"]) == {"migrate"}
    assert set(services["worker-alerts"]["depends_on"]) == {"migrate"}


def test_dev_compose_explicitly_restores_mock_services_for_local_integration():
    dev = _compose(ROOT / "docker-compose.dev.yml")
    services = dev["services"]
    assert MOCK_SERVICES.issubset(services)
    assert "mock-mail" in dev["services"]["api"]["depends_on"]
    assert {"mock-mail", "mock-webhook"}.issubset(dev["services"]["worker-alerts"]["depends_on"])


def test_production_api_has_readiness_healthcheck_and_restart_policy():
    production = _compose(ROOT / "docker-compose.yml")
    api = production["services"]["api"]
    assert api["restart"] == "unless-stopped"
    healthcheck = api["healthcheck"]
    assert healthcheck["test"][0] == "CMD"
    assert "127.0.0.1:8000/ready" in healthcheck["test"][-1]
    assert healthcheck["interval"] == "10s"
    assert healthcheck["timeout"] == "5s"
    assert healthcheck["retries"] == 10
    assert healthcheck["start_period"] == "20s"


def test_production_https_proxy_contract_keeps_api_internal():
    production = _compose(ROOT / "docker-compose.yml")
    api = production["services"]["api"]
    proxy = production["services"]["proxy"]
    assert "ports" not in api
    assert api["expose"] == ["8000"]
    assert proxy["image"] == "caddy:2.10-alpine"
    assert proxy["ports"] == ["${HTTP_PORT:-80}:80", "${HTTPS_PORT:-443}:443"]
    assert proxy["depends_on"]["api"]["condition"] == "service_healthy"

    caddyfile = (ROOT / "Caddyfile").read_text(encoding="utf-8")
    assert "{$PUBLIC_DOMAIN}" in caddyfile
    assert "header_up Host" in caddyfile
    assert "header_up X-Forwarded-Proto" in caddyfile
    assert "header_up X-Forwarded-For" in caddyfile
    assert "trusted_proxies" in caddyfile
    documentation = (ROOT / "docs" / "production-https.md").read_text(encoding="utf-8")
    for phrase in ("PUBLIC_DOMAIN", "ACME", "localhost", "8000", "443"):
        assert phrase in documentation
