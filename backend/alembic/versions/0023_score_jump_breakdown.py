"""bind score jump reasons to score breakdowns and evidence"""

from alembic import op
import sqlalchemy as sa


revision = "0023_score_jump_breakdown"
down_revision = "0022_score_jump_records"
branch_labels = None
depends_on = None


def upgrade():
    for name, column in (
        ("previous_breakdown", sa.JSON()),
        ("current_breakdown", sa.JSON()),
        ("change_breakdown", sa.JSON()),
        ("evidence_ids", sa.JSON()),
        ("evidence", sa.JSON()),
    ):
        op.add_column("score_jump_records", sa.Column(name, column, nullable=False, server_default=sa.text("'{}'" if name.endswith("breakdown") else "'[]'")))


def downgrade():
    for name in ("evidence", "evidence_ids", "change_breakdown", "current_breakdown", "previous_breakdown"):
        op.drop_column("score_jump_records", name)
