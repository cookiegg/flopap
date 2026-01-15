"""
管理API - 受限的管理功能
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.deps import get_db, require_auth
from app.core.config import settings

router = APIRouter()


def require_admin(user_id: str = Depends(require_auth)):
    """要求管理员权限"""
    # 简单的管理员检查 - 生产环境应该从数据库验证
    if user_id not in settings.admin_user_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user_id


class SystemStats(BaseModel):
    total_papers: int
    total_users: int
    total_recommendations: int
    content_generation_stats: dict


@router.get("/stats", response_model=SystemStats)
def get_system_stats(
    db: Session = Depends(get_db),
    admin_user: str = Depends(require_admin),
):
    """获取系统统计信息"""
    from sqlalchemy import text
    
    # 获取基础统计
    total_papers = db.execute(text("SELECT COUNT(*) FROM papers")).scalar()
    total_users = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
    total_recommendations = db.execute(text("SELECT COUNT(*) FROM user_recommendation_pools")).scalar()
    
    # 内容生成统计
    translation_count = db.execute(text("SELECT COUNT(*) FROM paper_translations")).scalar()
    interpretation_count = db.execute(text("SELECT COUNT(*) FROM paper_interpretations")).scalar()
    infographic_count = db.execute(text("SELECT COUNT(*) FROM paper_infographics")).scalar()
    tts_count = db.execute(text("SELECT COUNT(*) FROM paper_tts")).scalar()
    visual_count = db.execute(text("SELECT COUNT(*) FROM paper_visuals")).scalar()
    
    return SystemStats(
        total_papers=total_papers or 0,
        total_users=total_users or 0,
        total_recommendations=total_recommendations or 0,
        content_generation_stats={
            "translations": translation_count or 0,
            "interpretations": interpretation_count or 0,
            "infographics": infographic_count or 0,
            "tts": tts_count or 0,
            "visuals": visual_count or 0
        }
    )


@router.get("/health")
def health_check():
    """系统健康检查"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": "2025-12-19T17:35:00Z"
    }
