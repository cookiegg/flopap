from __future__ import annotations

from datetime import date, datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PaperTranslationMeta(BaseModel):
    """论文翻译元数据"""
    title_zh: Optional[str] = None
    summary_zh: Optional[str] = None
    model_name: Optional[str] = None


class PaperInterpretationMeta(BaseModel):
    """论文AI解读元数据"""
    interpretation: Optional[str] = None
    language: str = "zh"
    model_name: Optional[str] = None


class PaperMeta(BaseModel):
    id: UUID
    arxiv_id: str
    title: str
    summary: str
    authors: List[dict[str, str]]  # 修正：数据库中存储的是字典列表
    categories: List[str]
    submitted_date: datetime
    updated_date: Optional[datetime]
    pdf_url: Optional[str]
    html_url: Optional[str]
    comment: Optional[str]
    doi: Optional[str]
    primary_category: Optional[str]
    source: str = Field(description="数据源: arxiv, neurips2025")  # 新增：数据源字段
    translation: Optional[PaperTranslationMeta] = Field(default=None, description="中文翻译")
    interpretation: Optional[PaperInterpretationMeta] = Field(default=None, description="AI解读")
    infographic_html: Optional[str] = Field(default=None, description="信息图HTML内容")
    visual_html: Optional[str] = Field(default=None, description="可视化图HTML内容")


class FeedItem(BaseModel):
    position: int
    score: float
    paper: PaperMeta
    liked: bool = Field(default=False)
    bookmarked: bool = Field(default=False)
    disliked: bool = Field(default=False)


class FeedResponse(BaseModel):
    items: List[FeedItem]
    next_cursor: int
    total: int


class FeedSummary(BaseModel):
    """Feed摘要信息"""
    last_open: Optional[datetime] = None
    last_feed_date: Optional[date] = None
    missed_days: int = 0
    available_dates: List[date] = Field(default_factory=list)
    total_unread: int = 0
    today_count: int = 0


class FeedbackRequest(BaseModel):
    paper_id: UUID
    action: Literal["like", "bookmark", "dislike"]
    value: bool = True
    confirmed: bool = False


class FeedbackResponse(BaseModel):
    paper_id: UUID
    liked: bool
    bookmarked: bool
    disliked: bool
    requires_confirmation: bool = False
    message: Optional[str] = None


class PoolGenerateRequest(BaseModel):
    pool_date: Optional[str] = None
    source_date: Optional[str] = None


class PoolSummary(BaseModel):
    pool_date: str
    size: int
    active: int


class UserSummary(BaseModel):
    liked: List[PaperMeta]
    bookmarked: List[PaperMeta]
    disliked: List[PaperMeta]
    stats: dict


class UserProfileRequest(BaseModel):
    interested_categories: List[str] = Field(default_factory=list, description="感兴趣的 arXiv 分类，如 cs.AI, cs.CV")
    research_keywords: List[str] = Field(default_factory=list, description="研究方向关键词")
    preference_description: Optional[str] = Field(None, description="偏好描述（可选）")
    name: Optional[str] = Field(None, description="用户昵称")


class UserProfileResponse(BaseModel):
    user_id: str
    interested_categories: List[str]
    research_keywords: List[str]
    preference_description: Optional[str]
    onboarding_completed: bool
    name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None


class PaperDetailResponse(BaseModel):
    """论文详情响应"""
    paper: PaperMeta
    liked: bool = Field(default=False)
    bookmarked: bool = Field(default=False)
    disliked: bool = Field(default=False)
