"""
翻译生成服务 - 改进版本（可选）
提供与AI解读服务一致的双接口设计
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from loguru import logger
from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Paper, PaperTranslation
from app.services.llm import distribute_papers, get_deepseek_clients


def translate_single_paper(client: OpenAI, paper: Paper) -> Optional[Tuple[str, str]]:
    """翻译单篇论文的标题和摘要"""
    try:
        prompt = f"""请将以下英文学术论文的标题和摘要翻译成中文：

标题：{paper.title}
摘要：{paper.summary}

要求：
1. 保持学术性和准确性
2. 使用规范的中文表达
3. 保留专业术语的准确性
4. 分别返回翻译后的标题和摘要

请按以下格式返回：
标题：[翻译后的标题]
摘要：[翻译后的摘要]"""

        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[
                {"role": "system", "content": "你是专业的学术论文翻译助手，擅长将英文论文准确翻译成中文。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )
        
        result = response.choices[0].message.content.strip()
        
        # 解析返回结果
        lines = result.split('\n')
        title_zh = ""
        summary_zh = ""
        
        for line in lines:
            if line.startswith('标题：'):
                title_zh = line[3:].strip()
            elif line.startswith('摘要：'):
                summary_zh = line[3:].strip()
        
        if title_zh and summary_zh:
            return (title_zh, summary_zh)
        else:
            logger.warning("翻译结果解析失败: {}", paper.title[:50])
            return None
            
    except Exception as e:
        logger.error("翻译失败: paper={}, error={}", paper.title[:50], str(e))
        return None


# 核心翻译函数（无数据库依赖）
def generate_translations_for_papers(
    papers: List[Paper],
    max_workers: int = 30
) -> Dict[UUID, Tuple[str, str]]:
    """
    为论文对象列表生成翻译（纯函数，无数据库依赖）
    
    Args:
        papers: 论文对象列表
        max_workers: 并发线程数
        
    Returns:
        {paper_id: (title_zh, summary_zh)} 成功翻译的结果
    """
    if not papers:
        return {}
    
    logger.info("开始翻译 {} 篇论文", len(papers))
    
    # 获取LLM客户端并分发论文
    clients = get_deepseek_clients()
    paper_groups = distribute_papers(papers, len(clients))
    
    translation_results = {}
    
    # 并发翻译
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_paper = {}
        
        for i, (client, paper_group) in enumerate(zip(clients, paper_groups)):
            for paper in paper_group:
                future = executor.submit(translate_single_paper, client, paper)
                future_to_paper[future] = paper
        
        # 收集结果
        for future in as_completed(future_to_paper):
            paper = future_to_paper[future]
            try:
                result = future.result()
                if result:
                    translation_results[paper.id] = result
                    logger.debug("翻译成功: {}", paper.title[:50])
                else:
                    logger.warning("翻译失败: {}", paper.title[:50])
            except Exception as e:
                logger.error("翻译异常: paper={}, error={}", paper.title[:50], str(e))
    
    logger.info("翻译完成: 成功 {} 篇，失败 {} 篇", 
                len(translation_results), 
                len(papers) - len(translation_results))
    
    return translation_results


# 数据库操作函数
def save_translations_to_db(
    session: Session,
    translation_results: Dict[UUID, Tuple[str, str]],
    model_name: str = "deepseek-reasoner"
) -> int:
    """
    保存翻译结果到数据库
    
    Args:
        session: 数据库会话
        translation_results: 翻译结果字典
        model_name: 使用的模型名称
        
    Returns:
        成功保存的数量
    """
    if not translation_results:
        return 0
    
    saved_count = 0
    
    for paper_id, (title_zh, summary_zh) in translation_results.items():
        try:
            # 检查是否已存在翻译记录
            existing = session.scalar(
                select(PaperTranslation).where(PaperTranslation.paper_id == paper_id)
            )
            
            if existing:
                # 更新现有记录
                existing.title_zh = title_zh
                existing.summary_zh = summary_zh
                existing.model_name = model_name
            else:
                # 创建新记录
                translation = PaperTranslation(
                    paper_id=paper_id,
                    title_zh=title_zh,
                    summary_zh=summary_zh,
                    model_name=model_name
                )
                session.add(translation)
            
            saved_count += 1
            
        except Exception as e:
            logger.error("保存翻译失败: paper_id={}, error={}", paper_id, str(e))
    
    try:
        session.commit()
        logger.info("翻译结果保存完成: {} 篇", saved_count)
    except Exception as e:
        session.rollback()
        logger.error("翻译结果保存失败: {}", str(e))
        saved_count = 0
    
    return saved_count


# 便捷接口1：基于论文对象（推荐用于已有Paper对象的场景）
def generate_and_save_translations(
    session: Session,
    papers: List[Paper],
    max_workers: int = 30,
    model_name: str = "deepseek-reasoner"
) -> int:
    """
    为论文对象生成翻译并保存（推荐接口）
    
    Args:
        session: 数据库会话
        papers: 论文对象列表
        max_workers: 并发线程数
        model_name: 模型名称
        
    Returns:
        成功处理的论文数量
    """
    # 生成翻译
    translation_results = generate_translations_for_papers(papers, max_workers)
    
    # 保存结果
    saved_count = save_translations_to_db(session, translation_results, model_name)
    
    return saved_count


# 便捷接口2：基于论文ID（兼容现有代码）
def generate_and_save_translations_by_ids(
    session: Session,
    paper_ids: List[UUID],
    max_workers: int = 30,
    force_retranslate: bool = False,
    model_name: str = "deepseek-reasoner"
) -> int:
    """
    根据论文ID生成翻译并保存（兼容接口）
    
    Args:
        session: 数据库会话
        paper_ids: 论文ID列表
        max_workers: 并发线程数
        force_retranslate: 是否强制重新翻译
        model_name: 模型名称
        
    Returns:
        成功处理的论文数量
    """
    if not paper_ids:
        logger.info("没有需要翻译的论文")
        return 0
    
    # 获取论文对象
    papers_stmt = select(Paper).where(Paper.id.in_(paper_ids))
    papers = list(session.execute(papers_stmt).scalars())
    
    if not papers:
        logger.warning("未找到指定的论文")
        return 0
    
    # 过滤已翻译的论文（除非强制重新翻译）
    if not force_retranslate:
        papers_to_process = []
        for paper in papers:
            existing = session.scalar(
                select(PaperTranslation).where(PaperTranslation.paper_id == paper.id)
            )
            if not existing or not existing.title_zh or not existing.summary_zh:
                papers_to_process.append(paper)
        
        logger.info("过滤后需要翻译的论文: {} 篇", len(papers_to_process))
        papers = papers_to_process
    
    if not papers:
        logger.info("所有论文都已翻译完成")
        return 0
    
    # 调用基于对象的接口
    return generate_and_save_translations(session, papers, max_workers, model_name)


# 工具函数
def get_papers_missing_translation(
    session: Session,
    paper_ids: List[UUID]
) -> List[UUID]:
    """
    获取缺少翻译的论文ID列表
    
    Args:
        session: 数据库会话
        paper_ids: 要检查的论文ID列表
        
    Returns:
        缺少翻译的论文ID列表
    """
    missing_ids = []
    
    for paper_id in paper_ids:
        existing = session.scalar(
            select(PaperTranslation).where(PaperTranslation.paper_id == paper_id)
        )
        if not existing or not existing.title_zh or not existing.summary_zh:
            missing_ids.append(paper_id)
    
    return missing_ids
