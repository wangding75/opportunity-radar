"""persist alert priority and human ACK lifecycle metadata"""

from alembic import op
import sqlalchemy as sa


revision = "0014_alert_lifecycle"
down_revision = "0013_weekly_trend_reports"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("alert_events", sa.Column("priority", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("alert_events", sa.Column("acknowledged_by", sa.String(length=200), nullable=True))
    op.add_column("alert_events", sa.Column("dismissed_at", sa.DateTime(), nullable=True))
    op.add_column("alert_events", sa.Column("dismissed_by", sa.String(length=200), nullable=True))
    op.add_column("alert_events", sa.Column("resolved_at", sa.DateTime(), nullable=True))
    op.add_column("alert_events", sa.Column("resolved_by", sa.String(length=200), nullable=True))
    op.create_index("ix_alert_events_priority", "alert_events", ["priority"], unique=False)


def downgrade():
    op.drop_index("ix_alert_events_priority", table_name="alert_events")
    op.drop_column("alert_events", "resolved_by")
    op.drop_column("alert_events", "resolved_at")
    op.drop_column("alert_events", "dismissed_by")
    op.drop_column("alert_events", "dismissed_at")
    op.drop_column("alert_events", "acknowledged_by")
    op.drop_column("alert_events", "priority")
