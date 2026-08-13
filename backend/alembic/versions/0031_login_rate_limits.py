"""add shared login rate-limit counters

Revision ID: 0031_login_rate_limits
Revises: 0030_probe_task_leases
"""

from alembic import op
import sqlalchemy as sa


revision = "0031_login_rate_limits"
down_revision = "0030_probe_task_leases"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "login_rate_limits",
        sa.Column("key", sa.String(length=128), primary_key=True),
        sa.Column("window_started_at", sa.DateTime(), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("blocked_until", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_login_rate_limits_blocked_until", "login_rate_limits", ["blocked_until"])
    op.create_index("ix_login_rate_limits_updated_at", "login_rate_limits", ["updated_at"])


def downgrade():
    op.drop_index("ix_login_rate_limits_updated_at", table_name="login_rate_limits")
    op.drop_index("ix_login_rate_limits_blocked_until", table_name="login_rate_limits")
    op.drop_table("login_rate_limits")
