"""
论文评分算法
"""
from __future__ import annotations

import random
from typing import Callable

import numpy as np
import pendulum
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Paper, PaperEmbedding, UserFeedback, UserProfile


def default_scoring_algorithm(session: Session, paper: Paper, user_id: str) -> float:
    """
    默认评分算法 - 复用原有的三策略算法
    
    Args:
        session: 数据库会话
        paper: 论文对象
        user_id: 用户ID
        
    Returns:
        论文评分 (0.0 - 2.0)
    """
    # 获取用户向量
    user_vector = _get_user_profile_vector(session, user_id)
    
    # 获取用户画像
    user_profile = session.get(UserProfile, user_id)
    
    # 计算时间衰减
    now = pendulum.now("UTC")
    recency_days = max((now - pendulum.instance(paper.submitted_date)).days, 0)
    recency_bonus = max(0.0, 1.0 - min(recency_days / 30.0, 1.0))
    
    if user_vector is not None:
        # 策略1: 有用户反馈数据 - 使用embedding相似度
        paper_embedding = session.execute(
            select(PaperEmbedding).where(
                PaperEmbedding.paper_id == paper.id,
                PaperEmbedding.model_name == settings.embedding_model_name
            )
        ).scalar_one_or_none()
        
        if paper_embedding:
            vector = np.array(paper_embedding.vector, dtype=float)
            similarity = float(np.dot(user_vector, vector))
            score = 0.5 + similarity + recency_bonus
        else:
            score = 0.5 + recency_bonus
            
    elif user_profile and (user_profile.interested_categories or user_profile.research_keywords):
        # 策略2: 有用户画像 - 基于领域和关键词匹配
        category_score = _calculate_category_match_score(paper, user_profile)
        keyword_score = _calculate_keyword_match_score(paper, user_profile)
        score = 0.3 + category_score + keyword_score + recency_bonus * 0.5
        
    else:
        # 策略3: 新用户 - 随机推荐
        recency_bonus = recency_bonus * 0.3
        random_score = random.random()
        score = random_score + recency_bonus
    
    return score


def embedding_similarity_algorithm(session: Session, paper: Paper, user_id: str) -> float:
    """
    纯embedding相似度算法
    
    Args:
        session: 数据库会话
        paper: 论文对象
        user_id: 用户ID
        
    Returns:
        相似度评分 (0.0 - 1.0)
    """
    user_vector = _get_user_profile_vector(session, user_id)
    
    if user_vector is None:
        return 0.0
    
    paper_embedding = session.execute(
        select(PaperEmbedding).where(
            PaperEmbedding.paper_id == paper.id,
            PaperEmbedding.model_name == settings.embedding_model_name
        )
    ).scalar_one_or_none()
    
    if not paper_embedding:
        return 0.0
    
    vector = np.array(paper_embedding.vector, dtype=float)
    similarity = float(np.dot(user_vector, vector))
    
    # 归一化到 0-1 范围
    return max(0.0, min(1.0, (similarity + 1) / 2))


def category_matching_algorithm(session: Session, paper: Paper, user_id: str) -> float:
    """
    基于分类匹配的算法
    
    Args:
        session: 数据库会话
        paper: 论文对象
        user_id: 用户ID
        
    Returns:
        匹配评分 (0.0 - 1.0)
    """
    user_profile = session.get(UserProfile, user_id)
    
    if not user_profile or not user_profile.interested_categories:
        return 0.0
    
    return _calculate_category_match_score(paper, user_profile) * 2  # 放大到0-1范围


def time_decay_algorithm(session: Session, paper: Paper, user_id: str) -> float:
    """
    基于时间衰减的算法
    
    Args:
        session: 数据库会话
        paper: 论文对象
        user_id: 用户ID
        
    Returns:
        时间评分 (0.0 - 1.0)
    """
    now = pendulum.now("UTC")
    recency_days = max((now - pendulum.instance(paper.submitted_date)).days, 0)
    
    # 30天内的论文获得递减评分
    return max(0.0, 1.0 - min(recency_days / 30.0, 1.0))


# 辅助函数
def _get_user_profile_vector(session: Session, user_id: str) -> np.ndarray:
    """获取用户偏好向量"""
    from sqlalchemy import cast, String
    
    positives_subq = (
        select(PaperEmbedding.vector)
        .join(Paper, PaperEmbedding.paper_id == Paper.id)
        .join(
            UserFeedback,
            (UserFeedback.paper_id == Paper.id) &
            (UserFeedback.user_id == user_id) &
            (cast(UserFeedback.feedback_type, String).in_(["like", "bookmark"]))
        )
        .where(PaperEmbedding.model_name == settings.embedding_model_name)
    )
    
    vectors = [np.array(vec, dtype=float) for vec in session.execute(positives_subq).scalars().all() if vec]
    
    if not vectors:
        return None
    
    stacked = np.vstack(vectors)
    profile = stacked.mean(axis=0)
    norm = np.linalg.norm(profile)
    
    if norm == 0:
        return None
    
    return profile / norm


def _calculate_category_match_score(paper: Paper, user_profile: UserProfile) -> float:
    """计算分类匹配分数"""
    if not user_profile.interested_categories or not paper.categories:
        return 0.0
    
    paper_categories = set(paper.categories)
    user_categories = set(user_profile.interested_categories)
    
    intersection = paper_categories & user_categories
    match_ratio = len(intersection) / len(paper_categories)
    
    return match_ratio * 0.5  # 最多贡献0.5分


def _calculate_keyword_match_score(paper: Paper, user_profile: UserProfile) -> float:
    """计算关键词匹配分数"""
    if not user_profile.research_keywords:
        return 0.0
    
    search_text = f"{paper.title} {paper.summary}".lower()
    matched_keywords = sum(
        1 for keyword in user_profile.research_keywords
        if keyword.lower() in search_text
    )
    
    match_ratio = matched_keywords / len(user_profile.research_keywords)
    return min(match_ratio * 0.3, 0.3)  # 最多贡献0.3分


# 算法注册表
SCORING_ALGORITHMS = {
    'default': default_scoring_algorithm,
    'embedding': embedding_similarity_algorithm,
    'category': category_matching_algorithm,
    'time_decay': time_decay_algorithm,
}


def get_scoring_algorithm(algorithm_name: str) -> Callable:
    """
    获取评分算法函数
    
    Args:
        algorithm_name: 算法名称
        
    Returns:
        评分算法函数
    """
    if algorithm_name not in SCORING_ALGORITHMS:
        raise ValueError(f"未知的评分算法: {algorithm_name}")
    
    return SCORING_ALGORITHMS[algorithm_name]


def list_available_algorithms() -> list:
    """列出所有可用的算法"""
    return list(SCORING_ALGORITHMS.keys())
