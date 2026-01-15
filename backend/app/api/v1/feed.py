"""
推荐流API - 核心推荐功能
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_user_id
from app.schemas.feed import FeedResponse, FeedbackRequest, FeedbackResponse

router = APIRouter()


@router.get("", response_model=FeedResponse)
def get_user_feed(
    cursor: int = Query(0, ge=0, description="分页游标"),
    limit: int = Query(10, ge=1, le=2000, description="每页数量"),
    source: Optional[str] = Query(None, description="数据源: arxiv, conf/neurips2025, conf/iclr2025"),
    sub: Optional[str] = Query(None, description="arxiv子池: today(今日), week(一周)"),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
) -> FeedResponse:
    """获取用户个性化推荐流"""
    from app.services.feed_service import get_personalized_feed
    
    return get_personalized_feed(
        db, 
        cursor=cursor, 
        limit=limit, 
        user_id=user_id, 
        source=source,
        sub=sub
    )


@router.post("/feedback", response_model=FeedbackResponse)
def submit_user_feedback(
    feedback: FeedbackRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
) -> FeedbackResponse:
    """提交用户反馈"""
    from app.services.user_feedback_service import handle_user_feedback
    
    return handle_user_feedback(
        db,
        user_id=user_id,
        paper_id=feedback.paper_id,
        action=feedback.action,
        value=feedback.value,
        confirmed=feedback.confirmed
    )


@router.get("/stats")
def get_feed_stats(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """获取用户推荐统计"""
    from app.services.user_feedback_service import get_user_feedback_summary
    return get_user_feedback_summary(db, user_id)
