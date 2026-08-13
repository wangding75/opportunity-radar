from fastapi.testclient import TestClient

from app.mock_analysis_service import app


client = TestClient(app)
EVIDENCE_ID = "ev1_" + "a" * 64


def _request(evidence=None):
    return {
        "schema_version": "1",
        "citation_contract_version": "1",
        "opportunity": {
            "title": "Synthetic opportunity",
            "related_keywords": ["synthetic", "mock"],
            "evidence": evidence if evidence is not None else [{"evidence_id": EVIDENCE_ID, "title": "MOCK input"}],
        },
    }


def test_mock_service_returns_versioned_marked_result_with_bound_citation():
    response = client.post("/v1/analyze", json=_request())
    assert response.status_code == 200
    body = response.json()
    assert body["data_class"] == "MOCK"
    assert body["analysis_version"] == "mock-v1"
    assert len(body["input_signature"]) == 64
    assert body["citations"] == [{"evidence_id": EVIDENCE_ID, "claim": "MOCK synthetic evidence reference: MOCK input"}]


def test_mock_service_rejects_empty_and_invalid_evidence():
    assert client.post("/v1/analyze", json=_request(evidence=[])).status_code == 422
    assert client.post("/v1/analyze", json=_request(evidence=[{"evidence_id": "not-an-evidence-id"}])).status_code == 422


def test_mock_service_deduplicates_evidence_and_exposes_failure_mode():
    response = client.post(
        "/v1/analyze",
        json=_request(evidence=[{"evidence_id": EVIDENCE_ID}, {"evidence_id": EVIDENCE_ID}]),
    )
    assert response.status_code == 200
    assert len(response.json()["citations"]) == 1
    failure = client.post("/v1/analyze", json=_request(), headers={"X-Mock-Failure": "true"})
    assert failure.status_code == 503


def test_mock_health_is_explicitly_synthetic():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "provider": "mock", "data_class": "MOCK", "version": "mock-v1"}
