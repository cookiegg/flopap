"""
会议论文导入服务 - 2025年会议数据导入

支持从 data/paperlists 目录导入2025年会议论文数据
"""

import json
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

import pendulum
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import settings
from app.models import Paper, DataSource, IngestionBatch
from app.models.data_source import DataSourceType


# 2025年支持的会议列表
SUPPORTED_2025_CONFERENCES = {
    'neurips2025': {'name': 'NeurIPS 2025', 'category_prefix': 'neurips'},
    'iclr2025': {'name': 'ICLR 2025', 'category_prefix': 'iclr'},
    'icml2025': {'name': 'ICML 2025', 'category_prefix': 'icml'},
    'cvpr2025': {'name': 'CVPR 2025', 'category_prefix': 'cvpr'},
    'iccv2025': {'name': 'ICCV 2025', 'category_prefix': 'iccv'},
    'aaai2025': {'name': 'AAAI 2025', 'category_prefix': 'aaai'},
    'acl2025': {'name': 'ACL 2025', 'category_prefix': 'acl'},
    'naacl2025': {'name': 'NAACL 2025', 'category_prefix': 'naacl'},
    'coling2025': {'name': 'COLING 2025', 'category_prefix': 'coling'},
    'aistats2025': {'name': 'AISTATS 2025', 'category_prefix': 'aistats'},
    'wacv2025': {'name': 'WACV 2025', 'category_prefix': 'wacv'},
    'www2025': {'name': 'WWW 2025', 'category_prefix': 'www'},
    'corl2025': {'name': 'CoRL 2025', 'category_prefix': 'corl'},
    'colm2025': {'name': 'COLM 2025', 'category_prefix': 'colm'},
    'siggraph2025': {'name': 'SIGGRAPH 2025', 'category_prefix': 'siggraph'},
    'rss2025': {'name': 'RSS 2025', 'category_prefix': 'rss'},
    '3dv2025': {'name': '3DV 2025', 'category_prefix': '3dv'},
    'alt2025': {'name': 'ALT 2025', 'category_prefix': 'alt'},
    'ai4x2025': {'name': 'AI4X 2025', 'category_prefix': 'ai4x'},
}


def get_conference_data_path(conference_id: str) -> Path:
    """获取会议数据文件路径"""
    # 从 conference_id 提取会议名称 (如 neurips2025 -> nips)
    conf_name = conference_id.replace('2025', '')
    if conf_name == 'neurips':
        conf_name = 'nips'  # 特殊处理
    
    data_dir = settings.project_root / 'data' / 'paperlists' / conf_name
    return data_dir / f'{conference_id}.json'


def convert_conference_paper(paper_data: Dict[str, Any], conference_id: str) -> Dict[str, Any]:
    """转换会议论文数据格式"""
    conf_info = SUPPORTED_2025_CONFERENCES[conference_id]
    
    # 生成 arxiv_id (会议论文使用会议ID格式)
    arxiv_id = f"{conference_id}.{paper_data.get('id', str(uuid.uuid4())[:8])}"
    
    # 处理作者信息
    authors_str = paper_data.get('author', '')
    if authors_str:
        author_names = [name.strip() for name in authors_str.split(';') if name.strip()]
        authors = [{'name': name} for name in author_names]
    else:
        authors = [{'name': 'Unknown'}]
    
    # 处理分类信息
    primary_area = paper_data.get('primary_area', 'general')
    categories = [f"{conf_info['category_prefix']}.{primary_area}"]
    
    # 处理日期 (2025年会议统一使用2025年日期)
    submitted_date = pendulum.parse('2025-01-01T00:00:00Z')
    
    # 处理PDF链接
    pdf_url = None
    if 'site' in paper_data and paper_data['site']:
        pdf_url = paper_data['site']
    
    return {
        'arxiv_id': arxiv_id,
        'title': paper_data.get('title', 'Untitled'),
        'summary': paper_data.get('abstract', ''),
        'authors': authors,
        'categories': categories,
        'submitted_date': submitted_date,
        'updated_date': None,
        'pdf_url': pdf_url,
        'html_url': pdf_url,
        'comment': paper_data.get('tldr', ''),
        'doi': None,
        'primary_category': f"{conf_info['category_prefix']}.{primary_area}",
        'source': f'conf/{conference_id}',  # 修改：使用 conf/ 前缀
    }


def import_conference_papers(session: Session, conference_id: str) -> IngestionBatch:
    """导入指定会议的论文数据"""
    
    if conference_id not in SUPPORTED_2025_CONFERENCES:
        raise ValueError(f"不支持的会议: {conference_id}")
    
    conf_info = SUPPORTED_2025_CONFERENCES[conference_id]
    data_path = get_conference_data_path(conference_id)
    
    if not data_path.exists():
        raise FileNotFoundError(f"会议数据文件不存在: {data_path}")
    
    print(f"📚 开始导入 {conf_info['name']} 论文数据...")
    
    # 创建或获取数据源配置
    data_source = session.scalar(select(DataSource).where(DataSource.prefix == conference_id))
    if not data_source:
        data_source = DataSource(
            prefix=conference_id,
            name=conf_info['name'],
            source_type=DataSourceType.STATIC,
            is_active=True
        )
        session.add(data_source)
        session.flush()
    
    # 创建摄取批次
    batch = IngestionBatch(
        source_date=pendulum.now().date(),
        fetched_at=pendulum.now(),
        item_count=0,
        query=f"conference:{conference_id}",
        notes=f"Import {conf_info['name']} papers from JSON file"
    )
    session.add(batch)
    session.flush()
    
    # 读取JSON数据
    with open(data_path, 'r', encoding='utf-8') as f:
        papers_data = json.load(f)
    
    print(f"📄 找到 {len(papers_data)} 篇论文")
    
    # 导入论文数据
    imported_count = 0
    skipped_count = 0
    
    for paper_data in papers_data:
        try:
            converted_data = convert_conference_paper(paper_data, conference_id)
            
            # 检查是否已存在
            existing = session.scalar(
                select(Paper).where(Paper.arxiv_id == converted_data['arxiv_id'])
            )
            
            if existing is None:
                paper = Paper(
                    arxiv_id=converted_data['arxiv_id'],
                    title=converted_data['title'],
                    summary=converted_data['summary'],
                    authors=converted_data['authors'],
                    categories=converted_data['categories'],
                    submitted_date=converted_data['submitted_date'],
                    updated_date=converted_data['updated_date'],
                    pdf_url=converted_data['pdf_url'],
                    html_url=converted_data['html_url'],
                    comment=converted_data['comment'],
                    doi=converted_data['doi'],
                    primary_category=converted_data['primary_category'],
                    source=converted_data['source'],
                    ingestion_batch_id=batch.id,
                )
                session.add(paper)
                imported_count += 1
            else:
                skipped_count += 1
                
        except Exception as e:
            print(f"⚠️  跳过论文 {paper_data.get('id', 'unknown')}: {e}")
            skipped_count += 1
    
    # 更新批次信息
    batch.item_count = imported_count
    session.commit()
    
    print(f"✅ 导入完成: {imported_count} 篇新论文, {skipped_count} 篇跳过")
    return batch


def import_all_2025_conferences(session: Session) -> Dict[str, IngestionBatch]:
    """导入所有2025年会议数据"""
    results = {}
    
    print("🏛️ 开始导入所有2025年会议数据...")
    
    for conference_id in SUPPORTED_2025_CONFERENCES:
        try:
            batch = import_conference_papers(session, conference_id)
            results[conference_id] = batch
            print(f"✅ {conference_id}: {batch.item_count} 篇论文")
        except Exception as e:
            print(f"❌ {conference_id}: {e}")
            results[conference_id] = None
    
    return results


def get_available_2025_conferences() -> List[Dict[str, str]]:
    """获取可用的2025年会议列表"""
    available = []
    
    for conference_id, conf_info in SUPPORTED_2025_CONFERENCES.items():
        data_path = get_conference_data_path(conference_id)
        if data_path.exists():
            available.append({
                'id': conference_id,
                'name': conf_info['name'],
                'data_path': str(data_path),
                'file_size': data_path.stat().st_size
            })
    
    return available
