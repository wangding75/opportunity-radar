"""persist source-independent confirmation decisions"""

from alembic import op
import sqlalchemy as sa


revision = "0020_cross_source_confirmations"
down_revision = "0019_hiring_surge_records"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cross_source_confirmations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("opportunity_id", sa.Integer(), sa.ForeignKey("opportunities.id"), nullable=False),
        sa.Column("subject_key", sa.String(length=300), nullable=False),
        sa.Column("input_signature", sa.String(length=64), nullable=False),
        sa.Column("contract_version", sa.String(length=10), nullable=False),
        sa.Column("algorithm_version", sa.String(length=50), nullable=False),
        sa.Column("policy", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("confirmed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("input_evidence_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fresh_evidence_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deduplicated_evidence_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("stale_evidence_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("future_evidence_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("independent_source_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unique_claim_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_endpoints", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("evidence_ids", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("claim_fingerprints", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("evidence", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("reasons", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("evaluated_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("input_signature", name="uq_cross_source_confirmation_input_signature"),
    )
    op.create_index("ix_cross_source_confirmations_opportunity_id", "cross_source_confirmations", ["opportunity_id"], unique=False)
    op.create_index("ix_cross_source_confirmations_subject_key", "cross_source_confirmations", ["subject_key"], unique=False)
    op.create_index("ix_cross_source_confirmations_input_signature", "cross_source_confirmations", ["input_signature"], unique=False)
    op.create_index("ix_cross_source_confirmations_status", "cross_source_confirmations", ["status"], unique=False)
    op.create_index("ix_cross_source_confirmations_confirmed", "cross_source_confirmations", ["confirmed"], unique=False)
    op.create_index("ix_cross_source_confirmations_evaluated_at", "cross_source_confirmations", ["evaluated_at"], unique=False)
    op.create_index("ix_cross_source_confirmations_updated_at", "cross_source_confirmations", ["updated_at"], unique=False)


def downgrade():
    op.drop_index("ix_cross_source_confirmations_updated_at", table_name="cross_source_confirmations")
    op.drop_index("ix_cross_source_confirmations_evaluated_at", table_name="cross_source_confirmations")
    op.drop_index("ix_cross_source_confirmations_confirmed", table_name="cross_source_confirmations")
    op.drop_index("ix_cross_source_confirmations_status", table_name="cross_source_confirmations")
    op.drop_index("ix_cross_source_confirmations_input_signature", table_name="cross_source_confirmations")
    op.drop_index("ix_cross_source_confirmations_subject_key", table_name="cross_source_confirmations")
    op.drop_index("ix_cross_source_confirmations_opportunity_id", table_name="cross_source_confirmations")
    op.drop_table("cross_source_confirmations")
