"""
多层推荐池服务 - 基于用户需求的简化实现
保护排序表完整性，在推荐池层面进行过滤
"""

from typing import List, Set, Optional
from uuid import UUID
from datetime import date, datetime
from enum import Enum

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models import UserPaperRanking, UserFeedback, Paper
from app.services.recommendation.user_ranking_service import UserRankingService


class SourceType(Enum):
    DYNAMIC = "dynamic"  # arxiv等动态数据源
    STATIC = "static"    # neurips等静态数据源


class MultiLayerRecommendationService:
    """多层推荐池服务"""
    
    def __init__(self, session: Session):
        self.session = session
        self.ranking_service = UserRankingService(session)
    
    def get_user_recommendations(
        self,
        user_id: str,
        source: str,
        pool_ratio: float = 1.0,  # 默认不截取，由 ranking 自己决定大小
        max_size: int = 5000  # 提高上限
    ) -> List[UUID]:
        """获取用户推荐 - 统一入口"""
        
        source_type = self._get_source_type(source)
        today = datetime.now().date()
        
        if source_type == SourceType.DYNAMIC:
            return self._get_dynamic_recommendations(user_id, source, today, pool_ratio, max_size)
        else:
            return self._get_static_recommendations(user_id, source, today, pool_ratio, max_size)
    
    def _get_dynamic_recommendations(
        self,
        user_id: str,
        source: str,
        date: date,
        pool_ratio: float,
        max_size: int
    ) -> List[UUID]:
        """动态数据源推荐流程"""
        
        # Step 1: 获取排序表 (真值来源，不修改)
        # For arxiv, use T-3 date (papers are submitted 3 days before they appear)
        # Use arxiv_day_ prefix to match ArxivPoolService and Factory naming
        if source == 'arxiv':
            import pendulum
            ranking_date = pendulum.now("America/New_York").subtract(days=3).date()
            source_key = f"arxiv_day_{ranking_date.strftime('%Y%m%d')}"
        else:
            ranking_date = date
            source_key = f"{source}_{ranking_date.strftime('%Y%m%d')}"
        ranking = self.ranking_service.get_user_ranking(user_id, source_key)
        
        if not ranking or not ranking.paper_ids:
            return []
        
        # Step 2: 生成推荐池1 (初始推荐池)
        pool1 = self._generate_initial_pool(ranking.paper_ids, pool_ratio, max_size)
        
        # Step 3: 生成推荐池2 (过滤当日不感兴趣)
        pool2 = self._apply_realtime_filters(user_id, pool1, date)
        
        return pool2
    
    def _get_static_recommendations(
        self,
        user_id: str,
        source: str,
        date: date,
        pool_ratio: float,
        max_size: int
    ) -> List[UUID]:
        """静态数据源推荐流程"""
        
        # Step 1: 获取排序表 (可能需要重新生成)
        ranking = self._get_or_regenerate_static_ranking(user_id, source, date)
        
        if not ranking or not ranking.paper_ids:
            return []
        
        # Step 2: 生成推荐池1 (初始推荐池)
        pool1 = self._generate_initial_pool(ranking.paper_ids, pool_ratio, max_size)
        
        # Step 3: 生成推荐池2 (过滤历史交互 + 当日不感兴趣)
        pool2 = self._apply_comprehensive_filters(user_id, source, pool1, date)
        
        return pool2
    
    def _generate_initial_pool(
        self,
        paper_ids: List[UUID],
        pool_ratio: float,
        max_size: int
    ) -> List[UUID]:
        """生成初始推荐池"""
        pool_size = min(int(len(paper_ids) * pool_ratio), max_size, len(paper_ids))
        return paper_ids[:pool_size]
    
    def _apply_realtime_filters(
        self,
        user_id: str,
        initial_pool: List[UUID],
        filter_date: date
    ) -> List[UUID]:
        """应用实时过滤 (仅过滤当日不感兴趣)"""
        
        # 获取当日不感兴趣的论文
        disliked_today = self._get_disliked_papers_by_date(user_id, filter_date)
        
        # 过滤不感兴趣的论文，保留点赞和收藏的
        return [pid for pid in initial_pool if pid not in disliked_today]
    
    def _apply_comprehensive_filters(
        self,
        user_id: str,
        source: str,
        initial_pool: List[UUID],
        filter_date: date
    ) -> List[UUID]:
        """应用综合过滤 (历史交互 + 当日不感兴趣)"""
        
        # 获取历史交互过的论文 (昨天及之前)
        historical_interacted = self._get_historical_interacted_papers(user_id, filter_date)
        
        # 获取当日不感兴趣的论文
        disliked_today = self._get_disliked_papers_by_date(user_id, filter_date)
        
        # 应用过滤规则
        filtered_pool = []
        for paper_id in initial_pool:
            # 过滤历史交互过的论文
            if paper_id in historical_interacted:
                continue
            
            # 过滤当日不感兴趣的论文
            if paper_id in disliked_today:
                continue
            
            filtered_pool.append(paper_id)
        
        return filtered_pool
    
    def _get_disliked_papers_by_date(self, user_id: str, date: date) -> Set[UUID]:
        """获取指定日期不感兴趣的论文"""
        stmt = select(UserFeedback.paper_id).where(
            UserFeedback.user_id == user_id,
            UserFeedback.feedback_type == 'dislike',
            func.date(UserFeedback.created_at) == date
        )
        return set(self.session.execute(stmt).scalars().all())
    
    def _get_historical_interacted_papers(self, user_id: str, before_date: date) -> Set[UUID]:
        """获取历史交互过的论文 (点赞、收藏、不感兴趣)"""
        stmt = select(UserFeedback.paper_id).where(
            UserFeedback.user_id == user_id,
            func.date(UserFeedback.created_at) < before_date
        )
        return set(self.session.execute(stmt).scalars().all())
    
    def _get_or_regenerate_static_ranking(
        self,
        user_id: str,
        source: str,
        date: date
    ) -> Optional[UserPaperRanking]:
        """获取或重新生成静态数据源排序表"""
        
        # 检查今日是否已有排序表
        existing = self.ranking_service.get_user_ranking(user_id, source)
        
        # 如果不存在或用户画像有变化，重新生成
        if not existing or self._should_regenerate_ranking(user_id, source, date):
            # 获取静态数据源的所有论文 (不预过滤)
            all_papers = self._get_static_source_papers(source)
            
            # 重新生成完整排序表
            success = self.ranking_service.update_user_ranking(
                user_id, source, all_papers, force_update=True
            )
            
            if success:
                return self.ranking_service.get_user_ranking(user_id, source)
        
        return existing
    
    def _should_regenerate_ranking(self, user_id: str, source: str, date: date) -> bool:
        """判断是否需要重新生成排序表"""
        from datetime import timedelta
        
        # 简化逻辑：检查用户是否有新的反馈行为
        recent_feedback_count = self.session.execute(
            select(func.count(UserFeedback.id)).where(
                UserFeedback.user_id == user_id,
                func.date(UserFeedback.created_at) >= date - timedelta(days=1)
            )
        ).scalar()
        
        return recent_feedback_count > 0
    
    def _get_static_source_papers(self, source: str) -> List[UUID]:
        """获取静态数据源的所有论文"""
        stmt = select(Paper.id).where(Paper.source == source)
        return list(self.session.execute(stmt).scalars().all())
    
    def _get_source_type(self, source: str) -> SourceType:
        """判断数据源类型"""
        if source.startswith('arxiv'):
            return SourceType.DYNAMIC
        else:
            return SourceType.STATIC
    
    def handle_user_dislike(self, user_id: str, paper_id: UUID, source: str) -> dict:
        """处理用户不感兴趣反馈 - 不修改排序表"""
        
        # 1. 保存反馈记录
        from uuid import uuid4
        from sqlalchemy import insert
        
        insert_stmt = insert(UserFeedback.__table__).values(
            id=uuid4(),
            user_id=user_id,
            paper_id=paper_id,
            feedback_type='dislike',
        )
        self.session.execute(insert_stmt)
        self.session.commit()
        
        # 2. 清除相关缓存 (如果有)
        self._invalidate_recommendation_cache(user_id, source)
        
        return {
            "action": "dislike",
            "paper_id": str(paper_id),
            "message": "已从当前推荐中移除，排序表保持完整"
        }
    
    def _invalidate_recommendation_cache(self, user_id: str, source: str):
        """清除推荐缓存"""
        # 这里可以实现Redis缓存清除逻辑
        pass
