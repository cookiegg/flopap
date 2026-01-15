"""
推荐系统统一接口 (Facade模式)
提供简化的对外接口，隐藏内部复杂性
"""
from __future__ import annotations

from typing import List, Dict
from uuid import UUID

from sqlalchemy.orm import Session

from app.services.recommendation.user_ranking_service import UserRankingService
from app.services.recommendation.recommendation_pool_service import RecommendationPoolService, FeedbackType
from app.services.recommendation.ranking_scheduler_service import RankingSchedulerService


class RecommendationFacade:
    """推荐系统统一接口"""
    
    def __init__(self, session: Session):
        self.session = session
        self.ranking_service = UserRankingService(session)
        self.pool_service = RecommendationPoolService(session)
        self.scheduler_service = RankingSchedulerService(session)
    
    # === 用户推荐池操作 ===
    
    def get_user_recommendations(
        self,
        user_id: str,
        source_key: str,
        pool_ratio: float = 0.1
    ) -> List[UUID]:
        """获取用户推荐池"""
        return self.pool_service.generate_pool(user_id, source_key, pool_ratio)
    
    def user_like_paper(self, user_id: str, paper_id: UUID) -> Dict:
        """用户点赞论文"""
        return self.pool_service.handle_feedback(
            user_id, paper_id, FeedbackType.LIKE
        )
    
    def user_bookmark_paper(self, user_id: str, paper_id: UUID) -> Dict:
        """用户收藏论文"""
        return self.pool_service.handle_feedback(
            user_id, paper_id, FeedbackType.BOOKMARK
        )
    
    def user_dislike_paper(
        self,
        user_id: str,
        paper_id: UUID,
        source_key: str = None
    ) -> Dict:
        """用户不感兴趣论文"""
        return self.pool_service.handle_feedback(
            user_id, paper_id, FeedbackType.DISLIKE, source_key
        )
    
    def adjust_pool_ratio(
        self,
        user_id: str,
        source_key: str,
        new_ratio: float
    ) -> List[UUID]:
        """调整推荐池比例"""
        return self.pool_service.adjust_pool_size(user_id, source_key, new_ratio)
    
    # === 管理员操作 ===
    
    def update_user_ranking(
        self,
        user_id: str,
        source_key: str,
        paper_ids: List[UUID]
    ) -> bool:
        """更新用户排序表"""
        return self.ranking_service.update_user_ranking(
            user_id, source_key, paper_ids
        )
    
    def daily_arxiv_update(self, paper_ids: List[UUID]) -> Dict[str, int]:
        """每日arxiv更新任务"""
        return self.scheduler_service.daily_arxiv_update_job(paper_ids)
    
    def update_static_source_for_changed_users(
        self,
        source_key: str,
        paper_ids: List[UUID]
    ) -> Dict[str, int]:
        """为画像有变化的用户更新静态数据源"""
        return self.scheduler_service.update_static_source_for_changed_users(
            source_key, paper_ids
        )
    
    def get_user_ranking_status(
        self,
        user_id: str,
        source_type: str = "all"
    ) -> Dict[str, any]:
        """获取用户排序表状态"""
        if source_type == "dynamic":
            rankings = self.ranking_service.get_user_rankings_by_source_type(
                user_id, "dynamic"
            )
        elif source_type == "static":
            rankings = self.ranking_service.get_user_rankings_by_source_type(
                user_id, "static"
            )
        else:
            # 获取所有排序表
            dynamic_rankings = self.ranking_service.get_user_rankings_by_source_type(
                user_id, "dynamic"
            )
            static_rankings = self.ranking_service.get_user_rankings_by_source_type(
                user_id, "static"
            )
            rankings = dynamic_rankings + static_rankings
        
        return {
            "user_id": user_id,
            "total_rankings": len(rankings),
            "rankings": [
                {
                    "source_key": r.source_key,
                    "pool_date": r.pool_date.isoformat(),
                    "paper_count": len(r.paper_ids) if r.paper_ids else 0,
                    "last_updated": r.updated_at.isoformat() if r.updated_at else None
                }
                for r in rankings
            ]
        }
    
    def cleanup_expired_rankings(self) -> Dict[str, int]:
        """清理过期排序表"""
        cleaned_count = self.ranking_service.cleanup_expired_rankings()
        return {"cleaned_rankings": cleaned_count}
