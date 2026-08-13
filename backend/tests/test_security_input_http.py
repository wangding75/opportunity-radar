from pathlib import Path
import sys

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / "scripts"))
from validate_security_review_input_http import validate_security_review  # noqa: E402

from app.core.http_limits import read_limited_response
from app.services.webhook_security import WebhookDestinationPolicyError, validate_webhook_url_syntax


def test_input_http_security_review_artifact_has_eight_passed_controls():
    result = validate_security_review(Path(__file__).parents[2] / "validation" / "security_review_input_http.json")
    assert result["controls"] == 8
    assert result["status"] == "PASS"


def test_streaming_response_limit_rejects_oversized_body():
    response = httpx.Response(200, content=b"SYNTHETIC-too-large")
    with pytest.raises(ValueError, match="exceeded"):
        read_limited_response(response, max_bytes=4, label="synthetic response")


@pytest.mark.parametrize(
    "url",
    [
        "https://user:password@example.invalid/hook",
        "https://example.invalid/hook#fragment",
        "https://example.invalid/hook\r\nX-Injected: yes",
    ],
)
def test_webhook_destination_rejects_credential_fragment_and_header_injection_urls(url):
    with pytest.raises(WebhookDestinationPolicyError):
        validate_webhook_url_syntax(url)
