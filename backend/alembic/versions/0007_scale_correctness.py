"""scale correctness: stable opportunity lineage, incremental alerts, worker heartbeat

Revision ID: 0007_scale_correctness
Revises: 0006_product_workflow_alerts
"""
from alembic import op
import sqlalchemy as sa

revision = "0007_scale_correctness"
down_revision = "0006_product_workflow_alerts"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("opportunities", sa.Column("cluster_signature", sa.String(length=64), nullable=False, server_default=""))
    op.add_column("opportunities", sa.Column("cluster_generation", sa.Integer(), nullable=False, server_default="0"))
    op.create_index("ix_opportunities_cluster_signature", "opportunities", ["cluster_signature"])

    op.create_table(
        "keyword_relation_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("keyword_a_id", sa.Integer(), sa.ForeignKey("keywords.id"), nullable=False),
        sa.Column("keyword_b_id", sa.Integer(), sa.ForeignKey("keywords.id"), nullable=False),
        sa.Column("source_id", sa.String(length=100), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("keyword_a_id", "keyword_b_id", "source_id", name="uq_keyword_relation_source"),
    )
    op.create_index("ix_keyword_relation_sources_keyword_a_id", "keyword_relation_sources", ["keyword_a_id"])
    op.create_index("ix_keyword_relation_sources_keyword_b_id", "keyword_relation_sources", ["keyword_b_id"])
    op.create_index("ix_keyword_relation_sources_source_id", "keyword_relation_sources", ["source_id"])
    # Backfill relation/source provenance from historic co-occurrences. a<b removes mirrored pairs.
    op.execute(sa.text("""
        INSERT INTO keyword_relation_sources (keyword_a_id, keyword_b_id, source_id, first_seen_at)
        SELECT l.keyword_id, r.keyword_id, l.source_id, MIN(l.observed_at)
        FROM keyword_mentions l
        JOIN keyword_mentions r
          ON r.normalized_item_id = l.normalized_item_id
         AND r.source_id = l.source_id
         AND l.keyword_id < r.keyword_id
        GROUP BY l.keyword_id, r.keyword_id, l.source_id
    """))

    op.create_table(
        "opportunity_cluster_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("opportunity_id", sa.Integer(), sa.ForeignKey("opportunities.id"), nullable=False),
        sa.Column("generation", sa.Integer(), nullable=False),
        sa.Column("cluster_signature", sa.String(length=64), nullable=False),
        sa.Column("keyword_ids", sa.JSON(), nullable=False),
        sa.Column("change_type", sa.String(length=30), nullable=False, server_default="UPDATED"),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("opportunity_id", "generation", name="uq_opportunity_cluster_generation"),
    )
    op.create_index("ix_opportunity_cluster_versions_opportunity_id", "opportunity_cluster_versions", ["opportunity_id"])
    op.create_index("ix_opportunity_cluster_versions_cluster_signature", "opportunity_cluster_versions", ["cluster_signature"])
    op.create_index("ix_opportunity_cluster_versions_change_type", "opportunity_cluster_versions", ["change_type"])
    op.create_index("ix_opportunity_cluster_versions_started_at", "opportunity_cluster_versions", ["started_at"])

    op.create_table(
        "opportunity_lineage",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("parent_opportunity_id", sa.Integer(), sa.ForeignKey("opportunities.id"), nullable=False),
        sa.Column("child_opportunity_id", sa.Integer(), sa.ForeignKey("opportunities.id"), nullable=False),
        sa.Column("relation_type", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("parent_opportunity_id", "child_opportunity_id", "relation_type", name="uq_opportunity_lineage"),
    )
    op.create_index("ix_opportunity_lineage_parent_opportunity_id", "opportunity_lineage", ["parent_opportunity_id"])
    op.create_index("ix_opportunity_lineage_child_opportunity_id", "opportunity_lineage", ["child_opportunity_id"])
    op.create_index("ix_opportunity_lineage_relation_type", "opportunity_lineage", ["relation_type"])
    op.create_index("ix_opportunity_lineage_created_at", "opportunity_lineage", ["created_at"])

    op.create_table(
        "alert_evaluation_queue",
        sa.Column("opportunity_id", sa.Integer(), sa.ForeignKey("opportunities.id"), primary_key=True),
        sa.Column("reason", sa.String(length=100), nullable=False, server_default="OPPORTUNITY_CHANGED"),
        sa.Column("queued_at", sa.DateTime(), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
    )
    op.create_index("ix_alert_evaluation_queue_queued_at", "alert_evaluation_queue", ["queued_at"])

    op.create_table(
        "worker_heartbeats",
        sa.Column("worker_id", sa.String(length=200), primary_key=True),
        sa.Column("mode", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="IDLE"),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.Column("last_success_at", sa.DateTime(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("iteration_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_worker_heartbeats_mode", "worker_heartbeats", ["mode"])
    op.create_index("ix_worker_heartbeats_status", "worker_heartbeats", ["status"])
    op.create_index("ix_worker_heartbeats_last_seen_at", "worker_heartbeats", ["last_seen_at"])

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        op.execute("CREATE INDEX IF NOT EXISTS ix_opportunities_title_trgm ON opportunities USING gin (title gin_trgm_ops)")
        op.execute("CREATE INDEX IF NOT EXISTS ix_opportunities_summary_trgm ON opportunities USING gin (summary gin_trgm_ops)")
        op.execute("CREATE INDEX IF NOT EXISTS ix_raw_observations_title_trgm ON raw_observations USING gin (title gin_trgm_ops)")
        op.execute("CREATE INDEX IF NOT EXISTS ix_raw_observations_text_trgm ON raw_observations USING gin (text gin_trgm_ops)")
        op.execute("CREATE INDEX IF NOT EXISTS ix_raw_observations_query_trgm ON raw_observations USING gin (query gin_trgm_ops)")


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS ix_raw_observations_query_trgm")
        op.execute("DROP INDEX IF EXISTS ix_raw_observations_text_trgm")
        op.execute("DROP INDEX IF EXISTS ix_raw_observations_title_trgm")
        op.execute("DROP INDEX IF EXISTS ix_opportunities_summary_trgm")
        op.execute("DROP INDEX IF EXISTS ix_opportunities_title_trgm")
    op.drop_table("worker_heartbeats")
    op.drop_table("alert_evaluation_queue")
    op.drop_table("opportunity_lineage")
    op.drop_table("opportunity_cluster_versions")
    op.drop_table("keyword_relation_sources")
    op.drop_index("ix_opportunities_cluster_signature", table_name="opportunities")
    op.drop_column("opportunities", "cluster_generation")
    op.drop_column("opportunities", "cluster_signature")
