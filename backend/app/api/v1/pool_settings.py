"""数据源池设置 API"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_user_id
from app.models.data_source_pool_settings import DataSourcePoolSettings

router = APIRouter()


class PoolSettingsRequest(BaseModel):
    """池设置请求"""
    pool_ratio: float = Field(default=0.2, ge=0.0, le=1.0, description="推荐池比例 (0.0-1.0)")
    max_pool_size: int = Field(default=2000, ge=10, le=10000, description="最大池大小")
    show_mode: str = Field(default='pool', pattern='^(pool|all)$', description="显示模式: pool=仅推荐池, all=全部")
    filter_no_content: bool = Field(default=True, description="是否过滤无内容论文")


class PoolSettingsResponse(BaseModel):
    """池设置响应"""
    user_id: str
    source_key: str
    pool_ratio: float
    max_pool_size: int
    show_mode: str
    filter_no_content: bool
    updated_at: str


def get_or_create_settings(db: Session, user_id: str, source_key: str) -> DataSourcePoolSettings:
    """获取或创建数据源池设置"""
    setting = db.query(DataSourcePoolSettings).filter(
        DataSourcePoolSettings.user_id == user_id,
        DataSourcePoolSettings.source_key == source_key
    ).first()
    
    if not setting:
        setting = DataSourcePoolSettings(
            user_id=user_id,
            source_key=source_key,
            pool_ratio=0.2,
            max_pool_size=2000,
            show_mode='pool',
            filter_no_content=True
        )
        db.add(setting)
        db.commit()
        db.refresh(setting)
    
    return setting


@router.get("/{source_key}", response_model=PoolSettingsResponse)
async def get_pool_settings(
    source_key: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id)
):
    """获取指定数据源的池设置"""
    setting = get_or_create_settings(db, user_id, source_key)
    
    return PoolSettingsResponse(
        user_id=setting.user_id,
        source_key=setting.source_key,
        pool_ratio=setting.pool_ratio,
        max_pool_size=setting.max_pool_size,
        show_mode=setting.show_mode,
        filter_no_content=setting.filter_no_content,
        updated_at=setting.updated_at.isoformat() if setting.updated_at else datetime.utcnow().isoformat()
    )


@router.put("/{source_key}")
async def update_pool_settings(
    source_key: str,
    req: PoolSettingsRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id)
):
    """更新指定数据源的池设置"""
    setting = get_or_create_settings(db, user_id, source_key)
    
    setting.pool_ratio = req.pool_ratio
    setting.max_pool_size = req.max_pool_size
    setting.show_mode = req.show_mode
    setting.filter_no_content = req.filter_no_content
    setting.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "message": "Pool settings updated",
        "source_key": source_key,
        "settings": {
            "pool_ratio": setting.pool_ratio,
            "max_pool_size": setting.max_pool_size,
            "show_mode": setting.show_mode,
            "filter_no_content": setting.filter_no_content
        }
    }


@router.get("")
async def list_all_pool_settings(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id)
):
    """获取用户所有数据源的池设置"""
    settings = db.query(DataSourcePoolSettings).filter(
        DataSourcePoolSettings.user_id == user_id
    ).all()
    
    return {
        "user_id": user_id,
        "settings": [
            {
                "source_key": s.source_key,
                "pool_ratio": s.pool_ratio,
                "max_pool_size": s.max_pool_size,
                "show_mode": s.show_mode,
                "filter_no_content": s.filter_no_content
            }
            for s in settings
        ]
    }
