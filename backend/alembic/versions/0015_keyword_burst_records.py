"""persist keyword burst evaluations, evidence, and explanations"""

from alembic import op
import sqlalchemy as sa


revision = "0015_keyword_burst_records"
down_revision = "0014_alert_lifecycle"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("alert_events") as batch:
        batch.add_column(sa.Column("keyword_id", sa.Integer(), sa.ForeignKey("keywords.id", name="fk_alert_events_keyword_id_keywords"), nullable=True))
        batch.alter_column("opportunity_id", existing_type=sa.Integer(), nullable=True)
    op.create_index("ix_alert_events_keyword_id", "alert_events", ["keyword_id"], unique=False)
    op.create_table(
        "keyword_burst_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("keyword_id", sa.Integer(), sa.ForeignKey("keywords.id"), nullable=False),
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
        sa.Column("current_observations", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("baseline_observations", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_sources", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("baseline_sources", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("baseline_mean_daily", sa.Float(), nullable=False, server_default="0"),
        sa.Column("baseline_stddev_daily", sa.Float(), nullable=False, server_default="0"),
        sa.Column("current_mean_daily", sa.Float(), nullable=False, server_default="0"),
        sa.Column("growth_rate", sa.Float(), nullable=True),
        sa.Column("absolute_delta", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("z_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("reasons", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("evidence", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("explanation", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("alert_event_id", sa.Integer(), sa.ForeignKey("alert_events.id"), nullable=True),
        sa.Column("evaluated_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("input_signature", name="uq_keyword_burst_input_signature"),
        sa.UniqueConstraint("alert_event_id", name="uq_keyword_burst_alert_event"),
    )
    op.create_index("ix_keyword_burst_records_keyword_id", "keyword_burst_records", ["keyword_id"], unique=False)
    op.create_index("ix_keyword_burst_records_input_signature", "keyword_burst_records", ["input_signature"], unique=False)
    op.create_index("ix_keyword_burst_records_status", "keyword_burst_records", ["status"], unique=False)
    op.create_index("ix_keyword_burst_records_alert_event_id", "keyword_burst_records", ["alert_event_id"], unique=False)
    op.create_index("ix_keyword_burst_records_evaluated_at", "keyword_burst_records", ["evaluated_at"], unique=False)
    op.create_index("ix_keyword_burst_records_updated_at", "keyword_burst_records", ["updated_at"], unique=False)


def downgrade():
    op.drop_index("ix_keyword_burst_records_updated_at", table_name="keyword_burst_records")
    op.drop_index("ix_keyword_burst_records_evaluated_at", table_name="keyword_burst_records")
    op.drop_index("ix_keyword_burst_records_alert_event_id", table_name="keyword_burst_records")
    op.drop_index("ix_keyword_burst_records_status", table_name="keyword_burst_records")
    op.drop_index("ix_keyword_burst_records_input_signature", table_name="keyword_burst_records")
    op.drop_index("ix_keyword_burst_records_keyword_id", table_name="keyword_burst_records")
    op.drop_table("keyword_burst_records")
    op.drop_index("ix_alert_events_keyword_id", table_name="alert_events")
    with op.batch_alter_table("alert_events") as batch:
        batch.drop_column("keyword_id")
        batch.alter_column("opportunity_id", existing_type=sa.Integer(), nullable=False)
