"""persist graph relation item idempotency keys

Revision ID: 0029_keyword_relation_items
Revises: 0028_webhook_delivery_queue
"""

from alembic import op
import sqlalchemy as sa


revision = "0029_keyword_relation_items"
down_revision = "0028_webhook_delivery_queue"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "keyword_relation_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("keyword_a_id", sa.Integer(), sa.ForeignKey("keywords.id"), nullable=False),
        sa.Column("keyword_b_id", sa.Integer(), sa.ForeignKey("keywords.id"), nullable=False),
        sa.Column("relation_type", sa.String(30), nullable=False),
        sa.Column("normalized_item_id", sa.Integer(), sa.ForeignKey("normalized_items.id"), nullable=False),
        sa.Column("source_id", sa.String(100), nullable=False),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "keyword_a_id", "keyword_b_id", "relation_type", "normalized_item_id",
            name="uq_keyword_relation_item",
        ),
    )
    op.create_index("ix_keyword_relation_items_keyword_a_id", "keyword_relation_items", ["keyword_a_id"])
    op.create_index("ix_keyword_relation_items_keyword_b_id", "keyword_relation_items", ["keyword_b_id"])
    op.create_index("ix_keyword_relation_items_normalized_item_id", "keyword_relation_items", ["normalized_item_id"])
    op.create_index("ix_keyword_relation_items_source_id", "keyword_relation_items", ["source_id"])
    op.create_index("ix_keyword_relation_items_observed_at", "keyword_relation_items", ["observed_at"])
    op.create_index(
        "ix_keyword_relation_item_pair",
        "keyword_relation_items",
        ["keyword_a_id", "keyword_b_id", "relation_type"],
    )
    # Existing relation counters predate item-level idempotency. Mark the
    # already-materialized items that participate in an existing relation so a
    # post-upgrade retry cannot inflate historical counts.
    op.execute(
        sa.text(
            """
            INSERT INTO keyword_relation_items
                (keyword_a_id, keyword_b_id, relation_type, normalized_item_id, source_id, observed_at)
            SELECT DISTINCT
                relation.keyword_a_id, relation.keyword_b_id, relation.relation_type,
                first_mention.normalized_item_id, first_mention.source_id, first_mention.observed_at
            FROM keyword_relations AS relation
            JOIN keyword_mentions AS first_mention
              ON first_mention.keyword_id = relation.keyword_a_id
            JOIN keyword_mentions AS second_mention
              ON second_mention.keyword_id = relation.keyword_b_id
             AND second_mention.normalized_item_id = first_mention.normalized_item_id
            WHERE relation.relation_type = 'CO_OCCURS'
            """
        )
    )


def downgrade():
    op.drop_index("ix_keyword_relation_item_pair", table_name="keyword_relation_items")
    op.drop_index("ix_keyword_relation_items_observed_at", table_name="keyword_relation_items")
    op.drop_index("ix_keyword_relation_items_source_id", table_name="keyword_relation_items")
    op.drop_index("ix_keyword_relation_items_normalized_item_id", table_name="keyword_relation_items")
    op.drop_index("ix_keyword_relation_items_keyword_b_id", table_name="keyword_relation_items")
    op.drop_index("ix_keyword_relation_items_keyword_a_id", table_name="keyword_relation_items")
    op.drop_table("keyword_relation_items")
