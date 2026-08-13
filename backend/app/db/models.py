from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utc_now
from .base import Base


class RawObservation(Base):
    __tablename__ = "raw_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[str] = mapped_column(String(100), index=True)
    external_id: Mapped[str | None] = mapped_column(String(300), nullable=True)
    query: Mapped[str] = mapped_column(String(300), index=True)
    item_type: Mapped[str] = mapped_column(String(50), index=True)
    title: Mapped[str] = mapped_column(Text, default="")
    text: Mapped[str] = mapped_column(Text, default="")
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
    acquisition_method: Mapped[str] = mapped_column(String(50))
    evidence_quality: Mapped[str] = mapped_column(String(8))
    acquisition_risk: Mapped[str] = mapped_column(String(8))
    content_hash: Mapped[str] = mapped_column(String(64))
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    app_package: Mapped[str | None] = mapped_column(String(300), nullable=True)
    app_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    emulator_profile: Mapped[str | None] = mapped_column(String(200), nullable=True)
    instrumentation_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    raw_payload_bytes: Mapped[int] = mapped_column(Integer, default=0)
    raw_payload_archived_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    raw_payload_archive_file: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_payload_archive_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)

    normalized_item: Mapped["NormalizedItem | None"] = relationship(back_populates="raw_observation", uselist=False)

    __table_args__ = (
        Index("ix_raw_source_query_time", "source_id", "query", "observed_at"),
        Index("uq_raw_observations_content_hash", "content_hash", unique=True),
    )


class NormalizedItem(Base):
    __tablename__ = "normalized_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    raw_observation_id: Mapped[int] = mapped_column(ForeignKey("raw_observations.id"), unique=True)
    canonical_key: Mapped[str] = mapped_column(String(64), index=True)
    source_id: Mapped[str] = mapped_column(String(100), index=True)
    query: Mapped[str] = mapped_column(String(300), index=True)
    item_type: Mapped[str] = mapped_column(String(50), index=True)
    title: Mapped[str] = mapped_column(Text, default="")
    text: Mapped[str] = mapped_column(Text, default="")
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime, index=True)

    raw_observation: Mapped[RawObservation] = relationship(back_populates="normalized_item")


class Keyword(Base):
    __tablename__ = "keywords"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    canonical: Mapped[str] = mapped_column(String(200), unique=True)
    display_name: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(30), default="DISCOVERED", index=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    observation_count: Mapped[int] = mapped_column(Integer, default=0)
    source_count: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[float] = mapped_column(Float, default=0.0)


class KeywordMention(Base):
    __tablename__ = "keyword_mentions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), index=True)
    normalized_item_id: Mapped[int] = mapped_column(ForeignKey("normalized_items.id"), index=True)
    source_id: Mapped[str] = mapped_column(String(100), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime, index=True)

    __table_args__ = (UniqueConstraint("keyword_id", "normalized_item_id", name="uq_keyword_item"),)


class KeywordRelation(Base):
    __tablename__ = "keyword_relations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keyword_a_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), index=True)
    keyword_b_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), index=True)
    relation_type: Mapped[str] = mapped_column(String(30), default="CO_OCCURS")
    cooccurrence_count: Mapped[int] = mapped_column(Integer, default=1)
    source_count: Mapped[int] = mapped_column(Integer, default=1)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    weight: Mapped[float] = mapped_column(Float, default=0.0)

    __table_args__ = (
        UniqueConstraint("keyword_a_id", "keyword_b_id", "relation_type", name="uq_keyword_relation"),
        Index("ix_keyword_relation_weight", "weight", "last_seen_at"),
    )


class KeywordRelationSource(Base):
    __tablename__ = "keyword_relation_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keyword_a_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), index=True)
    keyword_b_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), index=True)
    source_id: Mapped[str] = mapped_column(String(100), index=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    __table_args__ = (UniqueConstraint("keyword_a_id", "keyword_b_id", "source_id", name="uq_keyword_relation_source"),)


class KeywordRelationItem(Base):
    __tablename__ = "keyword_relation_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keyword_a_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), index=True)
    keyword_b_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), index=True)
    relation_type: Mapped[str] = mapped_column(String(30), default="CO_OCCURS")
    normalized_item_id: Mapped[int] = mapped_column(ForeignKey("normalized_items.id"), index=True)
    source_id: Mapped[str] = mapped_column(String(100), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime, index=True)

    __table_args__ = (
        UniqueConstraint(
            "keyword_a_id", "keyword_b_id", "relation_type", "normalized_item_id",
            name="uq_keyword_relation_item",
        ),
        Index("ix_keyword_relation_item_pair", "keyword_a_id", "keyword_b_id", "relation_type"),
    )


class KeywordTrendDaily(Base):
    __tablename__ = "keyword_trend_daily"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), index=True)
    day: Mapped[date] = mapped_column(Date, index=True)
    observation_count: Mapped[int] = mapped_column(Integer, default=0)
    source_count: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (UniqueConstraint("keyword_id", "day", name="uq_keyword_trend_day"),)


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_key: Mapped[str] = mapped_column(String(240), unique=True)
    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), index=True)
    title: Mapped[str] = mapped_column(String(240))
    stage: Mapped[str] = mapped_column(String(40), index=True)
    score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    demand_score: Mapped[float] = mapped_column(Float, default=0.0)
    supply_score: Mapped[float] = mapped_column(Float, default=0.0)
    execution_score: Mapped[float] = mapped_column(Float, default=0.0)
    cross_source_score: Mapped[float] = mapped_column(Float, default=0.0)
    saturation_score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    summary: Mapped[str] = mapped_column(Text, default="")
    target_user: Mapped[str] = mapped_column(Text, default="")
    business_model: Mapped[str] = mapped_column(Text, default="")
    monetization: Mapped[str] = mapped_column(Text, default="")
    risk_notes: Mapped[str] = mapped_column(Text, default="")
    analysis_provider: Mapped[str] = mapped_column(String(80), default="heuristic")
    analysis_status: Mapped[str] = mapped_column(String(30), default="READY")
    analysis_citations: Mapped[list] = mapped_column(JSON, default=list)
    analysis_conflict: Mapped[dict] = mapped_column(JSON, default=dict)
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    related_keyword_count: Mapped[int] = mapped_column(Integer, default=1)
    analysis_signature: Mapped[str] = mapped_column(String(64), default="")
    analysis_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis_attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    analysis_last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    analysis_next_retry_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    cluster_signature: Mapped[str] = mapped_column(String(64), default="", index=True)
    cluster_generation: Mapped[int] = mapped_column(Integer, default=0)
    score_version: Mapped[str] = mapped_column(String(40), default="score-v1", index=True)
    score_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)


class DailyDigestRecord(Base):
    __tablename__ = "daily_digests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    digest_date: Mapped[date] = mapped_column(Date, unique=True, index=True)
    contract_version: Mapped[str] = mapped_column(String(10))
    algorithm_version: Mapped[str] = mapped_column(String(50))
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    window_start: Mapped[datetime] = mapped_column(DateTime)
    window_end: Mapped[datetime] = mapped_column(DateTime)
    generated_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    status: Mapped[str] = mapped_column(String(20), index=True)
    selection_policy: Mapped[dict] = mapped_column(JSON, default=dict)
    total_candidates: Mapped[int] = mapped_column(Integer, default=0)
    selected_count: Mapped[int] = mapped_column(Integer, default=0)
    input_signature: Mapped[str] = mapped_column(String(64), index=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)


class WeeklyTrendRecord(Base):
    __tablename__ = "weekly_trend_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    week_start: Mapped[date] = mapped_column(Date, unique=True, index=True)
    week_end: Mapped[date] = mapped_column(Date)
    baseline_start: Mapped[date] = mapped_column(Date)
    baseline_end: Mapped[date] = mapped_column(Date)
    contract_version: Mapped[str] = mapped_column(String(10))
    algorithm_version: Mapped[str] = mapped_column(String(50))
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    generated_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    status: Mapped[str] = mapped_column(String(20), index=True)
    selection_policy: Mapped[dict] = mapped_column(JSON, default=dict)
    total_candidates: Mapped[int] = mapped_column(Integer, default=0)
    selected_count: Mapped[int] = mapped_column(Integer, default=0)
    input_signature: Mapped[str] = mapped_column(String(64), index=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    explanation: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)


class KeywordBurstRecord(Base):
    __tablename__ = "keyword_burst_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), index=True)
    input_signature: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    contract_version: Mapped[str] = mapped_column(String(10))
    algorithm_version: Mapped[str] = mapped_column(String(50))
    policy: Mapped[dict] = mapped_column(JSON, default=dict)
    current_start: Mapped[date] = mapped_column(Date)
    current_end: Mapped[date] = mapped_column(Date)
    baseline_start: Mapped[date] = mapped_column(Date)
    baseline_end: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30), index=True)
    comparison: Mapped[str] = mapped_column(String(30))
    current_observations: Mapped[int] = mapped_column(Integer, default=0)
    baseline_observations: Mapped[int] = mapped_column(Integer, default=0)
    current_sources: Mapped[int] = mapped_column(Integer, default=0)
    baseline_sources: Mapped[int] = mapped_column(Integer, default=0)
    baseline_mean_daily: Mapped[float] = mapped_column(Float, default=0.0)
    baseline_stddev_daily: Mapped[float] = mapped_column(Float, default=0.0)
    current_mean_daily: Mapped[float] = mapped_column(Float, default=0.0)
    growth_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    absolute_delta: Mapped[int] = mapped_column(Integer, default=0)
    z_score: Mapped[float] = mapped_column(Float, default=0.0)
    reasons: Mapped[list] = mapped_column(JSON, default=list)
    evidence: Mapped[list] = mapped_column(JSON, default=list)
    explanation: Mapped[dict] = mapped_column(JSON, default=dict)
    alert_event_id: Mapped[int | None] = mapped_column(ForeignKey("alert_events.id"), nullable=True, unique=True, index=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)


class HiringSurgeRecord(Base):
    __tablename__ = "hiring_surge_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), index=True)
    opportunity_id: Mapped[int | None] = mapped_column(ForeignKey("opportunities.id"), nullable=True, index=True)
    detection_signature: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    input_signature: Mapped[str] = mapped_column(String(64), index=True)
    contract_version: Mapped[str] = mapped_column(String(10))
    algorithm_version: Mapped[str] = mapped_column(String(50))
    policy: Mapped[dict] = mapped_column(JSON, default=dict)
    current_start: Mapped[date] = mapped_column(Date)
    current_end: Mapped[date] = mapped_column(Date)
    baseline_start: Mapped[date] = mapped_column(Date)
    baseline_end: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30), index=True)
    comparison: Mapped[str] = mapped_column(String(30))
    surge: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    current_jobs: Mapped[int] = mapped_column(Integer, default=0)
    baseline_jobs: Mapped[int] = mapped_column(Integer, default=0)
    current_sources: Mapped[int] = mapped_column(Integer, default=0)
    baseline_sources: Mapped[int] = mapped_column(Integer, default=0)
    current_evidence: Mapped[int] = mapped_column(Integer, default=0)
    baseline_evidence: Mapped[int] = mapped_column(Integer, default=0)
    growth_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    absolute_delta: Mapped[int] = mapped_column(Integer, default=0)
    z_score: Mapped[float] = mapped_column(Float, default=0.0)
    evidence_ids: Mapped[list] = mapped_column(JSON, default=list)
    evidence: Mapped[list] = mapped_column(JSON, default=list)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    explanation: Mapped[dict] = mapped_column(JSON, default=dict)
    alert_event_id: Mapped[int | None] = mapped_column(ForeignKey("alert_events.id"), nullable=True, unique=True, index=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)


class CrossSourceConfirmationRecord(Base):
    __tablename__ = "cross_source_confirmations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id"), index=True)
    subject_key: Mapped[str] = mapped_column(String(300), index=True)
    input_signature: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    contract_version: Mapped[str] = mapped_column(String(10))
    algorithm_version: Mapped[str] = mapped_column(String(50))
    policy: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30), index=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    input_evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    fresh_evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    deduplicated_evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    stale_evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    future_evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    independent_source_count: Mapped[int] = mapped_column(Integer, default=0)
    unique_claim_count: Mapped[int] = mapped_column(Integer, default=0)
    source_endpoints: Mapped[list] = mapped_column(JSON, default=list)
    evidence_ids: Mapped[list] = mapped_column(JSON, default=list)
    claim_fingerprints: Mapped[list] = mapped_column(JSON, default=list)
    evidence: Mapped[list] = mapped_column(JSON, default=list)
    reasons: Mapped[list] = mapped_column(JSON, default=list)
    score_contract_version: Mapped[str] = mapped_column(String(10), default="")
    score_algorithm_version: Mapped[str] = mapped_column(String(50), default="")
    score_input_signature: Mapped[str] = mapped_column(String(64), default="", index=True)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    score_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    alert_event_id: Mapped[int | None] = mapped_column(ForeignKey("alert_events.id"), nullable=True, unique=True, index=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)


class ToolProductEntity(Base):
    __tablename__ = "tool_product_entities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_key: Mapped[str] = mapped_column(String(68), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(300))
    normalized_name: Mapped[str] = mapped_column(String(300), index=True)
    kind: Mapped[str] = mapped_column(String(20), index=True)
    status: Mapped[str] = mapped_column(String(30), index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    contract_version: Mapped[str] = mapped_column(String(10))
    algorithm_version: Mapped[str] = mapped_column(String(50))
    policy_version: Mapped[str] = mapped_column(String(50))
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    source_count: Mapped[int] = mapped_column(Integer, default=0)
    evidence_ids: Mapped[list] = mapped_column(JSON, default=list)
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    latest_input_signature: Mapped[str] = mapped_column(String(64), index=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)


class ToolProductEntityEvidence(Base):
    __tablename__ = "tool_product_entity_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("tool_product_entities.id"), index=True)
    normalized_item_id: Mapped[int] = mapped_column(ForeignKey("normalized_items.id"), index=True)
    evidence_id: Mapped[str] = mapped_column(String(68), index=True)
    source_id: Mapped[str] = mapped_column(String(100), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    __table_args__ = (
        UniqueConstraint("entity_id", "evidence_id", name="uq_tool_product_entity_evidence_id"),
        UniqueConstraint("entity_id", "normalized_item_id", name="uq_tool_product_entity_item"),
    )


class ToolProductOccurrence(Base):
    __tablename__ = "tool_product_occurrences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("tool_product_entities.id"), index=True)
    normalized_item_id: Mapped[int] = mapped_column(ForeignKey("normalized_items.id"), index=True)
    occurrence_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    classification: Mapped[str] = mapped_column(String(20), index=True)
    evidence_id: Mapped[str] = mapped_column(String(68), index=True)
    source_id: Mapped[str] = mapped_column(String(100), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    contract_version: Mapped[str] = mapped_column(String(10))
    algorithm_version: Mapped[str] = mapped_column(String(50))
    input_signature: Mapped[str] = mapped_column(String(64), index=True)
    alert_event_id: Mapped[int | None] = mapped_column(ForeignKey("alert_events.id"), nullable=True, unique=True, index=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    __table_args__ = (
        UniqueConstraint("entity_id", "normalized_item_id", name="uq_tool_product_occurrence_entity_item"),
    )


class ToolProductNormalizationRun(Base):
    __tablename__ = "tool_product_normalization_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_key: Mapped[str] = mapped_column(String(64), index=True)
    entity_key: Mapped[str | None] = mapped_column(String(68), nullable=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    kind: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30), index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    contract_version: Mapped[str] = mapped_column(String(10))
    algorithm_version: Mapped[str] = mapped_column(String(50))
    policy_version: Mapped[str] = mapped_column(String(50))
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    deduplicated_count: Mapped[int] = mapped_column(Integer, default=0)
    source_count: Mapped[int] = mapped_column(Integer, default=0)
    evidence_ids: Mapped[list] = mapped_column(JSON, default=list)
    reasons: Mapped[list] = mapped_column(JSON, default=list)
    input_signature: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class OpportunityClusterVersion(Base):
    __tablename__ = "opportunity_cluster_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id"), index=True)
    generation: Mapped[int] = mapped_column(Integer)
    cluster_signature: Mapped[str] = mapped_column(String(64), index=True)
    keyword_ids: Mapped[list] = mapped_column(JSON, default=list)
    change_type: Mapped[str] = mapped_column(String(30), default="UPDATED", index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (UniqueConstraint("opportunity_id", "generation", name="uq_opportunity_cluster_generation"),)


class OpportunityLineage(Base):
    __tablename__ = "opportunity_lineage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parent_opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id"), index=True)
    child_opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id"), index=True)
    relation_type: Mapped[str] = mapped_column(String(30), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)

    __table_args__ = (UniqueConstraint("parent_opportunity_id", "child_opportunity_id", "relation_type", name="uq_opportunity_lineage"),)


class OpportunityEvidence(Base):
    __tablename__ = "opportunity_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id"), index=True)
    normalized_item_id: Mapped[int] = mapped_column(ForeignKey("normalized_items.id"), index=True)
    evidence_type: Mapped[str] = mapped_column(String(40), index=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    observed_at: Mapped[datetime] = mapped_column(DateTime, index=True)

    __table_args__ = (
        UniqueConstraint("opportunity_id", "normalized_item_id", name="uq_opportunity_item"),
    )


class OpportunityKeyword(Base):
    __tablename__ = "opportunity_keywords"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id"), index=True)
    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), index=True)
    role: Mapped[str] = mapped_column(String(30), default="RELATED")
    weight: Mapped[float] = mapped_column(Float, default=0.0)

    __table_args__ = (UniqueConstraint("opportunity_id", "keyword_id", name="uq_opportunity_keyword"),)


class SourceHealthState(Base):
    __tablename__ = "source_health_states"

    source_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    status: Mapped[str] = mapped_column(String(30), default="UNKNOWN", index=True)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    circuit_open_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    total_runs: Mapped[int] = mapped_column(Integer, default=0)
    successful_runs: Mapped[int] = mapped_column(Integer, default=0)
    failed_runs: Mapped[int] = mapped_column(Integer, default=0)
    rate_limited_runs: Mapped[int] = mapped_column(Integer, default=0)
    last_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avg_duration_ms: Mapped[float] = mapped_column(Float, default=0.0)
    last_fetched: Mapped[int] = mapped_column(Integer, default=0)
    last_inserted: Mapped[int] = mapped_column(Integer, default=0)


class ProbeTask(Base):
    __tablename__ = "probe_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[str] = mapped_column(String(100), index=True)
    query: Mapped[str] = mapped_column(String(300), index=True)
    intent: Mapped[str] = mapped_column(String(40), index=True)
    keyword_id: Mapped[int | None] = mapped_column(ForeignKey("keywords.id"), nullable=True, index=True)
    priority: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    interval_minutes: Mapped[int] = mapped_column(Integer, default=1440)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    next_run_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
    lease_owner: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    lease_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    __table_args__ = (
        UniqueConstraint("source_id", "query", "intent", name="uq_probe_task_source_query_intent"),
        Index("ix_probe_task_due", "active", "next_run_at", "priority"),
    )


class CollectionRun(Base):
    __tablename__ = "collection_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    probe_task_id: Mapped[int | None] = mapped_column(ForeignKey("probe_tasks.id"), nullable=True, index=True)
    source_id: Mapped[str] = mapped_column(String(100), index=True)
    query: Mapped[str] = mapped_column(String(300), index=True)
    intent: Mapped[str | None] = mapped_column(String(40), nullable=True)
    worker_id: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(30), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    fetched: Mapped[int] = mapped_column(Integer, default=0)
    inserted: Mapped[int] = mapped_column(Integer, default=0)
    duplicates: Mapped[int] = mapped_column(Integer, default=0)
    normalized: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (Index("ix_collection_run_source_started", "source_id", "started_at"),)


class OpportunityResearch(Base):
    __tablename__ = "opportunity_research"

    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id"), primary_key=True)
    status: Mapped[str] = mapped_column(String(30), default="NEW", index=True)
    starred: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=0, index=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    min_score: Mapped[float] = mapped_column(Float, default=60.0)
    max_risk_score: Mapped[float] = mapped_column(Float, default=100.0)
    min_evidence_count: Mapped[int] = mapped_column(Integer, default=2)
    stages: Mapped[list] = mapped_column(JSON, default=list)
    keyword_contains: Mapped[list] = mapped_column(JSON, default=list)
    cooldown_minutes: Mapped[int] = mapped_column(Integer, default=1440)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    last_evaluated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    alert_rule_id: Mapped[int] = mapped_column(ForeignKey("alert_rules.id"), index=True)
    opportunity_id: Mapped[int | None] = mapped_column(ForeignKey("opportunities.id"), nullable=True, index=True)
    keyword_id: Mapped[int | None] = mapped_column(ForeignKey("keywords.id"), nullable=True, index=True)
    tool_product_entity_id: Mapped[int | None] = mapped_column(ForeignKey("tool_product_entities.id"), nullable=True, index=True)
    event_key: Mapped[str] = mapped_column(String(64), unique=True)
    status: Mapped[str] = mapped_column(String(30), default="NEW", index=True)
    priority: Mapped[int] = mapped_column(Integer, default=1, server_default="1", index=True)
    title: Mapped[str] = mapped_column(String(300))
    message: Mapped[str] = mapped_column(Text, default="")
    score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    acknowledged_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    dismissed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    dismissed_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String(200), nullable=True)

    __table_args__ = (
        Index("ix_alert_event_rule_created", "alert_rule_id", "created_at"),
    )


class AlertEvaluationQueue(Base):
    __tablename__ = "alert_evaluation_queue"

    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id"), primary_key=True)
    reason: Mapped[str] = mapped_column(String(100), default="OPPORTUNITY_CHANGED")
    queued_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    revision: Mapped[int] = mapped_column(Integer, default=0)
    claim_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)


class EmailDeliveryRecord(Base):
    """Durable, provider-neutral email delivery queue state."""

    __tablename__ = "email_delivery_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    alert_event_id: Mapped[int] = mapped_column(ForeignKey("alert_events.id"), unique=True, index=True)
    message_id: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    input_signature: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    recipients: Mapped[list] = mapped_column(JSON, default=list)
    template_name: Mapped[str] = mapped_column(String(100))
    template_version: Mapped[str] = mapped_column(String(40))
    request_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30), default="QUEUED", index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    claim_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    provider_message_id: Mapped[str | None] = mapped_column(String(300), nullable=True)
    failure_kind: Mapped[str | None] = mapped_column(String(40), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)

    __table_args__ = (
        Index("ix_email_delivery_queue_due", "status", "next_retry_at", "claim_until"),
    )


class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    url: Mapped[str] = mapped_column(Text)
    secret: Mapped[str] = mapped_column(Text)
    secret_fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    event_types: Mapped[list] = mapped_column(JSON, default=list)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)


class WebhookDeliveryRecord(Base):
    """Durable, provider-neutral Webhook delivery queue state."""

    __tablename__ = "webhook_delivery_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    alert_event_id: Mapped[int] = mapped_column(ForeignKey("alert_events.id"), index=True)
    endpoint_id: Mapped[int] = mapped_column(ForeignKey("webhook_endpoints.id"), index=True)
    event_id: Mapped[str] = mapped_column(String(128), index=True)
    delivery_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    input_signature: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    event_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30), default="QUEUED", index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    claim_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    request_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    signature_header: Mapped[str | None] = mapped_column(Text, nullable=True)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    provider_message_id: Mapped[str | None] = mapped_column(String(300), nullable=True)
    failure_kind: Mapped[str | None] = mapped_column(String(40), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)

    __table_args__ = (
        UniqueConstraint("endpoint_id", "alert_event_id", name="uq_webhook_delivery_endpoint_alert"),
        Index("ix_webhook_delivery_queue_due", "status", "next_retry_at", "claim_until"),
    )


class SourcePreference(Base):
    __tablename__ = "source_preferences"

    source_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    note: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[str] = mapped_column(String(64), index=True)
    actor: Mapped[str] = mapped_column(String(200), default="local")
    action: Mapped[str] = mapped_column(String(30), index=True)
    resource: Mapped[str] = mapped_column(String(500), index=True)
    status_code: Mapped[int] = mapped_column(Integer)
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)


class SeedKeyword(Base):
    __tablename__ = "seed_keywords"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    canonical: Mapped[str] = mapped_column(String(200), unique=True)
    display_name: Mapped[str] = mapped_column(String(200))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=3, index=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class WorkerHeartbeat(Base):
    __tablename__ = "worker_heartbeats"

    worker_id: Mapped[str] = mapped_column(String(200), primary_key=True)
    mode: Mapped[str] = mapped_column(String(30), index=True)
    status: Mapped[str] = mapped_column(String(30), default="IDLE", index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    iteration_count: Mapped[int] = mapped_column(Integer, default=0)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(500))
    role: Mapped[str] = mapped_column(String(30), default="VIEWER", index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)


class LoginRateLimit(Base):
    __tablename__ = "login_rate_limits"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    window_started_at: Mapped[datetime] = mapped_column(DateTime)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    blocked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    csrf_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)


class ApiToken(Base):
    __tablename__ = "api_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    scopes: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)

    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_api_token_user_name"),)


class OpportunityScoreSnapshot(Base):
    __tablename__ = "opportunity_score_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id"), index=True)
    model_version: Mapped[str] = mapped_column(String(40), index=True)
    input_signature: Mapped[str] = mapped_column(String(64), index=True)
    score: Mapped[float] = mapped_column(Float)
    risk_score: Mapped[float] = mapped_column(Float)
    stage: Mapped[str] = mapped_column(String(40), index=True)
    evidence_count: Mapped[int] = mapped_column(Integer)
    breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    calculated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)

    __table_args__ = (
        UniqueConstraint("opportunity_id", "model_version", "input_signature", name="uq_opportunity_score_snapshot"),
    )


class ScoreJumpRecord(Base):
    __tablename__ = "score_jump_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id"), index=True)
    input_signature: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    contract_version: Mapped[str] = mapped_column(String(10))
    algorithm_version: Mapped[str] = mapped_column(String(50))
    policy: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30), index=True)
    jumped: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    previous_snapshot_signature: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    current_snapshot_signature: Mapped[str] = mapped_column(String(64), index=True)
    previous_model_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    current_model_version: Mapped[str] = mapped_column(String(40))
    previous_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_score: Mapped[float] = mapped_column(Float)
    absolute_delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    relative_delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    previous_calculated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    current_calculated_at: Mapped[datetime] = mapped_column(DateTime)
    previous_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    current_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    change_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    evidence_ids: Mapped[list] = mapped_column(JSON, default=list)
    evidence: Mapped[list] = mapped_column(JSON, default=list)
    alert_event_id: Mapped[int | None] = mapped_column(ForeignKey("alert_events.id"), nullable=True, index=True)
    reasons: Mapped[list] = mapped_column(JSON, default=list)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)


class RiskEscalationRecord(Base):
    __tablename__ = "risk_escalation_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id"), index=True)
    input_signature: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    contract_version: Mapped[str] = mapped_column(String(10))
    algorithm_version: Mapped[str] = mapped_column(String(50))
    policy: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30), index=True)
    delivery_status: Mapped[str] = mapped_column(String(30), default="PENDING", index=True)
    escalated: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    previous_risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_risk_score: Mapped[float] = mapped_column(Float)
    absolute_delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    relative_delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    previous_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    current_level: Mapped[str] = mapped_column(String(20))
    previous_model_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    current_model_version: Mapped[str] = mapped_column(String(40))
    previous_calculated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    current_calculated_at: Mapped[datetime] = mapped_column(DateTime)
    previous_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    current_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    change_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    evidence_ids: Mapped[list] = mapped_column(JSON, default=list)
    evidence: Mapped[list] = mapped_column(JSON, default=list)
    reasons: Mapped[list] = mapped_column(JSON, default=list)
    alert_event_id: Mapped[int | None] = mapped_column(ForeignKey("alert_events.id"), nullable=True, index=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
