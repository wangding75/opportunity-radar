"""Small Docker-runnable mock for the HTTP analysis provider contract.

The service is deliberately deterministic and labels every generated result as
``MOCK``. It accepts only bounded, already-normalized provider input and never
pretends that an empty evidence set is a successful analysis.
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any

from fastapi import FastAPI, Header, HTTPException

from app.core.time import utc_now
from app.domain.citations import CITATION_CONTRACT_VERSION, validate_evidence_id


app = FastAPI(title="Opportunity Radar Mock Analysis Provider", version="mock-v1")
MOCK_ANALYSIS_VERSION = "mock-v1"


def _input_signature(opportunity: dict[str, Any]) -> str:
    encoded = json.dumps(opportunity, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _synthetic_citations(evidence: list[dict[str, Any]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    citations: list[dict[str, str]] = []
    for row in evidence[:20]:
        evidence_id = validate_evidence_id(row.get("evidence_id", ""))
        if evidence_id in seen:
            continue
        seen.add(evidence_id)
        title = str(row.get("title") or row.get("text") or "synthetic evidence").strip()[:300]
        citations.append({
            "evidence_id": evidence_id,
            "claim": f"MOCK synthetic evidence reference: {title}",
        })
    return citations


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "provider": "mock", "data_class": "MOCK", "version": MOCK_ANALYSIS_VERSION}


@app.post("/v1/analyze")
def analyze(body: dict[str, Any], x_mock_failure: str | None = Header(default=None)) -> dict[str, Any]:
    if x_mock_failure and x_mock_failure.strip().lower() in {"1", "true", "yes"}:
        raise HTTPException(status_code=503, detail="MOCK external provider failure")
    if body.get("schema_version") != "1":
        raise HTTPException(status_code=422, detail="unsupported schema_version")
    if body.get("citation_contract_version") != CITATION_CONTRACT_VERSION:
        raise HTTPException(status_code=422, detail="unsupported citation_contract_version")
    opportunity = body.get("opportunity")
    if not isinstance(opportunity, dict):
        raise HTTPException(status_code=422, detail="opportunity must be an object")
    evidence = opportunity.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        raise HTTPException(status_code=422, detail="MOCK analysis requires at least one evidence item")
    if len(evidence) > 100:
        raise HTTPException(status_code=422, detail="evidence exceeds 100 item limit")
    if any(not isinstance(row, dict) for row in evidence):
        raise HTTPException(status_code=422, detail="evidence items must be objects")
    try:
        citations = _synthetic_citations(evidence)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"invalid evidence contract: {exc}") from exc
    if not citations:
        raise HTTPException(status_code=422, detail="MOCK analysis requires valid evidence IDs")

    title = str(opportunity.get("title") or "untitled opportunity").strip()[:500]
    related_keywords = [str(value).strip() for value in opportunity.get("related_keywords", [])[:6]]
    keyword_text = ", ".join(value for value in related_keywords if value) or "the supplied topic"
    return {
        "summary": f"MOCK analysis for {title}: synthetic signals were received for {keyword_text}.",
        "target_user": "MOCK synthetic users represented by the supplied opportunity payload.",
        "business_model": "MOCK synthetic validation of a tool or service opportunity.",
        "monetization": "MOCK synthetic validation required before any monetization conclusion.",
        "risk_notes": "MOCK data only; validate all conclusions against observed evidence before use.",
        "citations": citations,
        "provider": "mock",
        "data_class": "MOCK",
        "analysis_version": MOCK_ANALYSIS_VERSION,
        "generated_at": utc_now().isoformat(),
        "input_signature": _input_signature(opportunity),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("MOCK_ANALYSIS_PORT", "8080")))
