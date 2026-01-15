"""用户论文排序表模型"""
from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

import pendulum
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserPaperRanking(Base):
    """用户论文排序表 - 存储用户个性化的论文排序结果"""
    
    __tablename__ = "user_paper_rankings"
    
    id: Mapped[UUID] = mapped_column(sa.UUID, primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(sa.String(255), nullable=False, index=True)
    pool_date: Mapped[date] = mapped_column(sa.Date, nullable=False, index=True)
    source_key: Mapped[str] = mapped_column(sa.String(100), nullable=False, default='default', index=True)
    
    # 存储排序后的论文ID数组和对应分数数组
    paper_ids: Mapped[list[UUID]] = mapped_column(ARRAY(sa.UUID), nullable=False)
    scores: Mapped[list[float]] = mapped_column(ARRAY(sa.Float), nullable=False)
    
    created_at: Mapped[pendulum.DateTime] = mapped_column(
        sa.DateTime(timezone=True), 
        nullable=False, 
        default=pendulum.now
    )
    updated_at: Mapped[pendulum.DateTime] = mapped_column(
        sa.DateTime(timezone=True), 
        nullable=False, 
        default=pendulum.now,
        onupdate=pendulum.now
    )
    
    # 索引和约束
    __table_args__ = (
        sa.Index("idx_user_ranking_date", "user_id", "pool_date"),
        sa.UniqueConstraint("user_id", "pool_date", "source_key", name="uq_user_ranking_date_source"),
    )
