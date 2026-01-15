"""数据源池设置模型"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DataSourcePoolSettings(Base):
    """数据源池设置 - 每个用户每个数据源独立配置"""
    
    __tablename__ = "data_source_pool_settings"
    
    id: Mapped[UUID] = mapped_column(sa.UUID, primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(sa.String(255), nullable=False, index=True)
    source_key: Mapped[str] = mapped_column(sa.String(100), nullable=False, index=True)
    
    # 推荐池配置 (生成时使用)
    pool_ratio: Mapped[float] = mapped_column(sa.Float, nullable=False, default=0.2)
    max_pool_size: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=2000)
    
    # 显示配置 (查询时使用)
    show_mode: Mapped[str] = mapped_column(sa.String(20), nullable=False, default='pool')  # 'pool' | 'all'
    filter_no_content: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), 
        nullable=False, 
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), 
        nullable=False, 
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    __table_args__ = (
        sa.UniqueConstraint('user_id', 'source_key', name='uq_user_source_pool_settings'),
        sa.CheckConstraint('pool_ratio >= 0.0 AND pool_ratio <= 1.0', name='check_pool_ratio_range'),
        sa.CheckConstraint("show_mode IN ('pool', 'all')", name='check_show_mode'),
    )
