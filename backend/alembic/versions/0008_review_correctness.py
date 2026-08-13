"""review correctness and alert queue leasing

Revision ID: 0008_review_correctness
Revises: 0007_scale_correctness
"""
from alembic import op
import sqlalchemy as sa

revision = "0008_review_correctness"
down_revision = "0007_scale_correctness"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "alert_evaluation_queue",
        sa.Column("revision", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "alert_evaluation_queue",
        sa.Column("claim_until", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "alert_evaluation_queue",
        sa.Column("next_retry_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_alert_evaluation_queue_claim_until", "alert_evaluation_queue", ["claim_until"])
    op.create_index("ix_alert_evaluation_queue_next_retry_at", "alert_evaluation_queue", ["next_retry_at"])


def downgrade():
    op.drop_index("ix_alert_evaluation_queue_next_retry_at", table_name="alert_evaluation_queue")
    op.drop_index("ix_alert_evaluation_queue_claim_until", table_name="alert_evaluation_queue")
    op.drop_column("alert_evaluation_queue", "next_retry_at")
    op.drop_column("alert_evaluation_queue", "claim_until")
    op.drop_column("alert_evaluation_queue", "revision")
