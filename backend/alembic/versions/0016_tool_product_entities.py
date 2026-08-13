"""persist multi-source tool and product entity normalization"""

from alembic import op
import sqlalchemy as sa


revision = "0016_tool_product_entities"
down_revision = "0015_keyword_burst_records"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tool_product_entities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entity_key", sa.String(length=68), nullable=False),
        sa.Column("display_name", sa.String(length=300), nullable=False),
        sa.Column("normalized_name", sa.String(length=300), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("contract_version", sa.String(length=10), nullable=False),
        sa.Column("algorithm_version", sa.String(length=50), nullable=False),
        sa.Column("policy_version", sa.String(length=50), nullable=False),
        sa.Column("evidence_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("evidence_ids", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("first_seen_at", sa.DateTime(), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        sa.Column("latest_input_signature", sa.String(length=64), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("entity_key", name="uq_tool_product_entity_key"),
    )
    op.create_index("ix_tool_product_entities_entity_key", "tool_product_entities", ["entity_key"], unique=False)
    op.create_index("ix_tool_product_entities_normalized_name", "tool_product_entities", ["normalized_name"], unique=False)
    op.create_index("ix_tool_product_entities_kind", "tool_product_entities", ["kind"], unique=False)
    op.create_index("ix_tool_product_entities_status", "tool_product_entities", ["status"], unique=False)
    op.create_index("ix_tool_product_entities_first_seen_at", "tool_product_entities", ["first_seen_at"], unique=False)
    op.create_index("ix_tool_product_entities_last_seen_at", "tool_product_entities", ["last_seen_at"], unique=False)
    op.create_index("ix_tool_product_entities_latest_input_signature", "tool_product_entities", ["latest_input_signature"], unique=False)
    op.create_index("ix_tool_product_entities_evaluated_at", "tool_product_entities", ["evaluated_at"], unique=False)
    op.create_index("ix_tool_product_entities_updated_at", "tool_product_entities", ["updated_at"], unique=False)

    op.create_table(
        "tool_product_entity_evidence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entity_id", sa.Integer(), sa.ForeignKey("tool_product_entities.id"), nullable=False),
        sa.Column("normalized_item_id", sa.Integer(), sa.ForeignKey("normalized_items.id"), nullable=False),
        sa.Column("evidence_id", sa.String(length=68), nullable=False),
        sa.Column("source_id", sa.String(length=100), nullable=False),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("entity_id", "evidence_id", name="uq_tool_product_entity_evidence_id"),
        sa.UniqueConstraint("entity_id", "normalized_item_id", name="uq_tool_product_entity_item"),
    )
    op.create_index("ix_tool_product_entity_evidence_entity_id", "tool_product_entity_evidence", ["entity_id"], unique=False)
    op.create_index("ix_tool_product_entity_evidence_normalized_item_id", "tool_product_entity_evidence", ["normalized_item_id"], unique=False)
    op.create_index("ix_tool_product_entity_evidence_evidence_id", "tool_product_entity_evidence", ["evidence_id"], unique=False)
    op.create_index("ix_tool_product_entity_evidence_source_id", "tool_product_entity_evidence", ["source_id"], unique=False)
    op.create_index("ix_tool_product_entity_evidence_observed_at", "tool_product_entity_evidence", ["observed_at"], unique=False)

    op.create_table(
        "tool_product_normalization_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("candidate_key", sa.String(length=64), nullable=False),
        sa.Column("entity_key", sa.String(length=68), nullable=True),
        sa.Column("display_name", sa.String(length=300), nullable=True),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("contract_version", sa.String(length=10), nullable=False),
        sa.Column("algorithm_version", sa.String(length=50), nullable=False),
        sa.Column("policy_version", sa.String(length=50), nullable=False),
        sa.Column("evidence_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deduplicated_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("evidence_ids", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("reasons", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("input_signature", sa.String(length=64), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("input_signature", name="uq_tool_product_normalization_input_signature"),
    )
    op.create_index("ix_tool_product_normalization_runs_candidate_key", "tool_product_normalization_runs", ["candidate_key"], unique=False)
    op.create_index("ix_tool_product_normalization_runs_entity_key", "tool_product_normalization_runs", ["entity_key"], unique=False)
    op.create_index("ix_tool_product_normalization_runs_status", "tool_product_normalization_runs", ["status"], unique=False)
    op.create_index("ix_tool_product_normalization_runs_input_signature", "tool_product_normalization_runs", ["input_signature"], unique=False)
    op.create_index("ix_tool_product_normalization_runs_evaluated_at", "tool_product_normalization_runs", ["evaluated_at"], unique=False)


def downgrade():
    op.drop_index("ix_tool_product_normalization_runs_evaluated_at", table_name="tool_product_normalization_runs")
    op.drop_index("ix_tool_product_normalization_runs_input_signature", table_name="tool_product_normalization_runs")
    op.drop_index("ix_tool_product_normalization_runs_status", table_name="tool_product_normalization_runs")
    op.drop_index("ix_tool_product_normalization_runs_entity_key", table_name="tool_product_normalization_runs")
    op.drop_index("ix_tool_product_normalization_runs_candidate_key", table_name="tool_product_normalization_runs")
    op.drop_table("tool_product_normalization_runs")
    op.drop_index("ix_tool_product_entity_evidence_observed_at", table_name="tool_product_entity_evidence")
    op.drop_index("ix_tool_product_entity_evidence_source_id", table_name="tool_product_entity_evidence")
    op.drop_index("ix_tool_product_entity_evidence_evidence_id", table_name="tool_product_entity_evidence")
    op.drop_index("ix_tool_product_entity_evidence_normalized_item_id", table_name="tool_product_entity_evidence")
    op.drop_index("ix_tool_product_entity_evidence_entity_id", table_name="tool_product_entity_evidence")
    op.drop_table("tool_product_entity_evidence")
    op.drop_index("ix_tool_product_entities_updated_at", table_name="tool_product_entities")
    op.drop_index("ix_tool_product_entities_evaluated_at", table_name="tool_product_entities")
    op.drop_index("ix_tool_product_entities_latest_input_signature", table_name="tool_product_entities")
    op.drop_index("ix_tool_product_entities_last_seen_at", table_name="tool_product_entities")
    op.drop_index("ix_tool_product_entities_first_seen_at", table_name="tool_product_entities")
    op.drop_index("ix_tool_product_entities_status", table_name="tool_product_entities")
    op.drop_index("ix_tool_product_entities_kind", table_name="tool_product_entities")
    op.drop_index("ix_tool_product_entities_normalized_name", table_name="tool_product_entities")
    op.drop_index("ix_tool_product_entities_entity_key", table_name="tool_product_entities")
    op.drop_table("tool_product_entities")
