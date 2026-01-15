"""
推荐池管理服务
单一职责：管理用户的推荐池，处理实时反馈
"""
from __future__ import annotations

from typing import List, Dict, Optional
from uuid import UUID
from enum import Enum

from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.models import UserPaperRanking, UserFeedback
from app.services.recommendation.user_ranking_service import UserRankingService


class FeedbackType(Enum):
    LIKE = "like"
    BOOKMARK = "bookmark"
    DISLIKE = "dislike"


class RecommendationPoolService:
    """推荐池管理服务"""
    
    def __init__(self, session: Session):
        self.session = session
        self.ranking_service = UserRankingService(session)
    
    def generate_pool(
        self,
        user_id: str,
        source_key: str,
        pool_ratio: float = 0.1,
        max_size: int = 1000
    ) -> List[UUID]:
        """生成推荐池"""
        # 对于动态数据源，获取最新的排序表
        if self._is_dynamic_source(source_key):
            ranking = self._get_latest_dynamic_ranking(user_id, source_key)
        else:
            ranking = self.ranking_service.get_user_ranking(user_id, source_key)
        
        if not ranking or not ranking.paper_ids:
            logger.warning(f"用户 {user_id} 数据源 {source_key} 无排序表")
            return []
        
        # 计算推荐池大小
        total_papers = len(ranking.paper_ids)
        pool_size = min(
            int(total_papers * pool_ratio),
            max_size,
            total_papers
        )
        
        # 处理极端情况
        if pool_ratio >= 1.0:
            pool_size = min(total_papers, max_size)
            logger.warning(f"用户 {user_id} 要求全部论文，限制为 {pool_size}")
        
        return ranking.paper_ids[:pool_size]
    
    def _is_dynamic_source(self, source_key: str) -> bool:
        """判断是否为动态数据源"""
        return source_key.startswith('arxiv')
    
    def _get_latest_dynamic_ranking(
        self,
        user_id: str,
        source_key: str
    ) -> Optional[UserPaperRanking]:
        """获取动态数据源的最新排序表"""
        stmt = select(UserPaperRanking).where(
            and_(
                UserPaperRanking.user_id == user_id,
                UserPaperRanking.source_key.like(f'{source_key}_%')
            )
        ).order_by(UserPaperRanking.pool_date.desc())
        
        return self.session.execute(stmt).scalars().first()
    
    def handle_feedback(
        self,
        user_id: str,
        paper_id: UUID,
        feedback_type: FeedbackType,
        source_key: Optional[str] = None
    ) -> Dict[str, any]:
        """处理用户反馈"""
        result = {
            "action": feedback_type.value,
            "paper_id": str(paper_id),
            "removed_from_pools": []
        }
        
        try:
            # 保存反馈
            self._save_feedback(user_id, paper_id, feedback_type)
            
            # 处理不感兴趣：从推荐池移除
            if feedback_type == FeedbackType.DISLIKE:
                removed_pools = self._remove_from_pools(user_id, paper_id, source_key)
                result["removed_from_pools"] = removed_pools
            
            return result
            
        except Exception as e:
            logger.error(f"处理反馈失败: {e}")
            result["error"] = str(e)
            return result
    
    def adjust_pool_size(
        self,
        user_id: str,
        source_key: str,
        new_ratio: float
    ) -> List[UUID]:
        """调整推荐池大小"""
        new_ratio = max(0.0, min(new_ratio, 1.0))  # 限制范围
        return self.generate_pool(user_id, source_key, new_ratio)
    
    def get_pool_status(
        self,
        user_id: str,
        source_key: str
    ) -> Dict[str, any]:
        """获取推荐池状态"""
        ranking = self.ranking_service.get_user_ranking(user_id, source_key)
        if not ranking:
            return {"error": "未找到排序表"}
        
        return {
            "user_id": user_id,
            "source_key": source_key,
            "total_papers": len(ranking.paper_ids) if ranking.paper_ids else 0,
            "pool_date": ranking.pool_date.isoformat() if ranking.pool_date else None,
            "last_updated": ranking.updated_at.isoformat() if ranking.updated_at else None
        }
    
    def _save_feedback(self, user_id: str, paper_id: UUID, feedback_type: FeedbackType):
        """保存用户反馈"""
        existing = self.session.query(UserFeedback).filter(
            and_(
                UserFeedback.user_id == user_id,
                UserFeedback.paper_id == paper_id
            )
        ).first()
        
        if existing:
            existing.feedback_type = feedback_type.value
        else:
            new_feedback = UserFeedback(
                user_id=user_id,
                paper_id=paper_id,
                feedback_type=feedback_type.value
            )
            self.session.add(new_feedback)
        
        self.session.commit()
    
    def _remove_from_pools(
        self,
        user_id: str,
        paper_id: UUID,
        target_source: Optional[str] = None
    ) -> List[str]:
        """从推荐池移除论文"""
        conditions = [UserPaperRanking.user_id == user_id]
        if target_source:
            conditions.append(UserPaperRanking.source_key == target_source)
        
        stmt = select(UserPaperRanking).where(and_(*conditions))
        pools = self.session.execute(stmt).scalars().all()
        
        removed_sources = []
        for pool in pools:
            if pool.paper_ids and paper_id in pool.paper_ids:
                idx = pool.paper_ids.index(paper_id)
                pool.paper_ids.pop(idx)
                if pool.scores and len(pool.scores) > idx:
                    pool.scores.pop(idx)
                removed_sources.append(pool.source_key)
        
        self.session.commit()
        return removed_sources
