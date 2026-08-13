"""link score jump records to accepted alert events"""

from alembic import op
import sqlalchemy as sa


revision = "0024_score_jump_alert_event"
down_revision = "0023_score_jump_breakdown"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("score_jump_records", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("alert_event_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_score_jump_records_alert_event_id", "alert_events", ["alert_event_id"], ["id"])
    op.create_index("ix_score_jump_records_alert_event_id", "score_jump_records", ["alert_event_id"], unique=False)


def downgrade():
    op.drop_index("ix_score_jump_records_alert_event_id", table_name="score_jump_records")
    with op.batch_alter_table("score_jump_records", recreate="always") as batch_op:
        batch_op.drop_column("alert_event_id")
