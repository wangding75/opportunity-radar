"""persist evidence-backed hiring surge evaluations and alerts"""

from alembic import op
import sqlalchemy as sa


revision = "0019_hiring_surge_records"
down_revision = "0018_tool_product_alerts"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "hiring_surge_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("keyword_id", sa.Integer(), sa.ForeignKey("keywords.id"), nullable=False),
        sa.Column("opportunity_id", sa.Integer(), sa.ForeignKey("opportunities.id"), nullable=True),
        sa.Column("detection_signature", sa.String(length=64), nullable=False),
        sa.Column("input_signature", sa.String(length=64), nullable=False),
        sa.Column("contract_version", sa.String(length=10), nullable=False),
        sa.Column("algorithm_version", sa.String(length=50), nullable=False),
        sa.Column("policy", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("current_start", sa.Date(), nullable=False),
        sa.Column("current_end", sa.Date(), nullable=False),
        sa.Column("baseline_start", sa.Date(), nullable=False),
        sa.Column("baseline_end", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("comparison", sa.String(length=30), nullable=False),
        sa.Column("surge", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("current_jobs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("baseline_jobs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_sources", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("baseline_sources", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_evidence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("baseline_evidence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("growth_rate", sa.Float(), nullable=True),
        sa.Column("absolute_delta", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("z_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("evidence_ids", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("evidence", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("metrics", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("explanation", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("alert_event_id", sa.Integer(), sa.ForeignKey("alert_events.id"), nullable=True),
        sa.Column("evaluated_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("detection_signature", name="uq_hiring_surge_detection_signature"),
        sa.UniqueConstraint("alert_event_id", name="uq_hiring_surge_alert_event"),
    )
    op.create_index("ix_hiring_surge_records_keyword_id", "hiring_surge_records", ["keyword_id"], unique=False)
    op.create_index("ix_hiring_surge_records_opportunity_id", "hiring_surge_records", ["opportunity_id"], unique=False)
    op.create_index("ix_hiring_surge_records_detection_signature", "hiring_surge_records", ["detection_signature"], unique=False)
    op.create_index("ix_hiring_surge_records_input_signature", "hiring_surge_records", ["input_signature"], unique=False)
    op.create_index("ix_hiring_surge_records_status", "hiring_surge_records", ["status"], unique=False)
    op.create_index("ix_hiring_surge_records_surge", "hiring_surge_records", ["surge"], unique=False)
    op.create_index("ix_hiring_surge_records_alert_event_id", "hiring_surge_records", ["alert_event_id"], unique=False)
    op.create_index("ix_hiring_surge_records_evaluated_at", "hiring_surge_records", ["evaluated_at"], unique=False)
    op.create_index("ix_hiring_surge_records_updated_at", "hiring_surge_records", ["updated_at"], unique=False)


def downgrade():
    op.drop_index("ix_hiring_surge_records_updated_at", table_name="hiring_surge_records")
    op.drop_index("ix_hiring_surge_records_evaluated_at", table_name="hiring_surge_records")
    op.drop_index("ix_hiring_surge_records_alert_event_id", table_name="hiring_surge_records")
    op.drop_index("ix_hiring_surge_records_surge", table_name="hiring_surge_records")
    op.drop_index("ix_hiring_surge_records_status", table_name="hiring_surge_records")
    op.drop_index("ix_hiring_surge_records_input_signature", table_name="hiring_surge_records")
    op.drop_index("ix_hiring_surge_records_detection_signature", table_name="hiring_surge_records")
    op.drop_index("ix_hiring_surge_records_opportunity_id", table_name="hiring_surge_records")
    op.drop_index("ix_hiring_surge_records_keyword_id", table_name="hiring_surge_records")
    op.drop_table("hiring_surge_records")
