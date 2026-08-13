"""signal graph, trend and opportunity engine

Revision ID: 0002_signal_opportunity_engine
Revises: 0001_initial
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_signal_opportunity_engine"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    # Query-path indexes missing from the original baseline migration.
    op.drop_index("ix_raw_observations_content_hash", table_name="raw_observations")
    op.create_index("uq_raw_observations_content_hash", "raw_observations", ["content_hash"], unique=True)
    op.create_index("ix_raw_observations_source_id", "raw_observations", ["source_id"])
    op.create_index("ix_raw_observations_query", "raw_observations", ["query"])
    op.create_index("ix_raw_observations_item_type", "raw_observations", ["item_type"])
    op.create_index("ix_raw_observations_observed_at", "raw_observations", ["observed_at"])
    op.create_index("ix_normalized_items_canonical_key", "normalized_items", ["canonical_key"])
    op.create_index("ix_normalized_items_source_id", "normalized_items", ["source_id"])
    op.create_index("ix_normalized_items_query", "normalized_items", ["query"])
    op.create_index("ix_normalized_items_item_type", "normalized_items", ["item_type"])
    op.create_index("ix_normalized_items_observed_at", "normalized_items", ["observed_at"])
    op.create_index("ix_keywords_status", "keywords", ["status"])
    op.create_index("ix_keyword_mentions_keyword_id", "keyword_mentions", ["keyword_id"])
    op.create_index("ix_keyword_mentions_normalized_item_id", "keyword_mentions", ["normalized_item_id"])
    op.create_index("ix_keyword_mentions_source_id", "keyword_mentions", ["source_id"])
    op.create_index("ix_keyword_mentions_observed_at", "keyword_mentions", ["observed_at"])

    op.create_table(
        "keyword_relations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("keyword_a_id", sa.Integer(), sa.ForeignKey("keywords.id"), nullable=False),
        sa.Column("keyword_b_id", sa.Integer(), sa.ForeignKey("keywords.id"), nullable=False),
        sa.Column("relation_type", sa.String(30), nullable=False),
        sa.Column("cooccurrence_count", sa.Integer(), nullable=False),
        sa.Column("source_count", sa.Integer(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.UniqueConstraint("keyword_a_id", "keyword_b_id", "relation_type", name="uq_keyword_relation"),
    )
    op.create_index("ix_keyword_relations_keyword_a_id", "keyword_relations", ["keyword_a_id"])
    op.create_index("ix_keyword_relations_keyword_b_id", "keyword_relations", ["keyword_b_id"])
    op.create_index("ix_keyword_relation_weight", "keyword_relations", ["weight", "last_seen_at"])

    op.create_table(
        "keyword_trend_daily",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("keyword_id", sa.Integer(), sa.ForeignKey("keywords.id"), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("observation_count", sa.Integer(), nullable=False),
        sa.Column("source_count", sa.Integer(), nullable=False),
        sa.UniqueConstraint("keyword_id", "day", name="uq_keyword_trend_day"),
    )
    op.create_index("ix_keyword_trend_daily_keyword_id", "keyword_trend_daily", ["keyword_id"])
    op.create_index("ix_keyword_trend_daily_day", "keyword_trend_daily", ["day"])

    op.create_table(
        "opportunities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("opportunity_key", sa.String(240), nullable=False),
        sa.Column("keyword_id", sa.Integer(), sa.ForeignKey("keywords.id"), nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("stage", sa.String(40), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("demand_score", sa.Float(), nullable=False),
        sa.Column("supply_score", sa.Float(), nullable=False),
        sa.Column("execution_score", sa.Float(), nullable=False),
        sa.Column("cross_source_score", sa.Float(), nullable=False),
        sa.Column("saturation_score", sa.Float(), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("evidence_count", sa.Integer(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("opportunity_key", name="uq_opportunities_opportunity_key"),
    )
    op.create_index("ix_opportunities_keyword_id", "opportunities", ["keyword_id"])
    op.create_index("ix_opportunities_stage", "opportunities", ["stage"])
    op.create_index("ix_opportunities_score", "opportunities", ["score"])

    op.create_table(
        "opportunity_evidence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("opportunity_id", sa.Integer(), sa.ForeignKey("opportunities.id"), nullable=False),
        sa.Column("normalized_item_id", sa.Integer(), sa.ForeignKey("normalized_items.id"), nullable=False),
        sa.Column("evidence_type", sa.String(40), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("opportunity_id", "normalized_item_id", name="uq_opportunity_item"),
    )
    op.create_index("ix_opportunity_evidence_opportunity_id", "opportunity_evidence", ["opportunity_id"])
    op.create_index("ix_opportunity_evidence_normalized_item_id", "opportunity_evidence", ["normalized_item_id"])
    op.create_index("ix_opportunity_evidence_evidence_type", "opportunity_evidence", ["evidence_type"])
    op.create_index("ix_opportunity_evidence_observed_at", "opportunity_evidence", ["observed_at"])


def downgrade():
    op.drop_table("opportunity_evidence")
    op.drop_index("ix_opportunities_score", table_name="opportunities")
    op.drop_index("ix_opportunities_stage", table_name="opportunities")
    op.drop_index("ix_opportunities_keyword_id", table_name="opportunities")
    op.drop_table("opportunities")
    op.drop_table("keyword_trend_daily")
    op.drop_index("ix_keyword_relation_weight", table_name="keyword_relations")
    op.drop_index("ix_keyword_relations_keyword_b_id", table_name="keyword_relations")
    op.drop_index("ix_keyword_relations_keyword_a_id", table_name="keyword_relations")
    op.drop_table("keyword_relations")

    op.drop_index("ix_keyword_mentions_observed_at", table_name="keyword_mentions")
    op.drop_index("ix_keyword_mentions_source_id", table_name="keyword_mentions")
    op.drop_index("ix_keyword_mentions_normalized_item_id", table_name="keyword_mentions")
    op.drop_index("ix_keyword_mentions_keyword_id", table_name="keyword_mentions")
    op.drop_index("ix_keywords_status", table_name="keywords")
    op.drop_index("ix_normalized_items_observed_at", table_name="normalized_items")
    op.drop_index("ix_normalized_items_item_type", table_name="normalized_items")
    op.drop_index("ix_normalized_items_query", table_name="normalized_items")
    op.drop_index("ix_normalized_items_source_id", table_name="normalized_items")
    op.drop_index("ix_normalized_items_canonical_key", table_name="normalized_items")
    op.drop_index("ix_raw_observations_observed_at", table_name="raw_observations")
    op.drop_index("ix_raw_observations_item_type", table_name="raw_observations")
    op.drop_index("ix_raw_observations_query", table_name="raw_observations")
    op.drop_index("ix_raw_observations_source_id", table_name="raw_observations")
    op.drop_index("uq_raw_observations_content_hash", table_name="raw_observations")
    op.create_index("ix_raw_observations_content_hash", "raw_observations", ["content_hash"])
