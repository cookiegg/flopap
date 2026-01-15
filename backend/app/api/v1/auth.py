"""
Authentication API - Standalone Edition (Single-User Mode)
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class UserInfo(BaseModel):
    user_id: str
    name: str
    email: str | None = None
    phone_number: str | None = None
    avatar_url: str | None = None


@router.get("/me", response_model=UserInfo)
def get_current_user_info():
    """Get current user info - returns default user in standalone edition"""
    return UserInfo(
        user_id="default",
        name="Local User",
        email=None,
        phone_number=None,
        avatar_url=None
    )

