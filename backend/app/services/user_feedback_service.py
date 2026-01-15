"""
用户反馈服务 - 专门处理用户反馈逻辑
从复杂的feed.py中提取出来的纯反馈处理功能
"""

from uuid import UUID
from typing import Dict, Union

from sqlalchemy.orm import Session
from sqlalchemy import select, cast, String

from app.models import UserFeedback, FeedbackTypeEnum, Paper
from app.schemas.feed import FeedbackResponse
from app.services.recommendation import RecommendationFacade, FeedbackType


def handle_user_feedback(
    session: Session,
    *,
    user_id: str,
    paper_id: UUID,
    action: FeedbackTypeEnum,
    value: bool,
    confirmed: bool = False,
) -> FeedbackResponse:
    """处理用户反馈"""
    
    # 验证论文存在
    paper = session.get(Paper, paper_id)
    if not paper:
        raise ValueError("论文不存在")
    
    facade = RecommendationFacade(session)
    
    if action == FeedbackTypeEnum.DISLIKE:
        if value and not confirmed:
            return FeedbackResponse(
                paper_id=paper_id,
                liked=_has_feedback(session, user_id, paper_id, FeedbackTypeEnum.LIKE),
                bookmarked=_has_feedback(session, user_id, paper_id, FeedbackTypeEnum.BOOKMARK),
                disliked=_has_feedback(session, user_id, paper_id, FeedbackTypeEnum.DISLIKE),
                requires_confirmation=True,
                message="确认后将移除该论文并清除点赞/收藏",
            )
        
        if value:
            # 移除其他反馈
            _remove_feedback(session, user_id, paper_id, [FeedbackTypeEnum.LIKE, FeedbackTypeEnum.BOOKMARK])
            # 添加不感兴趣反馈
            _ensure_feedback(session, user_id, paper_id, FeedbackTypeEnum.DISLIKE)
            
            # 使用多层推荐系统处理不感兴趣 - 不修改排序表
            from app.services.recommendation import MultiLayerRecommendationService
            ml_service = MultiLayerRecommendationService(session)
            result = ml_service.handle_user_dislike(user_id, paper_id, "arxiv")  # 默认source
            
            # 失效用户缓存
            from app.services.cache_service import CacheService
            CacheService.invalidate_user_feed(user_id)
            
            message = result.get("message", "已标记为不感兴趣，该论文已从推荐池移除")
        else:
            message = "不感兴趣不可撤销"
    else:
        message = None
        if value:
            if _has_feedback(session, user_id, paper_id, FeedbackTypeEnum.DISLIKE):
                message = "已标记不感兴趣，无法再次点赞或收藏"
            else:
                _ensure_feedback(session, user_id, paper_id, action)
                # 通知推荐系统
                if action == FeedbackTypeEnum.LIKE:
                    facade.user_like_paper(user_id, paper_id)
                elif action == FeedbackTypeEnum.BOOKMARK:
                    facade.user_bookmark_paper(user_id, paper_id)
        else:
            _remove_feedback(session, user_id, paper_id, [action])
    
    return FeedbackResponse(
        paper_id=paper_id,
        liked=_has_feedback(session, user_id, paper_id, FeedbackTypeEnum.LIKE),
        bookmarked=_has_feedback(session, user_id, paper_id, FeedbackTypeEnum.BOOKMARK),
        disliked=_has_feedback(session, user_id, paper_id, FeedbackTypeEnum.DISLIKE),
        requires_confirmation=False,
        message=message,
    )


def _has_feedback(session: Session, user_id: str, paper_id: UUID, feedback_type: Union[FeedbackTypeEnum, str]) -> bool:
    """检查用户是否有特定类型的反馈"""
    feedback_val = feedback_type.value if hasattr(feedback_type, 'value') else feedback_type
    
    stmt = select(UserFeedback.id).where(
        UserFeedback.user_id == user_id,
        UserFeedback.paper_id == paper_id,
        cast(UserFeedback.feedback_type, String) == feedback_val,
    )
    return session.execute(stmt).scalar_one_or_none() is not None


def _ensure_feedback(session: Session, user_id: str, paper_id: UUID, feedback_type: Union[FeedbackTypeEnum, str]) -> None:
    """确保反馈存在"""
    if not _has_feedback(session, user_id, paper_id, feedback_type):
        from uuid import uuid4
        from sqlalchemy import insert
        
        feedback_val = feedback_type.value if hasattr(feedback_type, 'value') else feedback_type
        
        insert_stmt = insert(UserFeedback.__table__).values(
            id=uuid4(),
            user_id=user_id,
            paper_id=paper_id,
            feedback_type=feedback_val,
        )
        session.execute(insert_stmt)
        session.commit()


def _remove_feedback(session: Session, user_id: str, paper_id: UUID, types: list[Union[FeedbackTypeEnum, str]]) -> None:
    """移除特定类型的反馈"""
    type_values = [t.value if hasattr(t, 'value') else t for t in types]
    stmt = select(UserFeedback).where(
        UserFeedback.user_id == user_id,
        UserFeedback.paper_id == paper_id,
        cast(UserFeedback.feedback_type, String).in_(type_values),
    )
    for feedback in session.execute(stmt).scalars().all():
        session.delete(feedback)
    session.commit()


def get_user_feedback_summary(session: Session, user_id: str) -> Dict[str, list]:
    """获取用户反馈摘要"""
    from app.schemas.feed import UserSummary, PaperMeta
    
    def _fetch_by_type(feedback_type: Union[FeedbackTypeEnum, str]) -> list:
        feedback_val = feedback_type.value if hasattr(feedback_type, 'value') else feedback_type
        stmt = (
            select(Paper)
            .join(UserFeedback, UserFeedback.paper_id == Paper.id)
            .where(
                UserFeedback.user_id == user_id,
                cast(UserFeedback.feedback_type, String) == feedback_val,
            )
            .order_by(UserFeedback.created_at.desc())
        )
        papers = session.execute(stmt).scalars().all()
        return [_paper_to_simple_meta(paper) for paper in papers]
    
    liked = _fetch_by_type(FeedbackTypeEnum.LIKE)
    bookmarked = _fetch_by_type(FeedbackTypeEnum.BOOKMARK)
    disliked = _fetch_by_type(FeedbackTypeEnum.DISLIKE)
    
    return {
        "liked": liked,
        "bookmarked": bookmarked,
        "disliked": disliked,
        "stats": {
            "liked_count": len(liked),
            "bookmarked_count": len(bookmarked),
            "disliked_count": len(disliked),
        }
    }


def _paper_to_simple_meta(paper: Paper):
    """简化的Paper转换"""
    from app.schemas.feed import PaperMeta
    
    # 处理authors字段 - 确保是字典格式
    authors = []
    if paper.authors:
        for author in paper.authors:
            if isinstance(author, str):
                authors.append({"name": author})
            elif isinstance(author, dict):
                authors.append(author)
            else:
                authors.append({"name": str(author)})
    
    # 处理翻译字段
    translation = None
    if paper.translation:
        translation = {
            "title_zh": paper.translation.title_zh,
            "summary_zh": paper.translation.summary_zh,
            "model_name": paper.translation.model_name
        }

    # 处理AI解读字段
    interpretation = None
    if paper.interpretation:
        interpretation = {
            "interpretation": paper.interpretation.interpretation,
            "language": paper.interpretation.language,
            "model_name": paper.interpretation.model_name
        }

    return PaperMeta(
        id=paper.id,
        arxiv_id=paper.arxiv_id,
        title=paper.title,
        summary=paper.summary,
        authors=authors,
        categories=paper.categories,
        submitted_date=paper.submitted_date,
        updated_date=paper.updated_date,
        pdf_url=paper.pdf_url,
        html_url=paper.html_url,
        comment=paper.comment,
        doi=paper.doi,
        primary_category=paper.primary_category,
        source=getattr(paper, 'source', 'arxiv'),
        translation=translation,
        interpretation=interpretation,
    )
