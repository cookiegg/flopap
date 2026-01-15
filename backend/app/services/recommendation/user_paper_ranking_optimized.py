"""
优化版论文排序生成 - 批量查询优化
"""
from __future__ import annotations

from typing import List, Dict, Optional
from uuid import UUID
import time

import numpy as np
import pendulum
from sqlalchemy import select
from sqlalchemy.orm import Session
from loguru import logger

from app.core.config import settings
from app.models import Paper, PaperEmbedding, UserProfile
from app.services.recommendation.user_paper_ranking import ScoredPaper


def generate_paper_ranking_optimized(
    session: Session,
    paper_ids: List[UUID],
    user_id: str,
    algorithm: str = 'default'
) -> List[ScoredPaper]:
    """
    优化版本的论文排序生成 - 使用批量查询
    
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
    
    start_time = time.time()
    
    # 1. 批量获取所有论文数据
    papers_dict = {p.id: p for p in session.execute(
        select(Paper).where(Paper.id.in_(paper_ids))
    ).scalars().all()}
    
    papers_query_time = time.time() - start_time
    
    # 2. 批量获取所有embeddings
    embeddings_start = time.time()
    embeddings_dict = {e.paper_id: e for e in session.execute(
        select(PaperEmbedding).where(
            PaperEmbedding.paper_id.in_(paper_ids),
            PaperEmbedding.model_name == settings.embedding_model_name
        )
    ).scalars().all()}
    
    embeddings_query_time = time.time() - embeddings_start
    
    # 3. 一次性获取用户数据
    user_start = time.time()
    user_profile = session.get(UserProfile, user_id)
    user_vector = _get_user_profile_vector_cached(session, user_id)
    user_query_time = time.time() - user_start
    
    # 4. 批量评分
    scoring_start = time.time()
    scored_papers = []
    
    # 预计算时间相关数据
    now = pendulum.now("UTC")
    
    for paper_id in paper_ids:
        paper = papers_dict.get(paper_id)
        if not paper:
            continue
            
        embedding = embeddings_dict.get(paper_id)
        score = _calculate_score_optimized(paper, embedding, user_profile, user_vector, now)
        
        scored_papers.append(ScoredPaper(
            paper_id=str(paper_id),
            score=score
        ))
    
    scoring_time = time.time() - scoring_start
    
    # 5. 排序
    sort_start = time.time()
    scored_papers.sort(key=lambda x: x.score, reverse=True)
    sort_time = time.time() - sort_start
    
    total_time = time.time() - start_time
    
    logger.info(f"用户 {user_id} 优化排序完成: {len(scored_papers)} 篇")
    logger.debug(f"性能分析 - 总计:{total_time:.2f}s 论文:{papers_query_time:.2f}s "
                f"嵌入:{embeddings_query_time:.2f}s 用户:{user_query_time:.2f}s "
                f"评分:{scoring_time:.2f}s 排序:{sort_time:.2f}s")
    
    return scored_papers


def _get_user_profile_vector_cached(session: Session, user_id: str) -> Optional[np.ndarray]:
    """获取用户画像向量 - 带缓存优化"""
    # 这里可以添加缓存逻辑
    from app.algorithms.scoring import _get_user_profile_vector
    return _get_user_profile_vector(session, user_id)


def _calculate_score_optimized(
    paper: Paper,
    embedding: Optional[PaperEmbedding],
    user_profile: Optional[UserProfile],
    user_vector: Optional[np.ndarray],
    current_time: pendulum.DateTime
) -> float:
    """
    优化版评分计算 - 减少重复计算
    """
    # 计算时间衰减 (预计算current_time)
    recency_days = max((current_time - pendulum.instance(paper.submitted_date)).days, 0)
    recency_bonus = max(0.0, 1.0 - min(recency_days / 30.0, 1.0))
    
    if user_vector is not None and embedding:
        # 策略1: 使用embedding相似度
        try:
            paper_vector = np.array(embedding.embedding)
            similarity = np.dot(user_vector, paper_vector) / (
                np.linalg.norm(user_vector) * np.linalg.norm(paper_vector)
            )
            base_score = max(0.0, similarity)
        except Exception:
            base_score = 0.5
    elif user_profile and user_profile.interested_categories:
        # 策略2: 使用类别匹配
        user_categories = set(user_profile.interested_categories)
        paper_categories = set(paper.categories or [])
        
        if user_categories and paper_categories:
            overlap = len(user_categories.intersection(paper_categories))
            base_score = min(overlap / len(user_categories), 1.0)
        else:
            base_score = 0.3
    else:
        # 策略3: 随机基线
        base_score = 0.5
    
    # 组合分数
    final_score = base_score + recency_bonus
    return min(final_score, 2.0)


# 替换原有的生成函数
def patch_ranking_service():
    """
    猴子补丁 - 替换原有的排序生成函数
    """
    import app.services.recommendation.user_paper_ranking as ranking_module
    
    # 备份原函数
    ranking_module._original_generate_paper_ranking = ranking_module.generate_paper_ranking
    
    # 替换为优化版本
    ranking_module.generate_paper_ranking = generate_paper_ranking_optimized
    
    logger.info("已启用优化版论文排序算法")


def restore_ranking_service():
    """
    恢复原有的排序生成函数
    """
    import app.services.recommendation.user_paper_ranking as ranking_module
    
    if hasattr(ranking_module, '_original_generate_paper_ranking'):
        ranking_module.generate_paper_ranking = ranking_module._original_generate_paper_ranking
        logger.info("已恢复原版论文排序算法")
