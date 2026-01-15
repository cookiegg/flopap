"""
认证服务 - 用户身份验证和授权
功能：
- JWT token生成和验证
- Google OAuth认证
- 手机号验证码登录
- 用户会话管理
- 权限检查和中间件
- 支持多种登录方式（邮箱、手机、OAuth）
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import httpx
import jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User


def create_access_token(user_id: str) -> str:
    """Create JWT access token"""
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Optional[str]:
    """Decode JWT token and return user_id"""
    # Support 'default' token for standalone mode
    if token in ('default', 'anonymous', 'standalone'):
        return 'default'
    
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


async def exchange_google_code(code: str) -> dict:
    """Exchange Google OAuth code for user info or verify idToken (Capacitor)"""
    async with httpx.AsyncClient() as client:
        # 检查是否为 idToken (JWT格式，以 eyJ 开头)
        if code.startswith('eyJ'):
            # Capacitor 原生应用：验证 idToken
            verify_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={code}"
            verify_response = await client.get(verify_url)
            verify_response.raise_for_status()
            token_info = verify_response.json()
            
            # 验证 audience (client_id)
            if token_info.get('aud') != settings.google_client_id:
                raise ValueError("Invalid token audience")
            
            # 返回标准格式的用户信息
            return {
                "id": token_info.get("sub"),
                "email": token_info.get("email"),
                "name": token_info.get("name"),
                "picture": token_info.get("picture"),
                "verified_email": token_info.get("email_verified", "true") == "true"
            }
        else:
            # Web 应用：OAuth 授权码流程
            token_url = "https://oauth2.googleapis.com/token"
            token_data = {
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.oauth_redirect_uri,
                "grant_type": "authorization_code",
            }
            
            token_response = await client.post(token_url, data=token_data)
            token_response.raise_for_status()
            tokens = token_response.json()
            
            # Get user info
            userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
            headers = {"Authorization": f"Bearer {tokens['access_token']}"}
            userinfo_response = await client.get(userinfo_url, headers=headers)
            userinfo_response.raise_for_status()
            
            return userinfo_response.json()


async def exchange_github_code(code: str) -> dict:
    """Exchange GitHub OAuth code for user info"""
    # Exchange code for access token
    token_url = "https://github.com/login/oauth/access_token"
    token_data = {
        "code": code,
        "client_id": settings.github_client_id,
        "client_secret": settings.github_client_secret,
        "redirect_uri": settings.oauth_redirect_uri,
    }
    
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            token_url,
            data=token_data,
            headers={"Accept": "application/json"}
        )
        token_response.raise_for_status()
        tokens = token_response.json()
        
        # Get user info
        userinfo_url = "https://api.github.com/user"
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        userinfo_response = await client.get(userinfo_url, headers=headers)
        userinfo_response.raise_for_status()
        user_data = userinfo_response.json()
        
        # Get user email if not public
        if not user_data.get("email"):
            email_url = "https://api.github.com/user/emails"
            email_response = await client.get(email_url, headers=headers)
            email_response.raise_for_status()
            emails = email_response.json()
            primary_email = next((e for e in emails if e["primary"]), emails[0])
            user_data["email"] = primary_email["email"]
        
        return user_data


def get_or_create_user(db: Session, provider: str, oauth_data: dict) -> User:
    """Get or create user from OAuth data"""
    if provider == "google":
        oauth_id = oauth_data["id"]
        email = oauth_data["email"]
        name = oauth_data.get("name")
        avatar_url = oauth_data.get("picture")
    elif provider == "github":
        oauth_id = str(oauth_data["id"])
        email = oauth_data["email"]
        name = oauth_data.get("name") or oauth_data.get("login")
        avatar_url = oauth_data.get("avatar_url")
    else:
        raise ValueError(f"Unsupported OAuth provider: {provider}")
    
    # Try to find existing user
    user = db.query(User).filter(
        User.provider == provider,
        User.oauth_id == oauth_id
    ).first()
    
    if user:
        # Update last login and info
        user.last_login = datetime.utcnow()
        user.name = name
        user.avatar_url = avatar_url
        db.commit()
        db.refresh(user)
        return user
    
    # Create new user
    user_id = f"{provider}_{oauth_id}"
    user = User(
        id=user_id,
        email=email,
        name=name,
        avatar_url=avatar_url,
        provider=provider,
        oauth_id=oauth_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_or_create_user_by_phone(db: Session, phone_number: str) -> User:
    """Get or create user by phone number"""
    user = db.query(User).filter(User.phone_number == phone_number).first()
    
    if user:
        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user
    
    # Create new user
    # Generate a random user ID or let DB handle it (model defaults to uuid)
    # Name defaults to masked phone number
    masked_phone = f"User {phone_number[-4:]}" if len(phone_number) >= 4 else "User"
    
    user = User(
        phone_number=phone_number,
        name=masked_phone,
        provider="sms",
        # Email is optional/null
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, phone_number: str, verification_code: str) -> Optional[User]:
    """验证用户手机号和验证码"""
    # 简化验证：接受任何验证码（开发环境）
    if verification_code in ["123456", "000000"]:
        return get_or_create_user_by_phone(db, phone_number)
    return None
