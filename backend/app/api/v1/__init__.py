"""
API v1 - 统一网关
只暴露前端必需的核心功能
"""

from fastapi import APIRouter
from .auth import router as auth_router
from .feed import router as feed_router
from .user import router as user_router
from .paper import router as paper_router
from .admin import router as admin_router
# SMS router removed for standalone edition
from .tts import router as tts_router
from .factory import router as factory_router
from .recommendation import router as recommendation_router
from .data_sources import router as data_sources_router
from .pool_settings import router as pool_settings_router
# Internal routers removed for standalone edition

# 创建v1 API路由器
v1_router = APIRouter(prefix="/v1")

# 注册核心API路由
v1_router.include_router(auth_router, prefix="/auth", tags=["认证"])
# SMS router removed for standalone edition
v1_router.include_router(feed_router, prefix="/feed", tags=["推荐流"])
v1_router.include_router(user_router, prefix="/user", tags=["用户"])
v1_router.include_router(paper_router, prefix="/paper", tags=["论文内容"])
v1_router.include_router(admin_router, prefix="/admin", tags=["管理"])
v1_router.include_router(tts_router, prefix="/tts", tags=["TTS音频"])
v1_router.include_router(factory_router, prefix="/factory", tags=["Factory控制台"])
v1_router.include_router(recommendation_router, prefix="/recommendation", tags=["推荐系统"])
v1_router.include_router(data_sources_router, prefix="/data-sources", tags=["数据源"])
v1_router.include_router(pool_settings_router, prefix="/pool-settings", tags=["池设置"])
# Internal routers removed for standalone edition

__all__ = ["v1_router"]

