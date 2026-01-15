"""
论文排序服务
功能：基于用户画像对论文列表进行排序
输入：论文列表 + 用户ID
输出：论文排序表
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List
from uuid import UUID

from loguru import logger
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Paper, PaperEmbedding
from app.algorithms.scoring import get_scoring_algorithm


@dataclass
class ScoredPaper:
    """评分后的论文"""
    paper_id: str
    score: float


def generate_paper_ranking(
    session: Session,
    paper_ids: List[UUID],
    user_id: str,
    algorithm: str = 'default'
) -> List[ScoredPaper]:
    """
    基于用户画像生成论文排序表 - 优化版本
    
    Args:
        session: 数据库会话
        paper_ids: 论文ID列表
        user_id: 用户ID
        algorithm: 评分算法
        
    Returns:
        评分排序后的论文列表
    """
    if not paper_ids:
        logger.warning(f"用户 {user_id} 输入论文ID列表为空")
        return []

    import time
    start_time = time.time()

    # 批量获取所有论文数据
    from sqlalchemy import select
    papers_dict = {p.id: p for p in session.execute(
        select(Paper).where(Paper.id.in_(paper_ids))
    ).scalars().all()}

    # 批量获取所有embeddings
    embeddings_dict = {e.paper_id: e for e in session.execute(
        select(PaperEmbedding).where(
            PaperEmbedding.paper_id.in_(paper_ids),
            PaperEmbedding.model_name == settings.embedding_model_name
        )
    ).scalars().all()}

    # 一次性获取用户数据
    from app.models import UserProfile
    user_profile = session.get(UserProfile, user_id)
    
    # 获取评分算法
    scoring_func = get_scoring_algorithm(algorithm)

    # 批量评分
    scored_papers = []
    for paper_id in paper_ids:
        paper = papers_dict.get(paper_id)
        if paper:
            score = scoring_func(session, paper, user_id)
            scored_papers.append(ScoredPaper(
                paper_id=str(paper_id),
                score=score
            ))

    # 按分数排序（降序）
    scored_papers.sort(key=lambda x: x.score, reverse=True)

    total_time = time.time() - start_time
    logger.info(f"用户 {user_id} 论文排序完成: {len(scored_papers)} 篇 (优化版 {total_time:.1f}秒)")
    return scored_papers


def get_top_papers(
    scored_papers: List[ScoredPaper],
    count: int
) -> List[ScoredPaper]:
    """
    获取排序表中的前N篇论文
    
    Args:
        scored_papers: 评分排序后的论文列表
        count: 需要的论文数量
        
    Returns:
        前N篇论文
    """
    return scored_papers[:count]


def filter_by_score(
    scored_papers: List[ScoredPaper],
    min_score: float
) -> List[ScoredPaper]:
    """
    按最低分数筛选论文
    
    Args:
        scored_papers: 评分排序后的论文列表
        min_score: 最低分数阈值
        
    Returns:
        符合分数要求的论文列表
    """
    return [sp for sp in scored_papers if sp.score >= min_score]


def get_paper_ids_ranked(
    scored_papers: List[ScoredPaper]
) -> List[str]:
    """
    从排序表中提取论文ID列表
    
    Args:
        scored_papers: 评分排序后的论文列表
        
    Returns:
        排序后的论文ID列表
    """
    return [sp.paper_id for sp in scored_papers]
