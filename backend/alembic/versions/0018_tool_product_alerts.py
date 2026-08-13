"""link first tool/product occurrences to evidence-backed alert events"""

from alembic import op
import sqlalchemy as sa


revision = "0018_tool_product_alerts"
down_revision = "0017_tool_product_occurrences"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("alert_events") as batch:
        batch.add_column(sa.Column("tool_product_entity_id", sa.Integer(), sa.ForeignKey("tool_product_entities.id", name="fk_alert_events_tool_product_entity"), nullable=True))
    op.create_index("ix_alert_events_tool_product_entity_id", "alert_events", ["tool_product_entity_id"], unique=False)
    with op.batch_alter_table("tool_product_occurrences") as batch:
        batch.add_column(sa.Column("alert_event_id", sa.Integer(), sa.ForeignKey("alert_events.id", name="fk_tool_product_occurrences_alert_event"), nullable=True))
    op.create_index("ix_tool_product_occurrences_alert_event_id", "tool_product_occurrences", ["alert_event_id"], unique=True)


def downgrade():
    op.drop_index("ix_tool_product_occurrences_alert_event_id", table_name="tool_product_occurrences")
    with op.batch_alter_table("tool_product_occurrences") as batch:
        batch.drop_column("alert_event_id")
    op.drop_index("ix_alert_events_tool_product_entity_id", table_name="alert_events")
    with op.batch_alter_table("alert_events") as batch:
        batch.drop_column("tool_product_entity_id")
