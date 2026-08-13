"""product research workflow, alerts, source controls and audit log

Revision ID: 0006_product_workflow_alerts
Revises: 0005_analysis_queue_observability
"""
from alembic import op
import sqlalchemy as sa

revision = "0006_product_workflow_alerts"
down_revision = "0005_analysis_queue_observability"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "opportunity_research",
        sa.Column("opportunity_id", sa.Integer(), sa.ForeignKey("opportunities.id"), primary_key=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="NEW"),
        sa.Column("starred", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("tags", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_opportunity_research_status", "opportunity_research", ["status"])
    op.create_index("ix_opportunity_research_starred", "opportunity_research", ["starred"])
    op.create_index("ix_opportunity_research_priority", "opportunity_research", ["priority"])
    op.create_index("ix_opportunity_research_updated_at", "opportunity_research", ["updated_at"])

    op.create_table(
        "alert_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False, unique=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("min_score", sa.Float(), nullable=False, server_default="60"),
        sa.Column("max_risk_score", sa.Float(), nullable=False, server_default="100"),
        sa.Column("min_evidence_count", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("stages", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("keyword_contains", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("cooldown_minutes", sa.Integer(), nullable=False, server_default="1440"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("last_evaluated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_alert_rules_enabled", "alert_rules", ["enabled"])

    op.create_table(
        "alert_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("alert_rule_id", sa.Integer(), sa.ForeignKey("alert_rules.id"), nullable=False),
        sa.Column("opportunity_id", sa.Integer(), sa.ForeignKey("opportunities.id"), nullable=False),
        sa.Column("event_key", sa.String(length=64), nullable=False, unique=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="NEW"),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("message", sa.Text(), nullable=False, server_default=""),
        sa.Column("score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("risk_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_alert_events_alert_rule_id", "alert_events", ["alert_rule_id"])
    op.create_index("ix_alert_events_opportunity_id", "alert_events", ["opportunity_id"])
    op.create_index("ix_alert_events_status", "alert_events", ["status"])
    op.create_index("ix_alert_events_created_at", "alert_events", ["created_at"])
    op.create_index("ix_alert_event_rule_created", "alert_events", ["alert_rule_id", "created_at"])

    op.create_table(
        "source_preferences",
        sa.Column("source_id", sa.String(length=100), primary_key=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("note", sa.Text(), nullable=False, server_default=""),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_source_preferences_enabled", "source_preferences", ["enabled"])

    op.create_table(
        "seed_keywords",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("canonical", sa.String(length=200), nullable=False, unique=True),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_seed_keywords_enabled", "seed_keywords", ["enabled"])
    op.create_index("ix_seed_keywords_priority", "seed_keywords", ["priority"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("actor", sa.String(length=200), nullable=False, server_default="local"),
        sa.Column("action", sa.String(length=30), nullable=False),
        sa.Column("resource", sa.String(length=500), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("detail", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_audit_logs_request_id", "audit_logs", ["request_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_resource", "audit_logs", ["resource"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade():
    op.drop_table("audit_logs")
    op.drop_table("seed_keywords")
    op.drop_table("source_preferences")
    op.drop_table("alert_events")
    op.drop_table("alert_rules")
    op.drop_table("opportunity_research")
