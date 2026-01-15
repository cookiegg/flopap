from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

from app.core.config import settings

# 同步引擎（保持向后兼容）
engine = create_engine(
    settings.database_url, 
    pool_pre_ping=True, 
    future=True,
    pool_size=20,
    max_overflow=0
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# 异步引擎（Framework V2使用）
def _convert_to_async_url(sync_url: str) -> str:
    """Convert sync database URL to async version"""
    if "postgresql+psycopg://" in sync_url:
        return sync_url.replace("postgresql+psycopg://", "postgresql+asyncpg://")
    elif "postgresql://" in sync_url:
        return sync_url.replace("postgresql://", "postgresql+asyncpg://")
    elif "postgresql+psycopg2://" in sync_url:
        return sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
    else:
        return sync_url

async_database_url = _convert_to_async_url(settings.database_url)
async_engine = create_async_engine(
    async_database_url, 
    pool_pre_ping=True, 
    future=True,
    pool_size=20,
    max_overflow=0
)
async_session_factory = async_sessionmaker(
    bind=async_engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False
)


def get_session():
    with SessionLocal() as session:
        yield session


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
