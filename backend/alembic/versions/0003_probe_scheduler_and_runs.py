"""persistent probe scheduler and collection run history

Revision ID: 0003_probe_scheduler_and_runs
Revises: 0002_signal_opportunity_engine
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_probe_scheduler_and_runs"
down_revision = "0002_signal_opportunity_engine"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "probe_tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.String(100), nullable=False),
        sa.Column("query", sa.String(300), nullable=False),
        sa.Column("intent", sa.String(40), nullable=False),
        sa.Column("keyword_id", sa.Integer(), sa.ForeignKey("keywords.id"), nullable=True),
        sa.Column("priority", sa.Float(), nullable=False),
        sa.Column("interval_minutes", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("next_run_at", sa.DateTime(), nullable=False),
        sa.Column("last_run_at", sa.DateTime(), nullable=True),
        sa.Column("last_status", sa.String(30), nullable=True),
        sa.Column("failure_count", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("source_id", "query", "intent", name="uq_probe_task_source_query_intent"),
    )
    op.create_index("ix_probe_tasks_source_id", "probe_tasks", ["source_id"])
    op.create_index("ix_probe_tasks_query", "probe_tasks", ["query"])
    op.create_index("ix_probe_tasks_intent", "probe_tasks", ["intent"])
    op.create_index("ix_probe_tasks_keyword_id", "probe_tasks", ["keyword_id"])
    op.create_index("ix_probe_tasks_priority", "probe_tasks", ["priority"])
    op.create_index("ix_probe_tasks_active", "probe_tasks", ["active"])
    op.create_index("ix_probe_tasks_next_run_at", "probe_tasks", ["next_run_at"])
    op.create_index("ix_probe_task_due", "probe_tasks", ["active", "next_run_at", "priority"])

    op.create_table(
        "collection_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("probe_task_id", sa.Integer(), sa.ForeignKey("probe_tasks.id"), nullable=True),
        sa.Column("source_id", sa.String(100), nullable=False),
        sa.Column("query", sa.String(300), nullable=False),
        sa.Column("intent", sa.String(40), nullable=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("fetched", sa.Integer(), nullable=False),
        sa.Column("inserted", sa.Integer(), nullable=False),
        sa.Column("duplicates", sa.Integer(), nullable=False),
        sa.Column("normalized", sa.Integer(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
    )
    op.create_index("ix_collection_runs_probe_task_id", "collection_runs", ["probe_task_id"])
    op.create_index("ix_collection_runs_source_id", "collection_runs", ["source_id"])
    op.create_index("ix_collection_runs_query", "collection_runs", ["query"])
    op.create_index("ix_collection_runs_status", "collection_runs", ["status"])
    op.create_index("ix_collection_runs_started_at", "collection_runs", ["started_at"])
    op.create_index("ix_collection_run_source_started", "collection_runs", ["source_id", "started_at"])


def downgrade():
    op.drop_table("collection_runs")
    op.drop_table("probe_tasks")
