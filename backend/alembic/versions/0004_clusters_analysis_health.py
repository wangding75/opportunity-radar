"""opportunity clusters, structured analysis, and source health

Revision ID: 0004_clusters_analysis_health
Revises: 0003_probe_scheduler_and_runs
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_clusters_analysis_health"
down_revision = "0003_probe_scheduler_and_runs"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("opportunities") as batch:
        batch.add_column(sa.Column("summary", sa.Text(), nullable=False, server_default=""))
        batch.add_column(sa.Column("target_user", sa.Text(), nullable=False, server_default=""))
        batch.add_column(sa.Column("business_model", sa.Text(), nullable=False, server_default=""))
        batch.add_column(sa.Column("monetization", sa.Text(), nullable=False, server_default=""))
        batch.add_column(sa.Column("risk_notes", sa.Text(), nullable=False, server_default=""))
        batch.add_column(sa.Column("analysis_provider", sa.String(80), nullable=False, server_default="heuristic"))
        batch.add_column(sa.Column("analysis_status", sa.String(30), nullable=False, server_default="READY"))
        batch.add_column(sa.Column("analyzed_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("related_keyword_count", sa.Integer(), nullable=False, server_default="1"))
        batch.add_column(sa.Column("analysis_signature", sa.String(64), nullable=False, server_default=""))
        batch.add_column(sa.Column("analysis_error", sa.Text(), nullable=True))

    op.create_table(
        "opportunity_keywords",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("opportunity_id", sa.Integer(), sa.ForeignKey("opportunities.id"), nullable=False),
        sa.Column("keyword_id", sa.Integer(), sa.ForeignKey("keywords.id"), nullable=False),
        sa.Column("role", sa.String(30), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.UniqueConstraint("opportunity_id", "keyword_id", name="uq_opportunity_keyword"),
    )
    op.create_index("ix_opportunity_keywords_opportunity_id", "opportunity_keywords", ["opportunity_id"])
    op.create_index("ix_opportunity_keywords_keyword_id", "opportunity_keywords", ["keyword_id"])

    op.create_table(
        "source_health_states",
        sa.Column("source_id", sa.String(100), primary_key=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False),
        sa.Column("last_success_at", sa.DateTime(), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(), nullable=True),
        sa.Column("circuit_open_until", sa.DateTime(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_source_health_states_status", "source_health_states", ["status"])
    op.create_index("ix_source_health_states_circuit_open_until", "source_health_states", ["circuit_open_until"])

    # Alembic's default version column is VARCHAR(32), but the next existing
    # revision is longer. Expand it before the migration runner writes 0005.
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(100)")


def downgrade():
    op.drop_table("source_health_states")
    op.drop_table("opportunity_keywords")
    with op.batch_alter_table("opportunities") as batch:
        batch.drop_column("analysis_error")
        batch.drop_column("analysis_signature")
        batch.drop_column("related_keyword_count")
        batch.drop_column("analyzed_at")
        batch.drop_column("analysis_status")
        batch.drop_column("analysis_provider")
        batch.drop_column("risk_notes")
        batch.drop_column("monetization")
        batch.drop_column("business_model")
        batch.drop_column("target_user")
        batch.drop_column("summary")
