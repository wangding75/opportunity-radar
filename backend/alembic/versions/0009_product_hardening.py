"""product hardening: users, sessions, tokens and score history

Revision ID: 0009_product_hardening
Revises: 0008_review_correctness
"""
from alembic import op
import sqlalchemy as sa

revision = "0009_product_hardening"
down_revision = "0008_review_correctness"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("raw_observations", sa.Column("raw_payload_bytes", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("raw_observations", sa.Column("raw_payload_archived_at", sa.DateTime(), nullable=True))
    op.add_column("raw_observations", sa.Column("raw_payload_archive_file", sa.Text(), nullable=True))
    op.add_column("raw_observations", sa.Column("raw_payload_archive_sha256", sa.String(length=64), nullable=True))
    op.create_index("ix_raw_observations_raw_payload_archived_at", "raw_observations", ["raw_payload_archived_at"])

    op.add_column("opportunities", sa.Column("score_version", sa.String(length=40), nullable=False, server_default="score-v1"))
    op.add_column("opportunities", sa.Column("score_breakdown", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
    op.create_index("ix_opportunities_score_version", "opportunities", ["score_version"])

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=500), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False, server_default="VIEWER"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.Column("failed_login_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_enabled", "users", ["enabled"])
    op.create_index("ix_users_locked_until", "users", ["locked_until"])

    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("csrf_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])
    op.create_index("ix_user_sessions_token_hash", "user_sessions", ["token_hash"], unique=True)
    op.create_index("ix_user_sessions_expires_at", "user_sessions", ["expires_at"])
    op.create_index("ix_user_sessions_last_seen_at", "user_sessions", ["last_seen_at"])
    op.create_index("ix_user_sessions_revoked_at", "user_sessions", ["revoked_at"])

    op.create_table(
        "api_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("scopes", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("user_id", "name", name="uq_api_token_user_name"),
    )
    op.create_index("ix_api_tokens_user_id", "api_tokens", ["user_id"])
    op.create_index("ix_api_tokens_token_hash", "api_tokens", ["token_hash"], unique=True)
    op.create_index("ix_api_tokens_expires_at", "api_tokens", ["expires_at"])
    op.create_index("ix_api_tokens_revoked_at", "api_tokens", ["revoked_at"])

    op.create_table(
        "opportunity_score_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("opportunity_id", sa.Integer(), sa.ForeignKey("opportunities.id"), nullable=False),
        sa.Column("model_version", sa.String(length=40), nullable=False),
        sa.Column("input_signature", sa.String(length=64), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("stage", sa.String(length=40), nullable=False),
        sa.Column("evidence_count", sa.Integer(), nullable=False),
        sa.Column("breakdown", sa.JSON(), nullable=False),
        sa.Column("calculated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("opportunity_id", "model_version", "input_signature", name="uq_opportunity_score_snapshot"),
    )
    op.create_index("ix_opportunity_score_snapshots_opportunity_id", "opportunity_score_snapshots", ["opportunity_id"])
    op.create_index("ix_opportunity_score_snapshots_model_version", "opportunity_score_snapshots", ["model_version"])
    op.create_index("ix_opportunity_score_snapshots_input_signature", "opportunity_score_snapshots", ["input_signature"])
    op.create_index("ix_opportunity_score_snapshots_stage", "opportunity_score_snapshots", ["stage"])
    op.create_index("ix_opportunity_score_snapshots_calculated_at", "opportunity_score_snapshots", ["calculated_at"])


def downgrade():
    op.drop_table("opportunity_score_snapshots")
    op.drop_table("api_tokens")
    op.drop_table("user_sessions")
    op.drop_table("users")
    op.drop_index("ix_opportunities_score_version", table_name="opportunities")
    op.drop_index("ix_raw_observations_raw_payload_archived_at", table_name="raw_observations")
    op.drop_column("raw_observations", "raw_payload_archive_sha256")
    op.drop_column("raw_observations", "raw_payload_archive_file")
    op.drop_column("raw_observations", "raw_payload_archived_at")
    op.drop_column("raw_observations", "raw_payload_bytes")
    op.drop_column("opportunities", "score_breakdown")
    op.drop_column("opportunities", "score_version")
