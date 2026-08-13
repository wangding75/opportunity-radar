"""persist daily opportunity digest snapshots

Revision ID: 0012_daily_digests
Revises: 0011_provider_conflict
"""

from alembic import op
import sqlalchemy as sa


revision = "0012_daily_digests"
down_revision = "0011_provider_conflict"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "daily_digests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("digest_date", sa.Date(), nullable=False),
        sa.Column("contract_version", sa.String(length=10), nullable=False),
        sa.Column("algorithm_version", sa.String(length=50), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="UTC"),
        sa.Column("window_start", sa.DateTime(), nullable=False),
        sa.Column("window_end", sa.DateTime(), nullable=False),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("selection_policy", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("total_candidates", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("selected_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("input_signature", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("digest_date", name="uq_daily_digest_date"),
    )
    op.create_index("ix_daily_digests_digest_date", "daily_digests", ["digest_date"], unique=False)
    op.create_index("ix_daily_digests_generated_at", "daily_digests", ["generated_at"], unique=False)
    op.create_index("ix_daily_digests_status", "daily_digests", ["status"], unique=False)
    op.create_index("ix_daily_digests_input_signature", "daily_digests", ["input_signature"], unique=False)
    op.create_index("ix_daily_digests_updated_at", "daily_digests", ["updated_at"], unique=False)


def downgrade():
    op.drop_index("ix_daily_digests_updated_at", table_name="daily_digests")
    op.drop_index("ix_daily_digests_input_signature", table_name="daily_digests")
    op.drop_index("ix_daily_digests_status", table_name="daily_digests")
    op.drop_index("ix_daily_digests_generated_at", table_name="daily_digests")
    op.drop_index("ix_daily_digests_digest_date", table_name="daily_digests")
    op.drop_table("daily_digests")
