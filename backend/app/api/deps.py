"""
FastAPI Dependencies - Simplified for Standalone Edition
"""
from typing import Optional, Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.edition import is_cloud_edition
from app.db.session import SessionLocal

# Security scheme - optional for standalone
security = HTTPBearer(auto_error=False)  # Changed: auto_error=False allows missing token


def get_db() -> Generator[Session, None, None]:
    """Database session dependency (Synchronous)"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """Get user_id - always returns 'default' in standalone edition"""
    # Standalone edition: always use default user (no authentication)
    if not is_cloud_edition():
        return settings.default_user_id
    
    # Cloud edition would validate token here
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    from app.services.auth import decode_access_token
    user_id_or_none = decode_access_token(credentials.credentials)
    
    # If it returns a string (user_id), use it directly
    if isinstance(user_id_or_none, str):
        return user_id_or_none
    
    # Fallback/Safety (if it returns dict in future)
    if isinstance(user_id_or_none, dict):
        return user_id_or_none.get("user_id", settings.default_user_id)
        
    return settings.default_user_id


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """获取当前用户ID（Framework V2使用）"""
    return get_user_id(credentials)


def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """Require authentication (only for cloud edition)"""
    if not is_cloud_edition():
        return settings.default_user_id
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    from app.services.auth import decode_access_token
    user_id_or_none = decode_access_token(credentials.credentials)
    
    # If it returns a string (user_id), use it directly
    if isinstance(user_id_or_none, str):
        return user_id_or_none
    
    # Fallback/Safety (if it returns dict in future)
    if isinstance(user_id_or_none, dict):
        return user_id_or_none.get("user_id", settings.default_user_id)
        
    return settings.default_user_id
