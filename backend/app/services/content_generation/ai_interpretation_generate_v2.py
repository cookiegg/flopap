"""
AI解读生成服务 - 改进版本
提供两种接口：基于ID和基于对象
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Union
from uuid import UUID

from loguru import logger
from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Paper, PaperInterpretation
from app.services.llm import distribute_papers, get_deepseek_clients
from app.services.content_generation.ai_interpretation_unified import generate_ai_interpretation_unified


# 核心生成函数（无数据库依赖）
def generate_interpretations_for_papers(
    papers: List[Paper],
    max_workers: int = 20
) -> Dict[UUID, str]:
    """
    为论文对象列表生成AI解读（纯函数，无数据库依赖）
    
    Args:
        papers: 论文对象列表
        max_workers: 并发线程数
        
    Returns:
        {paper_id: ai_interpretation} 成功生成的结果
    """
    if not papers:
        return {}
    
    logger.info("开始生成AI解读 {} 篇论文", len(papers))
    
    # 获取LLM客户端并分发论文
    clients = get_deepseek_clients()
    paper_groups = distribute_papers(papers, len(clients))
    
    interpretation_results = {}
    
    # 并发生成AI解读
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_paper = {}
        
        for i, (client, paper_group) in enumerate(zip(clients, paper_groups)):
            for paper in paper_group:
                future = executor.submit(generate_ai_interpretation_unified, client, paper)
                future_to_paper[future] = paper
        
        # 收集结果
        for future in as_completed(future_to_paper):
            paper = future_to_paper[future]
            try:
                result = future.result()
                if result:
                    interpretation_results[paper.id] = result
                    logger.debug("AI解读生成成功: {}", paper.title[:50])
                else:
                    logger.warning("AI解读生成失败: {}", paper.title[:50])
            except Exception as e:
                logger.error("AI解读生成异常: paper={}, error={}", paper.title[:50], str(e))
    
    logger.info("AI解读生成完成: 成功 {} 篇，失败 {} 篇", 
                len(interpretation_results), 
                len(papers) - len(interpretation_results))
    
    return interpretation_results


# 数据库操作函数
def save_interpretations_to_db(
    session: Session,
    interpretation_results: Dict[UUID, str],
    model_name: str = "deepseek-reasoner"
) -> int:
    """
    保存AI解读结果到数据库
    
    Args:
        session: 数据库会话
        interpretation_results: AI解读结果字典
        model_name: 使用的模型名称
        
    Returns:
        成功保存的数量
    """
    if not interpretation_results:
        return 0
    
    saved_count = 0
    
    for paper_id, ai_interpretation in interpretation_results.items():
        try:
            # 检查是否已存在解读记录
            existing = session.scalar(
                select(PaperInterpretation).where(PaperInterpretation.paper_id == paper_id)
            )
            
            if existing:
                # 更新现有记录
                existing.interpretation = ai_interpretation
                existing.model_name = model_name
            else:
                # 创建新记录
                interpretation_record = PaperInterpretation(
                    paper_id=paper_id,
                    interpretation=ai_interpretation,
                    language="zh",
                    model_name=model_name
                )
                session.add(interpretation_record)
            
            saved_count += 1
            
        except Exception as e:
            logger.error("保存AI解读失败: paper_id={}, error={}", paper_id, str(e))
    
    try:
        session.commit()
        logger.info("AI解读结果保存完成: {} 篇", saved_count)
    except Exception as e:
        session.rollback()
        logger.error("AI解读结果保存失败: {}", str(e))
        saved_count = 0
    
    return saved_count


# 便捷接口1：基于论文对象（推荐用于已有Paper对象的场景）
def generate_and_save_interpretations(
    session: Session,
    papers: List[Paper],
    max_workers: int = 20,
    model_name: str = "deepseek-reasoner"
) -> int:
    """
    为论文对象生成AI解读并保存（推荐接口）
    
    Args:
        session: 数据库会话
        papers: 论文对象列表
        max_workers: 并发线程数
        model_name: 模型名称
        
    Returns:
        成功处理的论文数量
    """
    # 生成AI解读
    interpretation_results = generate_interpretations_for_papers(papers, max_workers)
    
    # 保存结果
    saved_count = save_interpretations_to_db(session, interpretation_results, model_name)
    
    return saved_count


# 便捷接口2：基于论文ID（兼容现有代码）
def generate_and_save_interpretations_by_ids(
    session: Session,
    paper_ids: List[UUID],
    max_workers: int = 20,
    force_regenerate: bool = False,
    model_name: str = "deepseek-reasoner"
) -> int:
    """
    根据论文ID生成AI解读并保存（兼容接口）
    
    Args:
        session: 数据库会话
        paper_ids: 论文ID列表
        max_workers: 并发线程数
        force_regenerate: 是否强制重新生成
        model_name: 模型名称
        
    Returns:
        成功处理的论文数量
    """
    if not paper_ids:
        logger.info("没有需要生成AI解读的论文")
        return 0
    
    # 获取论文对象
    papers_stmt = select(Paper).where(Paper.id.in_(paper_ids))
    papers = list(session.execute(papers_stmt).scalars())
    
    if not papers:
        logger.warning("未找到指定的论文")
        return 0
    
    # 过滤已有AI解读的论文（除非强制重新生成）
    if not force_regenerate:
        papers_to_process = []
        for paper in papers:
            existing = session.scalar(
                select(PaperInterpretation).where(PaperInterpretation.paper_id == paper.id)
            )
            if not existing:
                papers_to_process.append(paper)
        
        logger.info("过滤后需要生成AI解读的论文: {} 篇", len(papers_to_process))
        papers = papers_to_process
    
    if not papers:
        logger.info("所有论文都已有AI解读")
        return 0
    
    # 调用基于对象的接口
    return generate_and_save_interpretations(session, papers, max_workers, model_name)


# 工具函数
def get_papers_missing_interpretation(
    session: Session,
    paper_ids: List[UUID]
) -> List[UUID]:
    """
    获取缺少AI解读的论文ID列表
    
    Args:
        session: 数据库会话
        paper_ids: 要检查的论文ID列表
        
    Returns:
        缺少AI解读的论文ID列表
    """
    missing_ids = []
    
    for paper_id in paper_ids:
        existing = session.scalar(
            select(PaperInterpretation).where(PaperInterpretation.paper_id == paper_id)
        )
        if not existing or not existing.interpretation:
            missing_ids.append(paper_id)
    
    return missing_ids
