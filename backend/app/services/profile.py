from __future__ import annotations

from typing import List, Optional
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import UserProfile


@dataclass
class UserProfileData:
    """用户完整资料数据类，包含User和UserProfile信息"""
    user_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None
    interested_categories: List[str] = None
    research_keywords: List[str] = None
    preference_description: Optional[str] = None
    onboarding_completed: bool = False


def get_user_profile(session: Session, user_id: str) -> Optional[UserProfileData]:
    """获取用户资料，如果不存在则返回 None"""
    from sqlalchemy import select
    from app.models.user import User

    # 先查询User表获取基本信息
    user_stmt = select(User).where(User.id == user_id)
    user = session.execute(user_stmt).scalar_one_or_none()
    
    if not user:
        return None

    # 查询UserProfile表获取偏好设置
    profile_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    profile = session.execute(profile_stmt).scalar_one_or_none()
    
    if not profile:
        # 如果没有profile，创建一个默认的
        profile = UserProfile(
            user_id=user_id,
            interested_categories=[],
            research_keywords=[],
            onboarding_completed=False
        )
        session.add(profile)
        session.commit()
    
    # 返回合并的数据
    return UserProfileData(
        user_id=user_id,
        name=user.name,
        email=user.email,
        phone_number=user.phone_number,
        avatar_url=user.avatar_url,
        interested_categories=profile.interested_categories or [],
        research_keywords=profile.research_keywords or [],
        preference_description=profile.preference_description,
        onboarding_completed=profile.onboarding_completed
    )


def update_user_profile(
    session: Session,
    *,
    user_id: str,
    interested_categories: List[str],
    research_keywords: List[str],
    preference_description: Optional[str] = None,
) -> UserProfile:
    """更新或创建用户资料"""
    profile = get_user_profile(session, user_id)
    
    if profile is None:
        profile = UserProfile(
            user_id=user_id,
            interested_categories=interested_categories,
            research_keywords=research_keywords,
            preference_description=preference_description,
            onboarding_completed=False,
        )
        session.add(profile)
    else:
        profile.interested_categories = interested_categories
        profile.research_keywords = research_keywords
        if preference_description is not None:
            profile.preference_description = preference_description
    
    return profile

