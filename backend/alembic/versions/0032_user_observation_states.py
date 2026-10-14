"""add per-user observation state

Revision ID: 0032_user_observation_states
Revises: 0031_login_rate_limits
"""

from alembic import op
import sqlalchemy as sa


revision = "0032_user_observation_states"
down_revision = "0031_login_rate_limits"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_observation_states",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("observation_id", sa.Integer(), sa.ForeignKey("raw_observations.id"), nullable=False),
        sa.Column("bookmarked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("dismissed_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("user_id", "observation_id", name="uq_user_observation_state"),
    )
    op.create_index("ix_user_observation_states_user_id", "user_observation_states", ["user_id"])
    op.create_index("ix_user_observation_states_observation_id", "user_observation_states", ["observation_id"])
    op.create_index("ix_user_observation_states_bookmarked", "user_observation_states", ["bookmarked"])
    op.create_index("ix_user_observation_states_dismissed_at", "user_observation_states", ["dismissed_at"])
    op.create_index("ix_user_observation_states_updated_at", "user_observation_states", ["updated_at"])


def downgrade():
    op.drop_index("ix_user_observation_states_updated_at", table_name="user_observation_states")
    op.drop_index("ix_user_observation_states_dismissed_at", table_name="user_observation_states")
    op.drop_index("ix_user_observation_states_bookmarked", table_name="user_observation_states")
    op.drop_index("ix_user_observation_states_observation_id", table_name="user_observation_states")
    op.drop_index("ix_user_observation_states_user_id", table_name="user_observation_states")
    op.drop_table("user_observation_states")
