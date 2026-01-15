"""
排序表调度服务
单一职责：管理定时更新任务
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import List, Dict

from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models import UserFeedback, UserPaperRanking
from app.services.recommendation.user_ranking_service import UserRankingService


class RankingSchedulerService:
    """排序表调度服务"""
    
    def __init__(self, session: Session):
        self.session = session
        self.ranking_service = UserRankingService(session)
    
    def daily_arxiv_update_job(self, paper_ids: List) -> Dict[str, int]:
        """每日arxiv更新任务"""
        stats = {"updated_users": 0, "failed_users": 0, "cleaned_rankings": 0}
        
        # 获取所有用户ID
        stmt = select(UserPaperRanking.user_id).distinct()
        all_users = self.session.execute(stmt).scalars().all()
        
        # 为每个用户更新arxiv排序表
        for user_id in all_users:
            if self.ranking_service.update_user_ranking(user_id, "arxiv", paper_ids):
                stats["updated_users"] += 1
            else:
                stats["failed_users"] += 1
        
        # 清理过期的arxiv排序表
        stats["cleaned_rankings"] = self.ranking_service.cleanup_expired_rankings()
        
        logger.info(f"每日arxiv更新完成: {stats}")
        return stats
    
    def update_static_source_for_changed_users(
        self,
        source_key: str,
        paper_ids: List
    ) -> Dict[str, int]:
        """为画像有变化的用户更新静态数据源"""
        stats = {"updated": 0, "skipped": 0, "failed": 0}
        
        # 获取所有用户
        stmt = select(UserPaperRanking.user_id).distinct()
        all_users = self.session.execute(stmt).scalars().all()
        
        for user_id in all_users:
            # 检查用户画像是否有变化
            if self.check_user_profile_changes(user_id):
                if self.ranking_service.update_user_ranking(user_id, source_key, paper_ids):
                    stats["updated"] += 1
                else:
                    stats["failed"] += 1
            else:
                stats["skipped"] += 1
        
        logger.info(f"静态数据源 {source_key} 更新完成: {stats}")
        return stats
    
    def update_static_source_for_all_users(
        self,
        source_key: str,
        paper_ids: List
    ) -> Dict[str, int]:
        """为所有用户更新静态数据源"""
        stats = {"updated": 0, "failed": 0}
        
        # 获取所有用户
        stmt = select(UserPaperRanking.user_id).distinct()
        all_users = self.session.execute(stmt).scalars().all()
        
        for user_id in all_users:
            if self.ranking_service.update_user_ranking(
                user_id, source_key, paper_ids
            ):
                stats["updated"] += 1
            else:
                stats["failed"] += 1
        
        return stats
    
    def check_user_profile_changes(self, user_id: str) -> bool:
        """检查用户画像是否有变化"""
        # 简单实现：检查最近是否有新反馈
        yesterday = date.today() - timedelta(days=1)
        
        stmt = select(func.count(UserFeedback.id)).where(
            UserFeedback.user_id == user_id,
            UserFeedback.created_at >= yesterday
        )
        
        recent_feedback_count = self.session.execute(stmt).scalar() or 0
        return recent_feedback_count >= 3  # 阈值：3次新反馈
    
    def _get_active_users(self) -> List[str]:
        """获取有新反馈的用户"""
        yesterday = date.today() - timedelta(days=1)
        
        stmt = select(UserFeedback.user_id).distinct().where(
            UserFeedback.created_at >= yesterday
        )
        
        return self.session.execute(stmt).scalars().all()
    
    def _update_user_all_sources(self, user_id: str) -> bool:
        """更新用户所有数据源"""
        try:
            # 获取用户现有的数据源
            stmt = select(UserPaperRanking.source_key).distinct().where(
                UserPaperRanking.user_id == user_id
            )
            user_sources = self.session.execute(stmt).scalars().all()
            
            success_count = 0
            for source_key in user_sources:
                # 这里需要根据source_key获取对应的论文ID
                # 实际实现中需要调用数据源服务
                paper_ids = self._get_papers_for_source(source_key)
                
                if self.ranking_service.update_user_ranking(
                    user_id, source_key, paper_ids
                ):
                    success_count += 1
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"更新用户 {user_id} 失败: {e}")
            return False
    
    def _get_papers_for_source(self, source_key: str) -> List:
        """获取数据源的论文ID"""
        from app.models import Paper
        from sqlalchemy import cast, Date
        
        # 解析 source_key 获取论文
        if source_key.startswith("arxiv_day_"):
            # arxiv_day_YYYYMMDD 格式
            try:
                date_str = source_key.replace("arxiv_day_", "")
                target_date = date(int(date_str[:4]), int(date_str[4:6]), int(date_str[6:8]))
                
                stmt = select(Paper.id).where(
                    cast(Paper.submitted_date, Date) == target_date,
                    Paper.source == 'arxiv',
                    Paper.primary_category.like('cs.%')
                )
                return list(self.session.execute(stmt).scalars().all())
            except (ValueError, IndexError):
                logger.warning(f"无法解析 source_key: {source_key}")
                return []
        
        elif source_key.startswith("conf/"):
            # 会议论文 (如 conf/neurips2025)
            stmt = select(Paper.id).where(
                Paper.source_key == source_key
            )
            return list(self.session.execute(stmt).scalars().all())
        
        else:
            logger.warning(f"未知的 source_key 类型: {source_key}")
            return []

