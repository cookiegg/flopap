"""用户活动跟踪服务"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional

import pendulum
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import UserActivity


def record_user_open(session: Session, user_id: str, feed_date: Optional[date] = None) -> UserActivity:
    """记录用户打开应用"""
    now = pendulum.now("UTC")
    today = now.date()
    
    stmt = select(UserActivity).where(UserActivity.user_id == user_id)
    activity = session.execute(stmt).scalar_one_or_none()
    
    if activity is None:
        activity = UserActivity(
            user_id=user_id,
            last_open_time=now,
            last_feed_date=feed_date or today,
        )
        session.add(activity)
    else:
        activity.last_open_time = now
        if feed_date:
            activity.last_feed_date = feed_date
    
    session.commit()
    return activity


def get_user_activity(session: Session, user_id: str) -> Optional[UserActivity]:
    """获取用户活动记录"""
    stmt = select(UserActivity).where(UserActivity.user_id == user_id)
    return session.execute(stmt).scalar_one_or_none()


def get_missed_days(session: Session, user_id: str) -> int:
    """获取用户错过的天数"""
    activity = get_user_activity(session, user_id)
    if activity is None or activity.last_open_time is None:
        return 0
    
    now = pendulum.now("UTC")
    last_open = pendulum.instance(activity.last_open_time)
    days_diff = (now.date() - last_open.date()).days
    
    # 错过的天数 = 间隔天数 - 1（今天不算错过）
    return max(0, days_diff - 1)
