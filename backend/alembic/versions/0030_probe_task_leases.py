"""persist explicit collection worker leases

Revision ID: 0030_probe_task_leases
Revises: 0029_keyword_relation_items
"""

from alembic import op
import sqlalchemy as sa


revision = "0030_probe_task_leases"
down_revision = "0029_keyword_relation_items"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("probe_tasks", sa.Column("lease_owner", sa.String(length=200), nullable=True))
    op.add_column("probe_tasks", sa.Column("lease_until", sa.DateTime(), nullable=True))
    op.create_index("ix_probe_tasks_lease_owner", "probe_tasks", ["lease_owner"])
    op.create_index("ix_probe_tasks_lease_until", "probe_tasks", ["lease_until"])
    op.add_column("collection_runs", sa.Column("worker_id", sa.String(length=200), nullable=True))
    op.create_index("ix_collection_runs_worker_id", "collection_runs", ["worker_id"])


def downgrade():
    op.drop_index("ix_collection_runs_worker_id", table_name="collection_runs")
    op.drop_column("collection_runs", "worker_id")
    op.drop_index("ix_probe_tasks_lease_until", table_name="probe_tasks")
    op.drop_index("ix_probe_tasks_lease_owner", table_name="probe_tasks")
    op.drop_column("probe_tasks", "lease_until")
    op.drop_column("probe_tasks", "lease_owner")
