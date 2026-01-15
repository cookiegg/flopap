"""推荐设置 API - 控制推荐池比例和显示模式"""
from datetime import datetime
from typing import Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_user_id
from app.models.framework_v2 import UserRecommendationSettings
from app.core.config import settings

router = APIRouter()


class RecommendationSettingsRequest(BaseModel):
    arxiv_ratio: int = 50  # 1-100, 表示百分比
    conference_ratio: int = 50  # 1-100, 表示百分比
    max_pool_size: int = 100
    enable_auto_generation: bool = False
    preferred_models: Dict[str, str] = {}


class RecommendationSettingsResponse(BaseModel):
    user_id: str
    arxiv_ratio: int
    conference_ratio: int
    enable_auto_generation: bool
    preferred_models: Dict[str, str]
    updated_at: str


def get_or_create_settings(db: Session, user_id: str) -> UserRecommendationSettings:
    """获取或创建用户推荐设置"""
    setting = db.query(UserRecommendationSettings).filter(
        UserRecommendationSettings.user_id == user_id
    ).first()
    
    if not setting:
        setting = UserRecommendationSettings(
            user_id=user_id,
            arxiv_ratio=50,
            conference_ratio=50,
            enable_auto_generation=False,
            preferred_models=[],
            updated_at=datetime.utcnow()
        )
        db.add(setting)
        db.commit()
        db.refresh(setting)
    
    return setting


@router.get("/settings", response_model=RecommendationSettingsResponse)
async def get_recommendation_settings(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id)
):
    """获取用户推荐设置"""
    setting = get_or_create_settings(db, user_id)
    
    return RecommendationSettingsResponse(
        user_id=setting.user_id,
        arxiv_ratio=setting.arxiv_ratio,
        conference_ratio=setting.conference_ratio,
        enable_auto_generation=setting.enable_auto_generation,
        preferred_models=dict(setting.preferred_models) if setting.preferred_models else {},
        updated_at=setting.updated_at.isoformat() if setting.updated_at else datetime.utcnow().isoformat()
    )


@router.put("/settings")
async def update_recommendation_settings(
    req: RecommendationSettingsRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id)
):
    """更新用户推荐设置"""
    setting = get_or_create_settings(db, user_id)
    
    # 验证范围
    if not (1 <= req.arxiv_ratio <= 100):
        raise HTTPException(status_code=400, detail="arxiv_ratio must be between 1 and 100")
    if not (1 <= req.conference_ratio <= 100):
        raise HTTPException(status_code=400, detail="conference_ratio must be between 1 and 100")
    
    setting.arxiv_ratio = req.arxiv_ratio
    setting.conference_ratio = req.conference_ratio
    setting.enable_auto_generation = req.enable_auto_generation
    setting.preferred_models = list(req.preferred_models.keys()) if req.preferred_models else []
    setting.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "message": "Settings updated",
        "settings": {
            "arxiv_ratio": setting.arxiv_ratio,
            "conference_ratio": setting.conference_ratio,
            "enable_auto_generation": setting.enable_auto_generation
        }
    }


@router.get("/available-models")
async def get_available_models():
    """获取可用的模型列表"""
    return {
        "models": {
            "deepseek-chat": {
                "name": "DeepSeek Chat",
                "provider": "DeepSeek",
                "description": "高性价比的通用模型",
                "cost_per_1k_tokens": 0.001
            },
            "gpt-4": {
                "name": "GPT-4",
                "provider": "OpenAI",
                "description": "强大的推理能力",
                "cost_per_1k_tokens": 0.03
            }
        }
    }


@router.get("/stats")
async def get_stats():
    """获取推荐统计信息"""
    return {
        "total_recommendations": 0,
        "arxiv_count": 0,
        "conference_count": 0,
        "last_updated": datetime.utcnow().isoformat()
    }

