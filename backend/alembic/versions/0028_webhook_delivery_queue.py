"""persist idempotent Webhook delivery queue state and retry leases"""

from alembic import op
import sqlalchemy as sa


revision = "0028_webhook_delivery_queue"
down_revision = "0027_webhook_endpoints"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "webhook_delivery_queue",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("alert_event_id", sa.Integer(), sa.ForeignKey("alert_events.id"), nullable=False),
        sa.Column("endpoint_id", sa.Integer(), sa.ForeignKey("webhook_endpoints.id"), nullable=False),
        sa.Column("event_id", sa.String(length=128), nullable=False),
        sa.Column("delivery_id", sa.String(length=128), nullable=False),
        sa.Column("input_signature", sa.String(length=64), nullable=False),
        sa.Column("event_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="QUEUED"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("claim_until", sa.DateTime(), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(), nullable=True),
        sa.Column("request_body", sa.Text(), nullable=True),
        sa.Column("signature_header", sa.Text(), nullable=True),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("provider_message_id", sa.String(length=300), nullable=True),
        sa.Column("failure_kind", sa.String(length=40), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column("last_attempt_at", sa.DateTime(), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("endpoint_id", "alert_event_id", name="uq_webhook_delivery_endpoint_alert"),
        sa.UniqueConstraint("delivery_id", name="uq_webhook_delivery_delivery_id"),
        sa.UniqueConstraint("input_signature", name="uq_webhook_delivery_input_signature"),
    )
    for name, columns in (
        ("alert_event_id", ["alert_event_id"]),
        ("endpoint_id", ["endpoint_id"]),
        ("event_id", ["event_id"]),
        ("delivery_id", ["delivery_id"]),
        ("input_signature", ["input_signature"]),
        ("status", ["status"]),
        ("claim_until", ["claim_until"]),
        ("next_retry_at", ["next_retry_at"]),
        ("created_at", ["created_at"]),
        ("updated_at", ["updated_at"]),
        ("due", ["status", "next_retry_at", "claim_until"]),
    ):
        op.create_index(f"ix_webhook_delivery_queue_{name}", "webhook_delivery_queue", columns, unique=False)


def downgrade():
    for name in ("due", "updated_at", "created_at", "next_retry_at", "claim_until", "status", "input_signature", "delivery_id", "event_id", "endpoint_id", "alert_event_id"):
        op.drop_index(f"ix_webhook_delivery_queue_{name}", table_name="webhook_delivery_queue")
    op.drop_table("webhook_delivery_queue")
