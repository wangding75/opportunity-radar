from __future__ import annotations

from app.db.models import Opportunity
from app.db.session import SessionLocal
from app.services.analysis_queue import run_pending_opportunity_analysis
from app.services.opportunity_analysis import OpportunityAnalysisResult, OpportunityAnalyzer
from app.services.ingestion import from_import, store_collected
from app.services.analysis import process_new_raw, refresh_derived_analysis
from app.domain.schemas import ImportRecord


class RecordingAnalyzer(OpportunityAnalyzer):
    def __init__(self, fail: bool = False):
        self.fail = fail
        self.payloads = []

    def analyze(self, payload):
        self.payloads.append(payload)
        if self.fail:
            raise RuntimeError("temporary analyzer outage")
        return OpportunityAnalysisResult(
            summary="external summary",
            target_user="operators",
            business_model="subscription",
            monetization="subscription fee",
            risk_notes="verify platform rules",
            provider="test_external",
            citations=[
                {"evidence_id": row["evidence_id"], "claim": "external result cites selected evidence"}
                for row in payload.evidence
            ],
        )


def _seed_opportunity(db):
    records = [
        ImportRecord(
            source_id=source_id,
            query="AI短剧",
            external_id=f"seed-{idx}",
            item_type="PRODUCT" if idx < 2 else "JOB",
            title="AI短剧工具" if idx < 2 else "AI短剧运营招聘",
            text="自动剪辑 " + ("x" * 5000),
        )
        for idx, source_id in enumerate(("analysis_seed_a", "analysis_seed_b", "analysis_seed_c"))
    ]
    for record in records:
        raw, _ = store_collected(
            db,
            source_id=record.source_id,
            query=record.query,
            record=from_import(record),
            acquisition_method=record.acquisition_method,
            evidence_quality=record.evidence_quality,
            acquisition_risk=record.acquisition_risk,
        )
        process_new_raw(db, raw)
    refresh_derived_analysis(db)
    db.commit()
    opp = db.query(Opportunity).filter(Opportunity.stage != "DORMANT").first()
    assert opp is not None
    opp.analysis_status = "PENDING"
    opp.analysis_provider = "heuristic_pending"
    opp.analysis_next_retry_at = None
    db.commit()
    return opp.id


def test_pending_analysis_runs_outside_collection_path_and_applies_result():
    with SessionLocal() as db:
        opportunity_id = _seed_opportunity(db)
        analyzer = RecordingAnalyzer()
        result = run_pending_opportunity_analysis(db, analyzer=analyzer, limit=1)
        assert result["claimed"] == 1
        assert result["executed"] == 1
        assert analyzer.payloads
        assert max(len(row.get("text", "")) for row in analyzer.payloads[0].evidence) <= 2000
        opp = db.get(Opportunity, opportunity_id)
        assert opp.analysis_status == "READY"
        assert opp.analysis_provider == "test_external"
        assert opp.summary == "external summary"
        assert opp.analysis_attempt_count == 1
        assert opp.analysis_next_retry_at is None
        assert opp.analysis_citations


def test_failed_analysis_keeps_heuristic_content_and_schedules_retry():
    with SessionLocal() as db:
        opportunity_id = _seed_opportunity(db)
        before = db.get(Opportunity, opportunity_id).summary
        analyzer = RecordingAnalyzer(fail=True)
        result = run_pending_opportunity_analysis(db, analyzer=analyzer, limit=1)
        assert result["results"][0]["status"] == "DEGRADED"
        opp = db.get(Opportunity, opportunity_id)
        assert opp.analysis_status == "DEGRADED"
        assert opp.summary == before
        assert opp.analysis_error == "temporary analyzer outage"
        assert opp.analysis_next_retry_at is not None


def test_refresh_with_external_provider_marks_pending_without_calling_network(monkeypatch):
    from types import SimpleNamespace
    import app.services.opportunities as opportunities_module

    fake_settings = SimpleNamespace(
        analysis_provider="http",
        analysis_evidence_limit=30,
        analysis_evidence_text_chars=2000,
    )
    monkeypatch.setattr(opportunities_module, "settings", fake_settings)
    with SessionLocal() as db:
        records = [
            ImportRecord(
                source_id=source,
                query="AI工作流",
                external_id=f"external-{idx}",
                item_type="PRODUCT" if idx < 2 else "JOB",
                title="AI工作流工具" if idx < 2 else "AI工作流招聘",
                text="自动化流程",
            )
            for idx, source in enumerate(("ext_a", "ext_b", "ext_c"))
        ]
        for record in records:
            raw, _ = store_collected(
                db,
                source_id=record.source_id,
                query=record.query,
                record=from_import(record),
                acquisition_method=record.acquisition_method,
                evidence_quality=record.evidence_quality,
                acquisition_risk=record.acquisition_risk,
            )
            process_new_raw(db, raw)
        refresh_derived_analysis(db)
        db.commit()
        opp = db.query(Opportunity).filter(Opportunity.stage != "DORMANT").first()
        assert opp is not None
        assert opp.analysis_status == "PENDING"
        assert opp.analysis_provider == "heuristic_pending"
        assert opp.summary
        assert opp.analysis_next_retry_at is not None
