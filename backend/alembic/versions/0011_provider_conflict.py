"""persist multi-provider conflict and selection report

Revision ID: 0011_provider_conflict
Revises: 0010_analysis_citations
"""
from alembic import op
import sqlalchemy as sa


revision = "0011_provider_conflict"
down_revision = "0010_analysis_citations"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "opportunities",
        sa.Column("analysis_conflict", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )


def downgrade():
    op.drop_column("opportunities", "analysis_conflict")
