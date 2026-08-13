"""add scoring and alert linkage to source confirmations"""

from alembic import op
import sqlalchemy as sa


revision = "0021_cross_source_alerts"
down_revision = "0020_cross_source_confirmations"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("cross_source_confirmations", sa.Column("score_contract_version", sa.String(length=10), nullable=False, server_default=""))
    op.add_column("cross_source_confirmations", sa.Column("score_algorithm_version", sa.String(length=50), nullable=False, server_default=""))
    op.add_column("cross_source_confirmations", sa.Column("score_input_signature", sa.String(length=64), nullable=False, server_default=""))
    op.add_column("cross_source_confirmations", sa.Column("score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("cross_source_confirmations", sa.Column("risk_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("cross_source_confirmations", sa.Column("score_breakdown", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
    # SQLite cannot ALTER TABLE with a new foreign-key constraint. Batch mode
    # keeps the migration usable by the repository's SQLite regression path as
    # well as PostgreSQL.
    with op.batch_alter_table("cross_source_confirmations", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("alert_event_id", sa.Integer(), sa.ForeignKey("alert_events.id", name="fk_cross_source_confirmation_alert_event"), nullable=True))
    op.create_index("ix_cross_source_confirmations_score_input_signature", "cross_source_confirmations", ["score_input_signature"], unique=False)
    op.create_index("ix_cross_source_confirmations_alert_event_id", "cross_source_confirmations", ["alert_event_id"], unique=False)
    op.create_index("uq_cross_source_confirmation_alert_event", "cross_source_confirmations", ["alert_event_id"], unique=True)


def downgrade():
    op.drop_index("uq_cross_source_confirmation_alert_event", table_name="cross_source_confirmations")
    op.drop_index("ix_cross_source_confirmations_alert_event_id", table_name="cross_source_confirmations")
    op.drop_index("ix_cross_source_confirmations_score_input_signature", table_name="cross_source_confirmations")
    with op.batch_alter_table("cross_source_confirmations", recreate="always") as batch_op:
        batch_op.drop_column("alert_event_id")
    op.drop_column("cross_source_confirmations", "score_breakdown")
    op.drop_column("cross_source_confirmations", "risk_score")
    op.drop_column("cross_source_confirmations", "score")
    op.drop_column("cross_source_confirmations", "score_input_signature")
    op.drop_column("cross_source_confirmations", "score_algorithm_version")
    op.drop_column("cross_source_confirmations", "score_contract_version")
