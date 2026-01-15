"""
用户管理API - 用户配置和偏好设置
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.deps import get_db, get_user_id
from app.schemas.feed import UserSummary  # 导入UserSummary schema

router = APIRouter()


class UserPreferences(BaseModel):
    interested_categories: List[str]
    research_keywords: List[str]
    name: str | None = None


class UserProfileResponse(BaseModel):
    user_id: str
    name: str | None = None
    email: str | None = None
    phone_number: str | None = None
    avatar_url: str | None = None
    interested_categories: List[str]
    research_keywords: List[str]
    onboarding_completed: bool


class UserProfileUpdateRequest(BaseModel):
    name: str | None = None
    interested_categories: List[str] | None = None
    research_keywords: List[str] | None = None
    preference_description: str | None = None


@router.get("/profile", response_model=UserProfileResponse)
def get_user_profile_v1(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """获取用户完整资料"""
    from app.services.profile import get_user_profile
    
    profile = get_user_profile(db, user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    return UserProfileResponse(
        user_id=profile.user_id,
        name=profile.name,
        email=profile.email,
        phone_number=profile.phone_number,
        avatar_url=profile.avatar_url,
        interested_categories=profile.interested_categories or [],
        research_keywords=profile.research_keywords or [],
        onboarding_completed=profile.onboarding_completed
    )


@router.put("/profile", response_model=UserProfileResponse)
def update_user_profile_v1(
    profile_data: UserProfileUpdateRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """更新用户完整资料"""
    from app.services.profile import update_user_profile, get_user_profile
    
    # 获取当前资料
    current_profile = get_user_profile(db, user_id)
    
    # 准备更新数据
    update_data = {}
    if profile_data.interested_categories is not None:
        update_data['interested_categories'] = profile_data.interested_categories
    if profile_data.research_keywords is not None:
        update_data['research_keywords'] = profile_data.research_keywords
    if profile_data.preference_description is not None:
        update_data['preference_description'] = profile_data.preference_description
    
    # 更新资料
    if update_data:
        profile = update_user_profile(db, user_id=user_id, **update_data)
        db.commit()
    else:
        profile = current_profile
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Failed to update profile"
        )
    
    return UserProfileResponse(
        user_id=profile.user_id,
        name=profile.name,
        email=profile.email,
        phone_number=profile.phone_number,
        avatar_url=profile.avatar_url,
        interested_categories=profile.interested_categories or [],
        research_keywords=profile.research_keywords or [],
        onboarding_completed=profile.onboarding_completed
    )


@router.put("/preferences")
def update_preferences(
    preferences: UserPreferences,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """更新用户偏好设置"""
    from app.services.profile import update_user_profile
    
    success = update_user_profile(
        db,
        user_id=user_id,
        interested_categories=preferences.interested_categories,
        research_keywords=preferences.research_keywords,
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update preferences"
        )
    
    db.commit()
    return {"message": "Preferences updated successfully"}


@router.post("/onboarding/complete")
def complete_onboarding(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """完成用户引导"""
    from app.models.paper import UserProfile
    from sqlalchemy import select
    
    # 直接查询数据库模型对象
    profile = db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    ).scalar_one_or_none()
    
    if not profile:
        # 如果没有profile，创建一个
        profile = UserProfile(
            user_id=user_id,
            interested_categories=[],
            research_keywords=[],
            onboarding_completed=True  # 直接设置为True
        )
        db.add(profile)
    else:
        profile.onboarding_completed = True
    
    db.commit()
    
    return {"message": "Onboarding completed successfully"}


@router.get("/summary", response_model=UserSummary)
def get_user_summary_v1(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
) -> UserSummary:
    """获取用户摘要信息（收藏、点赞等）"""
    from app.services.user_feedback_service import get_user_feedback_summary
    
    return get_user_feedback_summary(db, user_id)
