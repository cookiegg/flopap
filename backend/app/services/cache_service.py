"""
缓存服务 - Redis 缓存封装
提供简单的缓存接口，Redis 不可用时优雅降级
"""
import json
from typing import Any, List, Optional
from loguru import logger

from app.core.redis import get_redis
from app.core.config import settings


class CacheService:
    """缓存服务封装"""
    
    # 缓存 Key 前缀
    PREFIX_FEED_TODAY = "feed:today:"
    PREFIX_FEED_WEEK = "feed:week:"
    PREFIX_PAPER = "paper:"
    PREFIX_USER_PROFILE = "user:profile:"
    
    @classmethod
    def _get_client(cls):
        """获取 Redis 客户端"""
        return get_redis()
    
    @classmethod
    def get(cls, key: str) -> Optional[str]:
        """获取缓存值"""
        client = cls._get_client()
        if not client:
            return None
        try:
            return client.get(key)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None
    
    @classmethod
    def set(cls, key: str, value: str, ttl: int = None) -> bool:
        """设置缓存值"""
        client = cls._get_client()
        if not client:
            return False
        try:
            ttl = ttl or settings.redis_cache_ttl
            client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False
    
    @classmethod
    def delete(cls, key: str) -> bool:
        """删除缓存"""
        client = cls._get_client()
        if not client:
            return False
        try:
            client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")
            return False
    
    @classmethod
    def get_json(cls, key: str) -> Optional[Any]:
        """获取 JSON 缓存"""
        value = cls.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None
    
    @classmethod
    def set_json(cls, key: str, value: Any, ttl: int = None) -> bool:
        """设置 JSON 缓存"""
        try:
            json_str = json.dumps(value, ensure_ascii=False)
            return cls.set(key, json_str, ttl)
        except (TypeError, ValueError) as e:
            logger.warning(f"Cache JSON serialize error: {e}")
            return False
    
    # ============ 业务方法 ============
    
    @classmethod
    def get_today_pool(cls, user_id: str) -> Optional[List[str]]:
        """获取 Today 推荐池缓存"""
        key = f"{cls.PREFIX_FEED_TODAY}{user_id}"
        return cls.get_json(key)
    
    @classmethod
    def set_today_pool(cls, user_id: str, paper_ids: List[str], ttl: int = 3600) -> bool:
        """设置 Today 推荐池缓存 (默认1小时)"""
        key = f"{cls.PREFIX_FEED_TODAY}{user_id}"
        return cls.set_json(key, paper_ids, ttl)
    
    @classmethod
    def get_week_pool(cls, user_id: str) -> Optional[List[str]]:
        """获取 Week 推荐池缓存"""
        key = f"{cls.PREFIX_FEED_WEEK}{user_id}"
        return cls.get_json(key)
    
    @classmethod
    def set_week_pool(cls, user_id: str, paper_ids: List[str], ttl: int = 3600) -> bool:
        """设置 Week 推荐池缓存 (默认1小时)"""
        key = f"{cls.PREFIX_FEED_WEEK}{user_id}"
        return cls.set_json(key, paper_ids, ttl)
    
    @classmethod
    def invalidate_user_feed(cls, user_id: str) -> None:
        """清除用户 Feed 缓存 (用户反馈后调用)"""
        cls.delete(f"{cls.PREFIX_FEED_TODAY}{user_id}")
        cls.delete(f"{cls.PREFIX_FEED_WEEK}{user_id}")
        logger.debug(f"Invalidated feed cache for user {user_id}")
