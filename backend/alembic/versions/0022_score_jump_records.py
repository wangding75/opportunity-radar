"""persist score jump detection evaluations"""

from alembic import op
import sqlalchemy as sa


revision = "0022_score_jump_records"
down_revision = "0021_cross_source_alerts"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "score_jump_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("opportunity_id", sa.Integer(), sa.ForeignKey("opportunities.id"), nullable=False),
        sa.Column("input_signature", sa.String(length=64), nullable=False),
        sa.Column("contract_version", sa.String(length=10), nullable=False),
        sa.Column("algorithm_version", sa.String(length=50), nullable=False),
        sa.Column("policy", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("jumped", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("previous_snapshot_signature", sa.String(length=64), nullable=True),
        sa.Column("current_snapshot_signature", sa.String(length=64), nullable=False),
        sa.Column("previous_model_version", sa.String(length=40), nullable=True),
        sa.Column("current_model_version", sa.String(length=40), nullable=False),
        sa.Column("previous_score", sa.Float(), nullable=True),
        sa.Column("current_score", sa.Float(), nullable=False),
        sa.Column("absolute_delta", sa.Float(), nullable=True),
        sa.Column("relative_delta", sa.Float(), nullable=True),
        sa.Column("previous_calculated_at", sa.DateTime(), nullable=True),
        sa.Column("current_calculated_at", sa.DateTime(), nullable=False),
        sa.Column("reasons", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("evaluated_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("input_signature", name="uq_score_jump_input_signature"),
    )
    for name, column in (
        ("opportunity_id", "opportunity_id"),
        ("input_signature", "input_signature"),
        ("status", "status"),
        ("jumped", "jumped"),
        ("previous_snapshot_signature", "previous_snapshot_signature"),
        ("current_snapshot_signature", "current_snapshot_signature"),
        ("evaluated_at", "evaluated_at"),
        ("updated_at", "updated_at"),
    ):
        op.create_index(f"ix_score_jump_records_{name}", "score_jump_records", [column], unique=False)


def downgrade():
    for name in (
        "updated_at",
        "evaluated_at",
        "current_snapshot_signature",
        "previous_snapshot_signature",
        "jumped",
        "status",
        "input_signature",
        "opportunity_id",
    ):
        op.drop_index(f"ix_score_jump_records_{name}", table_name="score_jump_records")
    op.drop_table("score_jump_records")
