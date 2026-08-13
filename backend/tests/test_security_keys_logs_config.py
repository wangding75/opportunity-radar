from pathlib import Path
import json
import logging
import sys

sys.path.insert(0, str(Path(__file__).parents[2] / "scripts"))
from validate_security_review_keys_logs_config import validate_security_review  # noqa: E402

from app.core.observability import JsonFormatter
from app.services.sanitizer import redact_log_text, sanitize_query


def test_keys_logs_config_security_review_artifact_has_eight_passed_controls():
    result = validate_security_review(Path(__file__).parents[2] / "validation" / "security_review_keys_logs_config_container.json")
    assert result["controls"] == 8
    assert result["status"] == "PASS"


def test_audit_query_and_structured_log_redaction_remove_secrets():
    safe_query = sanitize_query("q=synthetic&token=secret-token&email=user%40example.com&page=1")
    assert safe_query == "q=synthetic&page=1"
    redacted = redact_log_text("token=secret password=hunter2 https://user:db-pass@example.invalid/path")
    assert "secret" not in redacted and "hunter2" not in redacted and "db-pass" not in redacted
    record = logging.LogRecord("security", logging.ERROR, __file__, 1, "api_key=secret-key", (), None)
    formatted = json.loads(JsonFormatter().format(record))
    assert "secret-key" not in formatted["message"]


def test_docker_and_compose_secret_boundaries_are_explicit():
    dockerfile = (Path(__file__).parents[2] / "Dockerfile").read_text(encoding="utf-8")
    compose = (Path(__file__).parents[2] / "docker-compose.yml").read_text(encoding="utf-8")
    dockerignore = (Path(__file__).parents[2] / ".dockerignore").read_text(encoding="utf-8")
    assert "USER appuser" in dockerfile and "10001" in dockerfile
    assert "POSTGRES_PASSWORD:?set POSTGRES_PASSWORD" in compose
    assert 'ALLOW_LEGACY_API_KEY: "false"' in compose
    assert ".env" in dockerignore
