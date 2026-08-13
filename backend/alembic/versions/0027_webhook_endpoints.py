"""persist signed webhook endpoint configuration"""

from alembic import op
import sqlalchemy as sa


revision = "0027_webhook_endpoints"
down_revision = "0026_email_delivery_queue"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "webhook_endpoints",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("secret", sa.Text(), nullable=False),
        sa.Column("secret_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("event_types", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("name", name="uq_webhook_endpoint_name"),
    )
    for name, column in (
        ("name", "name"),
        ("secret_fingerprint", "secret_fingerprint"),
        ("enabled", "enabled"),
        ("updated_at", "updated_at"),
    ):
        op.create_index(f"ix_webhook_endpoints_{name}", "webhook_endpoints", [column], unique=False)


def downgrade():
    for name in ("updated_at", "enabled", "secret_fingerprint", "name"):
        op.drop_index(f"ix_webhook_endpoints_{name}", table_name="webhook_endpoints")
    op.drop_table("webhook_endpoints")
