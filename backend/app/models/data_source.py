from __future__ import annotations
from sqlalchemy import String, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TimestampMixin
import enum


class DataSourceType(enum.Enum):
    """数据源类型"""
    DAILY = "daily"  # 每日更新数据源 (arxiv, ieee等)
    STATIC = "static"  # 静态导入数据源 (neurips2025, icml2024等)


class DataSource(TimestampMixin, Base):
    """数据源配置"""
    __tablename__ = "data_sources"

    prefix: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    source_type: Mapped[DataSourceType] = mapped_column(Enum(DataSourceType), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
