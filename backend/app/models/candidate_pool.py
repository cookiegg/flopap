"""候选池模型"""
from __future__ import annotations

from uuid import UUID, uuid4

import pendulum
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CandidatePool(Base):
    """候选池表 - 存储筛选后的论文ID列表"""
    __tablename__ = "candidate_pools"

    id: Mapped[UUID] = mapped_column(sa.UUID, primary_key=True, default=uuid4)
    batch_id: Mapped[UUID] = mapped_column(sa.UUID, nullable=False)  # 移除外键约束
    paper_id: Mapped[UUID] = mapped_column(sa.UUID, sa.ForeignKey("papers.id"), nullable=False)
    filter_type: Mapped[str] = mapped_column(sa.String(50), nullable=False)  # 'cs', 'ai-ml-cv', 'all' etc.
    created_at: Mapped[pendulum.DateTime] = mapped_column(
        sa.DateTime(timezone=True), 
        nullable=False, 
        default=pendulum.now
    )
    
    # 索引
    __table_args__ = (
        sa.Index("idx_candidate_pool_batch_filter", "batch_id", "filter_type"),
        sa.Index("idx_candidate_pool_paper", "paper_id"),
        sa.UniqueConstraint("batch_id", "paper_id", "filter_type", name="uq_candidate_pool_batch_paper_filter"),
    )
