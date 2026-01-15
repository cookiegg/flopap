"""
Redis 连接管理
"""
import redis
from functools import lru_cache
from loguru import logger

from app.core.config import settings


class RedisClient:
    """Redis 客户端封装"""
    
    _instance: redis.Redis | None = None
    
    @classmethod
    def get_client(cls) -> redis.Redis | None:
        """获取 Redis 客户端实例"""
        if cls._instance is None:
            try:
                cls._instance = redis.Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    db=settings.redis_db,
                    password=settings.redis_password or None,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                # 测试连接
                cls._instance.ping()
                logger.info(f"Redis connected: {settings.redis_host}:{settings.redis_port}")
            except redis.ConnectionError as e:
                logger.warning(f"Redis connection failed: {e}. Caching disabled.")
                cls._instance = None
            except Exception as e:
                logger.warning(f"Redis error: {e}. Caching disabled.")
                cls._instance = None
        return cls._instance
    
    @classmethod
    def close(cls):
        """关闭 Redis 连接"""
        if cls._instance:
            cls._instance.close()
            cls._instance = None
            logger.info("Redis connection closed")


@lru_cache
def get_redis() -> redis.Redis | None:
    """获取 Redis 客户端 (FastAPI 依赖注入用)"""
    return RedisClient.get_client()
