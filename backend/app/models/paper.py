from __future__ import annotations

import uuid
from datetime import datetime, date
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text, TypeDecorator
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class UserActivity(TimestampMixin, Base):
    __tablename__ = "user_activity"

    user_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    last_open_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_feed_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)


class IngestionBatch(TimestampMixin, Base):
    __tablename__ = "ingestion_batches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    item_count: Mapped[int] = mapped_column(Integer, nullable=False)
    query: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    papers: Mapped[List["Paper"]] = relationship(back_populates="ingestion_batch")


class Paper(TimestampMixin, Base):
    __tablename__ = "papers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    arxiv_id: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    authors: Mapped[List[dict[str, str]]] = mapped_column(JSONB, nullable=False)
    categories: Mapped[List[str]] = mapped_column(ARRAY(String(length=128)), nullable=False)
    submitted_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    pdf_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    html_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    doi: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    primary_category: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default='arxiv', index=True)  # 新增：数据源标识
    ingestion_batch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ingestion_batches.id", ondelete="SET NULL"), nullable=True
    )

    ingestion_batch: Mapped[Optional[IngestionBatch]] = relationship(back_populates="papers")
    embeddings: Mapped[List["PaperEmbedding"]] = relationship(back_populates="paper", cascade="all, delete-orphan")
    translation: Mapped[Optional["PaperTranslation"]] = relationship(back_populates="paper", uselist=False, cascade="all, delete-orphan")
    interpretation: Mapped[Optional["PaperInterpretation"]] = relationship(back_populates="paper", uselist=False, cascade="all, delete-orphan")
    infographic: Mapped[Optional["PaperInfographic"]] = relationship(back_populates="paper", uselist=False, cascade="all, delete-orphan")


class PaperEmbedding(TimestampMixin, Base):
    __tablename__ = "paper_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), index=True)
    model_name: Mapped[str] = mapped_column(String(256), nullable=False)
    dimension: Mapped[int] = mapped_column(Integer, nullable=False)
    vector: Mapped[List[float]] = mapped_column(ARRAY(Float), nullable=False)

    paper: Mapped[Paper] = relationship(back_populates="embeddings")


class FeedbackTypeEnum(str, PyEnum):  # type: ignore[misc]
    LIKE = "like"
    BOOKMARK = "bookmark"
    DISLIKE = "dislike"


class FeedbackTypeEnumType(TypeDecorator):
    """自定义 Enum 类型，确保使用值（小写）而不是名称（大写）进行序列化"""
    from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
    impl = PG_ENUM("like", "bookmark", "dislike", name="feedback_type", create_type=False)
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        """返回数据库方言特定的实现"""
        if dialect.name == 'postgresql':
            return self.impl
        # 对于非 PostgreSQL 数据库，使用 String
        from sqlalchemy import String
        return String(16)

    def process_bind_param(self, value, dialect):
        """将 Python Enum 转换为数据库值 - 必须在参数绑定前调用"""
        if value is None:
            return None
        # 确保返回小写字符串值
        if isinstance(value, FeedbackTypeEnum):
            result = value.value  # 返回小写字符串值 "like", "bookmark", "dislike"
            return result
        if isinstance(value, str):
            return value.lower()  # 确保是小写
        # 如果是其他类型，尝试转换为字符串并转小写
        result = str(value).lower()
        return result

    def process_result_value(self, value, dialect):
        """将数据库值转换为 Python Enum"""
        if value is None:
            return None
        if isinstance(value, FeedbackTypeEnum):
            return value
        # 从数据库读取的值应该是字符串，转换为 Enum
        str_value = value.lower() if isinstance(value, str) else str(value).lower()
        return FeedbackTypeEnum(str_value)


class UserFeedback(TimestampMixin, Base):
    __tablename__ = "user_feedback"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    paper_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), index=True)
    feedback_type: Mapped[FeedbackTypeEnum] = mapped_column(FeedbackTypeEnumType(), nullable=False)

    paper: Mapped[Paper] = relationship("Paper", backref="feedback")

    paper: Mapped[Paper] = relationship("Paper", backref="feedback_entries")

    __table_args__ = (
        CheckConstraint("feedback_type IN ('like','bookmark','dislike')", name="feedback_type_valid"),
        {
            "sqlite_autoincrement": True,
            "comment": "Stores user-level explicit feedback for recommendation tuning",
        },
    )


class UserProfile(TimestampMixin, Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True, nullable=False)
    # 感兴趣的领域（如 cs.AI, cs.CV, cs.LG 等 arXiv 分类）
    interested_categories: Mapped[List[str]] = mapped_column(ARRAY(String(length=128)), nullable=False, default=list)
    # 研究方向关键词（用户自定义）
    research_keywords: Mapped[List[str]] = mapped_column(ARRAY(String(length=256)), nullable=False, default=list)
    # 偏好描述（文本形式，可用于生成初始 embedding）
    preference_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # 是否完成初始设置
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        {
            "comment": "用户偏好和兴趣资料，用于个性化推荐",
        },
    )


class DailyRecommendationPool(TimestampMixin, Base):
    __tablename__ = "daily_recommendation_pool"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pool_date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    paper_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    paper: Mapped[Paper] = relationship(viewonly=True)

    __table_args__ = (
        CheckConstraint("position >= 0", name="position_non_negative"),
        CheckConstraint("score >= 0", name="score_non_negative"),
    )


class ConferenceRecommendationPool(TimestampMixin, Base):
    __tablename__ = "conference_recommendation_pool"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    paper_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    paper: Mapped[Paper] = relationship(viewonly=True)

    __table_args__ = (
        CheckConstraint("position >= 0", name="position_non_negative"),
        CheckConstraint("score >= 0", name="score_non_negative"),
    )


class PaperTranslation(TimestampMixin, Base):
    """
    论文翻译表
    
    存储论文的中文翻译内容。
    AI解读内容已迁移至独立的 PaperInterpretation 表。
    """
    __tablename__ = "paper_translations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    title_zh: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="论文标题中文翻译")
    summary_zh: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="论文摘要中文翻译")
    model_name: Mapped[str] = mapped_column(String(256), nullable=False, comment="翻译使用的AI模型名称")

    paper: Mapped[Paper] = relationship("Paper", back_populates="translation")

    __table_args__ = (
        {
            "comment": "存储论文的中文翻译内容，AI解读已迁移至PaperInterpretation表",
        },
    )


class PaperInterpretation(TimestampMixin, Base):
    """
    论文AI解读表
    
    存储论文的AI解读内容，格式已统一为markdown格式：
    - 93.6%的记录使用标准markdown格式（## 标题）
    - 6.4%的记录使用兼容的结构化文本格式
    - 所有记录都适合TTS语音合成（需清理markdown标记）
    - 内容长度控制在800-1200字符范围内
    """
    __tablename__ = "paper_interpretations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    interpretation: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="AI解读内容，markdown格式，包含研究背景、核心方法、主要贡献三个部分")
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="zh", comment="解读语言，默认中文")
    model_name: Mapped[str] = mapped_column(String(256), nullable=False, comment="生成解读的AI模型名称")

    paper: Mapped[Paper] = relationship("Paper", back_populates="interpretation")

    __table_args__ = (
        {
            "comment": "存储论文的AI解读内容，格式已统一为markdown，适合用户阅读和TTS语音合成",
        },
    )


class PaperVisual(TimestampMixin, Base):
    """Store generated visual explanations for papers"""
    __tablename__ = "paper_visuals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    image_data: Mapped[str] = mapped_column(Text, nullable=False)  # Base64 data URL
    model_name: Mapped[str] = mapped_column(String(128), nullable=False, default="gemini-2.5-flash-image")
    
    paper: Mapped["Paper"] = relationship()
