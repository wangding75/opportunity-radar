"""Bounded, explicitly synthetic risk escalation fixture and acceptance loader."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Keyword, NormalizedItem, Opportunity, OpportunityEvidence, OpportunityScoreSnapshot, RawObservation
from app.services.risk_escalation_alerts import materialize_risk_escalations

DEFAULT_FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "risk_escalation_mock.json"
MOCK_SOURCE_PREFIXES = ("synthetic-", "mock-")


def load_risk_escalation_mock_fixture(path: Path | None = None) -> dict:
    fixture_path = path or DEFAULT_FIXTURE
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("data_class") not in {"MOCK", "SYNTHETIC"}:
        raise ValueError("risk escalation fixture must be explicitly marked MOCK or SYNTHETIC")
    snapshots = payload.get("snapshots")
    evidence = payload.get("evidence")
    if not isinstance(snapshots, list) or len(snapshots) != 2:
        raise ValueError("risk escalation fixture must contain exactly two snapshots")
    if not isinstance(evidence, list) or len(evidence) > 20:
        raise ValueError("risk escalation fixture evidence must contain between 0 and 20 records")
    for record in evidence:
        if not isinstance(record, dict) or not str(record.get("source_id", "")).startswith(MOCK_SOURCE_PREFIXES):
            raise ValueError("risk escalation fixture source IDs must be synthetic-/mock- prefixed")
    return payload


def seed_risk_escalation_mock(db: Session, *, fixture_path: Path | None = None) -> dict:
    """Seed the real snapshot/evidence chain and materialize its alert without committing."""

    fixture = load_risk_escalation_mock_fixture(fixture_path)
    keyword = db.scalar(select(Keyword).where(Keyword.canonical == str(fixture["keyword_canonical"])))
    if keyword is None:
        keyword = Keyword(canonical=str(fixture["keyword_canonical"]), display_name=str(fixture["keyword_display_name"]), status="ACTIVE")
        db.add(keyword)
        db.flush()
    opportunity = db.scalar(select(Opportunity).where(Opportunity.opportunity_key == str(fixture["opportunity_key"])))
    if opportunity is None:
        opportunity = Opportunity(opportunity_key=str(fixture["opportunity_key"]), keyword_id=keyword.id, title=str(fixture["opportunity_title"]), stage="VALIDATED", score=75.0, risk_score=55.0, evidence_count=1)
        db.add(opportunity)
        db.flush()
    imported_snapshots = 0
    duplicate_snapshots = 0
    for payload in fixture["snapshots"]:
        signature = str(payload["input_signature"])
        existing = db.scalar(select(OpportunityScoreSnapshot).where(OpportunityScoreSnapshot.input_signature == signature))
        if existing is not None:
            duplicate_snapshots += 1
            continue
        db.add(OpportunityScoreSnapshot(opportunity_id=opportunity.id, model_version=str(payload["model_version"]), input_signature=signature, score=float(payload["score"]), risk_score=float(payload["risk_score"]), stage=str(payload["stage"]), evidence_count=int(payload.get("evidence_count", 0)), breakdown=dict(payload.get("breakdown") or {}), calculated_at=datetime.fromisoformat(str(payload["calculated_at"]).replace("Z", "+00:00"))))
        imported_snapshots += 1
    db.flush()
    imported_evidence = 0
    duplicate_evidence = 0
    for payload in fixture["evidence"]:
        text = str(payload.get("text", ""))
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        raw = db.scalar(select(RawObservation).where(RawObservation.content_hash == content_hash))
        if raw is not None:
            duplicate_evidence += 1
            continue
        observed_at = datetime.fromisoformat(str(payload["observed_at"]).replace("Z", "+00:00"))
        raw = RawObservation(source_id=str(payload["source_id"]), external_id=str(payload.get("external_id", "")), query=str(payload.get("query", "synthetic risk")), item_type=str(payload.get("item_type", "NEWS")), title=str(payload.get("title", "")), text=text, source_url=payload.get("url"), observed_at=observed_at, acquisition_method="MOCK", evidence_quality="HIGH", acquisition_risk="LOW", content_hash=content_hash, raw_payload={"data_class": fixture["data_class"]})
        db.add(raw)
        db.flush()
        item = NormalizedItem(raw_observation_id=raw.id, canonical_key=content_hash[:64], source_id=raw.source_id, query=raw.query, item_type=raw.item_type, title=raw.title, text=raw.text, source_url=raw.source_url, observed_at=observed_at)
        db.add(item)
        db.flush()
        db.add(OpportunityEvidence(opportunity_id=opportunity.id, normalized_item_id=item.id, evidence_type="RISK", observed_at=observed_at))
        imported_evidence += 1
    db.flush()
    current_at = max(datetime.fromisoformat(str(row["calculated_at"]).replace("Z", "+00:00")) for row in fixture["snapshots"])
    alerts = materialize_risk_escalations(db, opportunity_ids={opportunity.id}, evaluated_at=current_at)
    return {"fixture_name": fixture["fixture_name"], "data_class": fixture["data_class"], "snapshots": len(fixture["snapshots"]), "imported_snapshots": imported_snapshots, "duplicate_snapshots": duplicate_snapshots, "evidence": len(fixture["evidence"]), "imported_evidence": imported_evidence, "duplicate_evidence": duplicate_evidence, "opportunity_id": opportunity.id, "alerts": alerts}
