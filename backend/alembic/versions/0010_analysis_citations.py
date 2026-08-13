"""persist validated provider analysis citations

Revision ID: 0010_analysis_citations
Revises: 0009_product_hardening
"""
from alembic import op
import sqlalchemy as sa


revision = "0010_analysis_citations"
down_revision = "0009_product_hardening"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "opportunities",
        sa.Column("analysis_citations", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
    )


def downgrade():
    op.drop_column("opportunities", "analysis_citations")
