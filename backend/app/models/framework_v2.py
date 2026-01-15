"""Framework V2 数据模型"""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

from app.db.base import Base, TimestampMixin


class ServiceTypeEnum(str, PyEnum):
    """支持的AI服务类型"""
    DASHSCOPE = "dashscope"
    DEEPSEEK = "deepseek"
    GEMINI = "gemini"
    OPENAI = "openai"


class ContentTypeEnum(str, PyEnum):
    """内容生成类型"""
    INFOGRAPHIC = "infographic"
    VISUALIZATION = "visualization"
    TTS = "tts"
    SUMMARY = "summary"
    TRANSLATION = "translation"


class TaskStatusEnum(str, PyEnum):
    """任务状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UserRecommendationSettings(Base):
    """用户推荐配置"""
    __tablename__ = "user_recommendation_settings"

    user_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    arxiv_ratio: Mapped[int] = mapped_column(Integer, default=10, nullable=False)  # 1:N比例，如10表示1:10
    conference_ratio: Mapped[int] = mapped_column(Integer, default=20, nullable=False)  # 1:N比例，如20表示1:20
    enable_auto_generation: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    preferred_models: Mapped[List[str]] = mapped_column(JSONB, default=list, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("arxiv_ratio BETWEEN 1 AND 100", name="check_arxiv_ratio"),
        CheckConstraint("conference_ratio BETWEEN 1 AND 100", name="check_conference_ratio"),
    )


class UserGeneratedContent(TimestampMixin, Base):
    """用户生成内容"""
    __tablename__ = "user_generated_content"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("papers.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    model_used: Mapped[str] = mapped_column(String(100), nullable=False)
    generation_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    is_shared: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    quality_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # 关系
    paper: Mapped["Paper"] = relationship("Paper", viewonly=True)

    __table_args__ = (
        CheckConstraint("content_type IN ('infographic', 'visualization', 'tts', 'summary', 'translation')", name="valid_content_type"),
        CheckConstraint("quality_score IS NULL OR quality_score BETWEEN 0.00 AND 5.00", name="valid_quality_score"),
    )


class AdminPushedContent(TimestampMixin, Base):
    """管理员推送内容"""
    __tablename__ = "admin_pushed_content"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("papers.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False, index=True)
    target_users: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)

    # 关系
    paper: Mapped["Paper"] = relationship("Paper", viewonly=True)

    __table_args__ = (
        CheckConstraint("priority BETWEEN 1 AND 5", name="valid_priority"),
        CheckConstraint("content_type IN ('infographic', 'visualization', 'tts', 'summary', 'translation')", name="valid_admin_content_type"),
    )


class ContentGenerationTask(TimestampMixin, Base):
    """内容生成任务队列"""
    __tablename__ = "content_generation_tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("papers.id", ondelete="CASCADE"), 
        nullable=False
    )
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estimated_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    actual_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # 关系
    paper: Mapped["Paper"] = relationship("Paper", viewonly=True)

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed')", name="valid_task_status"),
        CheckConstraint("progress BETWEEN 0 AND 100", name="valid_progress"),
        CheckConstraint("content_type IN ('infographic', 'visualization', 'tts', 'summary', 'translation')", name="valid_task_content_type"),
    )
