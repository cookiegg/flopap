"""
Data Sources API - 动态数据源管理

提供:
- GET /data-sources - 返回所有已激活的数据源列表
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func, distinct
from typing import List, Optional
from pydantic import BaseModel
import logging

from app.api import deps
from app.models import Paper, DataSource as DataSourceModel
from app.services.data_ingestion.conference_import import SUPPORTED_2025_CONFERENCES

router = APIRouter()
logger = logging.getLogger(__name__)


class SubSource(BaseModel):
    id: str
    name: str


class DataSourceInfo(BaseModel):
    id: str
    name: str
    type: str  # 'streaming' or 'conference'
    paper_count: Optional[int] = None
    sub_sources: Optional[List[SubSource]] = None


class DataSourcesResponse(BaseModel):
    data_sources: List[DataSourceInfo]


@router.get("", response_model=DataSourcesResponse)
async def get_data_sources(
    db: Session = Depends(deps.get_db)
):
    """
    获取所有可用的数据源列表
    
    包括:
    - arxiv: 每日ArXiv论文流
    - 已导入的会议数据源 (neurips2025, iclr2025 等)
    """
    data_sources = []
    
    # 1. ArXiv数据源 (始终可用)
    arxiv_source = DataSourceInfo(
        id="arxiv",
        name="ArXiv Daily",
        type="streaming",
        sub_sources=[
            SubSource(id="today", name="Today"),
            SubSource(id="week", name="This Week")
        ]
    )
    data_sources.append(arxiv_source)
    
    # 2. 已导入的会议数据源
    # 查询数据库中有论文的会议
    conference_sources = db.execute(
        select(
            Paper.source,
            func.count(Paper.id).label('count')
        ).where(
            Paper.source.like('conf/%')
        ).group_by(Paper.source)
    ).all()
    
    for source_row in conference_sources:
        source_key = source_row[0]  # e.g., 'conf/neurips2025'
        paper_count = source_row[1]
        
        # 提取会议ID
        if source_key.startswith('conf/'):
            conf_id = source_key[5:]  # 去掉 'conf/' 前缀
        else:
            conf_id = source_key
        
        # 获取会议名称
        conf_info = SUPPORTED_2025_CONFERENCES.get(conf_id, {})
        conf_name = conf_info.get('name', conf_id.upper())
        
        conf_source = DataSourceInfo(
            id=conf_id,
            name=conf_name,
            type="conference",
            paper_count=paper_count
        )
        data_sources.append(conf_source)
    
    return DataSourcesResponse(data_sources=data_sources)


@router.get("/available-conferences")
async def get_available_conferences():
    """
    获取所有可用的会议配置 (包括未导入的)
    
    返回 data/paperlists 中配置的所有会议
    """
    from app.services.data_ingestion.conference_import import get_available_2025_conferences
    
    available = get_available_2025_conferences()
    
    return {
        "conferences": [
            {
                "id": conf['id'],
                "name": conf['name'],
                "file_size": conf['file_size'],
                "file_path": str(conf['file_path'])
            }
            for conf in available
        ]
    }
