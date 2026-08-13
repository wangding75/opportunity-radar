"""persist first-seen and duplicate tool/product occurrences"""

from alembic import op
import sqlalchemy as sa


revision = "0017_tool_product_occurrences"
down_revision = "0016_tool_product_entities"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tool_product_occurrences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entity_id", sa.Integer(), sa.ForeignKey("tool_product_entities.id"), nullable=False),
        sa.Column("normalized_item_id", sa.Integer(), sa.ForeignKey("normalized_items.id"), nullable=False),
        sa.Column("occurrence_key", sa.String(length=64), nullable=False),
        sa.Column("classification", sa.String(length=20), nullable=False),
        sa.Column("evidence_id", sa.String(length=68), nullable=False),
        sa.Column("source_id", sa.String(length=100), nullable=False),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.Column("contract_version", sa.String(length=10), nullable=False),
        sa.Column("algorithm_version", sa.String(length=50), nullable=False),
        sa.Column("input_signature", sa.String(length=64), nullable=False),
        sa.Column("detected_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("occurrence_key", name="uq_tool_product_occurrence_key"),
        sa.UniqueConstraint("entity_id", "normalized_item_id", name="uq_tool_product_occurrence_entity_item"),
    )
    op.create_index("ix_tool_product_occurrences_entity_id", "tool_product_occurrences", ["entity_id"], unique=False)
    op.create_index("ix_tool_product_occurrences_normalized_item_id", "tool_product_occurrences", ["normalized_item_id"], unique=False)
    op.create_index("ix_tool_product_occurrences_occurrence_key", "tool_product_occurrences", ["occurrence_key"], unique=False)
    op.create_index("ix_tool_product_occurrences_classification", "tool_product_occurrences", ["classification"], unique=False)
    op.create_index("ix_tool_product_occurrences_evidence_id", "tool_product_occurrences", ["evidence_id"], unique=False)
    op.create_index("ix_tool_product_occurrences_source_id", "tool_product_occurrences", ["source_id"], unique=False)
    op.create_index("ix_tool_product_occurrences_observed_at", "tool_product_occurrences", ["observed_at"], unique=False)
    op.create_index("ix_tool_product_occurrences_input_signature", "tool_product_occurrences", ["input_signature"], unique=False)
    op.create_index("ix_tool_product_occurrences_detected_at", "tool_product_occurrences", ["detected_at"], unique=False)


def downgrade():
    op.drop_index("ix_tool_product_occurrences_detected_at", table_name="tool_product_occurrences")
    op.drop_index("ix_tool_product_occurrences_input_signature", table_name="tool_product_occurrences")
    op.drop_index("ix_tool_product_occurrences_observed_at", table_name="tool_product_occurrences")
    op.drop_index("ix_tool_product_occurrences_source_id", table_name="tool_product_occurrences")
    op.drop_index("ix_tool_product_occurrences_evidence_id", table_name="tool_product_occurrences")
    op.drop_index("ix_tool_product_occurrences_classification", table_name="tool_product_occurrences")
    op.drop_index("ix_tool_product_occurrences_occurrence_key", table_name="tool_product_occurrences")
    op.drop_index("ix_tool_product_occurrences_normalized_item_id", table_name="tool_product_occurrences")
    op.drop_index("ix_tool_product_occurrences_entity_id", table_name="tool_product_occurrences")
    op.drop_table("tool_product_occurrences")
