"""initial tables

Revision ID: 0001_initial
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("raw_observations",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("source_id", sa.String(100), nullable=False),
        sa.Column("external_id", sa.String(300)), sa.Column("query", sa.String(300), nullable=False),
        sa.Column("item_type", sa.String(50), nullable=False), sa.Column("title", sa.Text(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False), sa.Column("source_url", sa.Text()), sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.Column("acquisition_method", sa.String(50), nullable=False), sa.Column("evidence_quality", sa.String(8), nullable=False),
        sa.Column("acquisition_risk", sa.String(8), nullable=False), sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=False), sa.Column("app_package", sa.String(300)), sa.Column("app_version", sa.String(100)),
        sa.Column("emulator_profile", sa.String(200)), sa.Column("instrumentation_version", sa.String(100)), sa.Column("session_id", sa.String(200)))
    op.create_index("ix_raw_source_query_time", "raw_observations", ["source_id", "query", "observed_at"])
    op.create_index("ix_raw_observations_content_hash", "raw_observations", ["content_hash"])
    op.create_table("normalized_items", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("raw_observation_id", sa.Integer(), sa.ForeignKey("raw_observations.id"), nullable=False, unique=True), sa.Column("canonical_key", sa.String(64), nullable=False), sa.Column("source_id", sa.String(100), nullable=False), sa.Column("query", sa.String(300), nullable=False), sa.Column("item_type", sa.String(50), nullable=False), sa.Column("title", sa.Text(), nullable=False), sa.Column("text", sa.Text(), nullable=False), sa.Column("source_url", sa.Text()), sa.Column("observed_at", sa.DateTime(), nullable=False))
    op.create_table("keywords", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("canonical", sa.String(200), unique=True, nullable=False), sa.Column("display_name", sa.String(200), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("first_seen_at", sa.DateTime(), nullable=False), sa.Column("last_seen_at", sa.DateTime(), nullable=False), sa.Column("observation_count", sa.Integer(), nullable=False), sa.Column("source_count", sa.Integer(), nullable=False), sa.Column("score", sa.Float(), nullable=False))
    op.create_table("keyword_mentions", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("keyword_id", sa.Integer(), sa.ForeignKey("keywords.id"), nullable=False), sa.Column("normalized_item_id", sa.Integer(), sa.ForeignKey("normalized_items.id"), nullable=False), sa.Column("source_id", sa.String(100), nullable=False), sa.Column("observed_at", sa.DateTime(), nullable=False), sa.UniqueConstraint("keyword_id", "normalized_item_id", name="uq_keyword_item"))


def downgrade():
    op.drop_table("keyword_mentions")
    op.drop_table("keywords")
    op.drop_table("normalized_items")
    op.drop_index("ix_raw_observations_content_hash", table_name="raw_observations")
    op.drop_index("ix_raw_source_query_time", table_name="raw_observations")
    op.drop_table("raw_observations")
