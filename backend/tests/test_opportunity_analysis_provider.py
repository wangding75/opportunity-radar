from __future__ import annotations

from datetime import datetime

import httpx
import pytest
import json

from app.services.opportunity_analysis import HttpOpportunityAnalyzer, OpportunityAnalysisInput


def _payload():
    return OpportunityAnalysisInput(
        title="AI视频自动化",
        related_keywords=["AI视频自动化", "批量剪辑"],
        stage="PRODUCTIZING",
        score=55.0,
        risk_score=10.0,
        evidence_types={"DEMAND": 1, "SUPPLY": 2},
        evidence=[{"title": "AI视频工具", "text": "自动剪辑", "source": "test", "type": "SUPPLY", "observed_at": datetime(2026, 8, 12, 5, 0, 0)}],
    )


def test_http_analysis_provider_enforces_structured_contract():
    def handler(request: httpx.Request) -> httpx.Response:
        body = request.read().decode()
        assert '"schema_version":"1"' in body.replace(" ", "")
        assert '"citation_contract_version":"1"' in body.replace(" ", "")
        assert '"evidence_id":"ev1_' in body.replace(" ", "")
        assert '"observed_at":"2026-08-12T05:00:00"' in body.replace(" ", "")
        return httpx.Response(
            200,
            json={
                "summary": "结构化摘要",
                "target_user": "内容团队",
                "business_model": "工具订阅",
                "monetization": "订阅费",
                "risk_notes": "需核验平台规则",
                "citations": [{"evidence_id": json.loads(body)["opportunity"]["evidence"][0]["evidence_id"], "claim": "supporting evidence"}],
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = HttpOpportunityAnalyzer("https://analysis.invalid/v1", client=client)
    result = provider.analyze(_payload())
    assert result.provider == "http"
    assert result.business_model == "工具订阅"
    client.close()


def test_http_analysis_provider_rejects_incomplete_response():
    client = httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"summary": "only"})))
    provider = HttpOpportunityAnalyzer("https://analysis.invalid/v1", client=client)
    with pytest.raises(ValueError, match="invalid structured response"):
        provider.analyze(_payload())
    client.close()


def test_http_analysis_provider_rejects_citation_not_in_request():
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200,
                json={
                    "summary": "summary",
                    "target_user": "users",
                    "business_model": "model",
                    "monetization": "fee",
                    "risk_notes": "risk",
                    "citations": [{"evidence_id": "ev1_" + "f" * 64, "claim": "unknown"}],
                },
            )
        )
    )
    provider = HttpOpportunityAnalyzer("https://analysis.invalid/v1", client=client)
    with pytest.raises(ValueError, match="unknown evidence_id"):
        provider.analyze(_payload())
    client.close()


def test_http_analysis_provider_rejects_oversized_response():
    huge = "x" * 5000
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200,
                json={
                    "summary": huge,
                    "target_user": "u",
                    "business_model": "b",
                    "monetization": "m",
                    "risk_notes": "r",
                },
            )
        )
    )
    provider = HttpOpportunityAnalyzer("https://analysis.invalid/v1", max_response_bytes=1000, client=client)
    with pytest.raises(ValueError, match="size limit"):
        provider.analyze(_payload())
    client.close()
