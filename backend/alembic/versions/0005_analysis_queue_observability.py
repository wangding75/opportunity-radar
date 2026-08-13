"""external analysis queue and collection observability

Revision ID: 0005_analysis_queue_observability
Revises: 0004_clusters_analysis_health
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_analysis_queue_observability"
down_revision = "0004_clusters_analysis_health"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("opportunities") as batch:
        batch.add_column(sa.Column("analysis_attempt_count", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("analysis_last_attempt_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("analysis_next_retry_at", sa.DateTime(), nullable=True))
        batch.create_index("ix_opportunities_analysis_next_retry_at", ["analysis_next_retry_at"])

    with op.batch_alter_table("source_health_states") as batch:
        batch.add_column(sa.Column("total_runs", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("successful_runs", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("failed_runs", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("rate_limited_runs", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("last_duration_ms", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("avg_duration_ms", sa.Float(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("last_fetched", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("last_inserted", sa.Integer(), nullable=False, server_default="0"))

    with op.batch_alter_table("collection_runs") as batch:
        batch.add_column(sa.Column("duration_ms", sa.Integer(), nullable=True))


def downgrade():
    with op.batch_alter_table("collection_runs") as batch:
        batch.drop_column("duration_ms")

    with op.batch_alter_table("source_health_states") as batch:
        batch.drop_column("last_inserted")
        batch.drop_column("last_fetched")
        batch.drop_column("avg_duration_ms")
        batch.drop_column("last_duration_ms")
        batch.drop_column("rate_limited_runs")
        batch.drop_column("failed_runs")
        batch.drop_column("successful_runs")
        batch.drop_column("total_runs")

    with op.batch_alter_table("opportunities") as batch:
        batch.drop_index("ix_opportunities_analysis_next_retry_at")
        batch.drop_column("analysis_next_retry_at")
        batch.drop_column("analysis_last_attempt_at")
        batch.drop_column("analysis_attempt_count")
