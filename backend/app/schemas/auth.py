from __future__ import annotations

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    id: str
    email: str | None
    phone_number: str | None = None
    name: str | None
    avatar_url: str | None
    provider: str | None  # 修正：匹配数据库中的 provider 字段名


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class OAuthCallbackRequest(BaseModel):
    code: str
    provider: str  # 'google' or 'github'
