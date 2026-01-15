from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ingestion_batches",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("source_date", sa.Date(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("item_count", sa.Integer(), nullable=False),
        sa.Column("query", sa.String(length=255), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.CheckConstraint("item_count >= 0", name="ck_ingestion_batches_item_count_non_negative"),
        sa.UniqueConstraint("id"),
    )
    op.create_index(op.f("ix_ingestion_batches_source_date"), "ingestion_batches", ["source_date"], unique=False)

    op.create_table(
        "papers",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("arxiv_id", sa.String(length=32), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("authors", sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column("categories", sa.ARRAY(sa.String(length=128)), nullable=False),
        sa.Column("submitted_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pdf_url", sa.String(length=512), nullable=True),
        sa.Column("html_url", sa.String(length=512), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("doi", sa.String(length=256), nullable=True),
        sa.Column("primary_category", sa.String(length=128), nullable=True),
        sa.Column("ingestion_batch_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["ingestion_batch_id"], ["ingestion_batches.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("arxiv_id", name="uq_papers_arxiv_id"),
    )
    op.create_index(op.f("ix_papers_arxiv_id"), "papers", ["arxiv_id"], unique=False)

    op.create_table(
        "paper_embeddings",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("paper_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("model_name", sa.String(length=256), nullable=False),
        sa.Column("dimension", sa.Integer(), nullable=False),
        sa.Column("vector", sa.ARRAY(sa.Float()), nullable=False),
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_paper_embeddings_paper_id"), "paper_embeddings", ["paper_id"], unique=False)

    # 创建 PostgreSQL 原生 enum 类型
    from sqlalchemy.dialects.postgresql import ENUM
    feedback_type_enum = ENUM("like", "bookmark", "dislike", name="feedback_type", create_type=True)

    op.create_table(
        "user_feedback",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("paper_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("feedback_type", feedback_type_enum, nullable=False),
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_user_feedback_user_id"), "user_feedback", ["user_id"], unique=False)
    op.create_index(op.f("ix_user_feedback_paper_id"), "user_feedback", ["paper_id"], unique=False)
    op.create_check_constraint("feedback_type_valid", "user_feedback", "feedback_type IN ('like','bookmark','dislike')")
    op.create_unique_constraint(
        "uq_user_feedback_user_paper_type",
        "user_feedback",
        ["user_id", "paper_id", "feedback_type"],
    )

    op.create_table(
        "daily_recommendation_pool",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("pool_date", sa.Date(), nullable=False),
        sa.Column("paper_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_daily_recommendation_pool_pool_date"), "daily_recommendation_pool", ["pool_date"], unique=False)
    op.create_index(op.f("ix_daily_recommendation_pool_paper_id"), "daily_recommendation_pool", ["paper_id"], unique=False)
    op.create_check_constraint("position_non_negative", "daily_recommendation_pool", "position >= 0")
    op.create_check_constraint("score_non_negative", "daily_recommendation_pool", "score >= 0")


def downgrade() -> None:
    op.drop_constraint("score_non_negative", "daily_recommendation_pool", type_="check")
    op.drop_constraint("position_non_negative", "daily_recommendation_pool", type_="check")
    op.drop_index(op.f("ix_daily_recommendation_pool_paper_id"), table_name="daily_recommendation_pool")
    op.drop_index(op.f("ix_daily_recommendation_pool_pool_date"), table_name="daily_recommendation_pool")
    op.drop_table("daily_recommendation_pool")

    op.drop_constraint("uq_user_feedback_user_paper_type", "user_feedback", type_="unique")
    op.drop_constraint("feedback_type_valid", "user_feedback", type_="check")
    op.drop_index(op.f("ix_user_feedback_paper_id"), table_name="user_feedback")
    op.drop_index(op.f("ix_user_feedback_user_id"), table_name="user_feedback")
    op.drop_table("user_feedback")

    op.drop_index(op.f("ix_paper_embeddings_paper_id"), table_name="paper_embeddings")
    op.drop_table("paper_embeddings")

    op.drop_index(op.f("ix_papers_arxiv_id"), table_name="papers")
    op.drop_table("papers")

    op.drop_index(op.f("ix_ingestion_batches_source_date"), table_name="ingestion_batches")
    op.drop_table("ingestion_batches")

    from sqlalchemy.dialects.postgresql import ENUM
    feedback_type_enum = ENUM("like", "bookmark", "dislike", name="feedback_type", create_type=False)
    feedback_type_enum.drop(op.get_bind(), checkfirst=True)
