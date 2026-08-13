import httpx
from app.connectors.github import GitHubSearchConnector
from app.domain.schemas import CollectorQuery


def test_github_connector_parses_official_api_shape():
    def handler(request: httpx.Request):
        assert request.url.path == "/search/repositories"
        return httpx.Response(200, json={"items":[{
            "id":123,"full_name":"demo/ai-short-video","description":"AI short video automation",
            "html_url":"https://github.com/demo/ai-short-video","language":"Python","topics":["ai-video"],
            "stargazers_count":10,"forks_count":2,"created_at":"2026-08-01T00:00:00Z","updated_at":"2026-08-12T00:00:00Z"
        }]})
    client = httpx.Client(transport=httpx.MockTransport(handler))
    connector = GitHubSearchConnector(client=client)
    result = connector.collect(CollectorQuery(query="ai short video", limit=10))
    assert result.source_id == "github"
    assert len(result.records) == 1
    assert result.records[0].payload["topics"] == ["ai-video"]


def test_github_connector_surfaces_rate_limit_retry_window():
    from app.connectors.base import ConnectorRateLimitError

    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(429, headers={"Retry-After": "120"}, json={"message": "rate limited"})
        )
    )
    connector = GitHubSearchConnector(client=client)
    try:
        connector.collect(CollectorQuery(query="ai", limit=1))
    except ConnectorRateLimitError as exc:
        assert exc.retry_after_seconds == 120
    else:
        raise AssertionError("expected rate limit exception")
    client.close()


def test_github_connector_rejects_oversized_response_before_body_parse():
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, headers={"Content-Length": "10000001"}, content=b"{}")
        )
    )
    connector = GitHubSearchConnector(client=client)
    import pytest
    with pytest.raises(ValueError, match="size limit"):
        connector.collect(CollectorQuery(query="ai", limit=1))
    client.close()
