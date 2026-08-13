"""persist weekly emerging trend reports with explanations"""

from alembic import op
import sqlalchemy as sa


revision = "0013_weekly_trend_reports"
down_revision = "0012_daily_digests"
branch_labels = None
depends_on = None


def upgrade():
    # Existing installations reached this migration with Alembic's default
    # VARCHAR(32) version column; widen it before recording this revision.
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(100)")
    op.create_table(
        "weekly_trend_reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("week_end", sa.Date(), nullable=False),
        sa.Column("baseline_start", sa.Date(), nullable=False),
        sa.Column("baseline_end", sa.Date(), nullable=False),
        sa.Column("contract_version", sa.String(length=10), nullable=False),
        sa.Column("algorithm_version", sa.String(length=50), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="UTC"),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("selection_policy", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("total_candidates", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("selected_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("input_signature", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("explanation", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("week_start", name="uq_weekly_trend_report_week_start"),
    )
    op.create_index("ix_weekly_trend_reports_week_start", "weekly_trend_reports", ["week_start"], unique=False)
    op.create_index("ix_weekly_trend_reports_generated_at", "weekly_trend_reports", ["generated_at"], unique=False)
    op.create_index("ix_weekly_trend_reports_status", "weekly_trend_reports", ["status"], unique=False)
    op.create_index("ix_weekly_trend_reports_input_signature", "weekly_trend_reports", ["input_signature"], unique=False)
    op.create_index("ix_weekly_trend_reports_updated_at", "weekly_trend_reports", ["updated_at"], unique=False)


def downgrade():
    op.drop_index("ix_weekly_trend_reports_updated_at", table_name="weekly_trend_reports")
    op.drop_index("ix_weekly_trend_reports_input_signature", table_name="weekly_trend_reports")
    op.drop_index("ix_weekly_trend_reports_status", table_name="weekly_trend_reports")
    op.drop_index("ix_weekly_trend_reports_generated_at", table_name="weekly_trend_reports")
    op.drop_index("ix_weekly_trend_reports_week_start", table_name="weekly_trend_reports")
    op.drop_table("weekly_trend_reports")
