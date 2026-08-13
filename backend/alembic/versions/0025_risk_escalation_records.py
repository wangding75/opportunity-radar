"""persist risk escalation explanations, evidence, and delivery state"""

from alembic import op
import sqlalchemy as sa


revision = "0025_risk_escalation_records"
down_revision = "0024_score_jump_alert_event"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "risk_escalation_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("opportunity_id", sa.Integer(), sa.ForeignKey("opportunities.id"), nullable=False),
        sa.Column("input_signature", sa.String(length=64), nullable=False),
        sa.Column("contract_version", sa.String(length=10), nullable=False),
        sa.Column("algorithm_version", sa.String(length=50), nullable=False),
        sa.Column("policy", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("delivery_status", sa.String(length=30), nullable=False, server_default="PENDING"),
        sa.Column("escalated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("previous_risk_score", sa.Float(), nullable=True),
        sa.Column("current_risk_score", sa.Float(), nullable=False),
        sa.Column("absolute_delta", sa.Float(), nullable=True),
        sa.Column("relative_delta", sa.Float(), nullable=True),
        sa.Column("previous_level", sa.String(length=20), nullable=True),
        sa.Column("current_level", sa.String(length=20), nullable=False),
        sa.Column("previous_model_version", sa.String(length=40), nullable=True),
        sa.Column("current_model_version", sa.String(length=40), nullable=False),
        sa.Column("previous_calculated_at", sa.DateTime(), nullable=True),
        sa.Column("current_calculated_at", sa.DateTime(), nullable=False),
        sa.Column("previous_breakdown", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("current_breakdown", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("change_breakdown", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("evidence_ids", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("evidence", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("reasons", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("alert_event_id", sa.Integer(), sa.ForeignKey("alert_events.id"), nullable=True),
        sa.Column("evaluated_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("input_signature", name="uq_risk_escalation_input_signature"),
    )
    for name, column in (
        ("opportunity_id", "opportunity_id"),
        ("input_signature", "input_signature"),
        ("status", "status"),
        ("delivery_status", "delivery_status"),
        ("escalated", "escalated"),
        ("alert_event_id", "alert_event_id"),
        ("evaluated_at", "evaluated_at"),
        ("updated_at", "updated_at"),
    ):
        op.create_index(f"ix_risk_escalation_records_{name}", "risk_escalation_records", [column], unique=False)


def downgrade():
    for name in ("updated_at", "evaluated_at", "alert_event_id", "escalated", "delivery_status", "status", "input_signature", "opportunity_id"):
        op.drop_index(f"ix_risk_escalation_records_{name}", table_name="risk_escalation_records")
    op.drop_table("risk_escalation_records")
