from datetime import datetime, timedelta
from typing import List
from uuid import UUID

from sqlalchemy import select, func, desc, and_, case
from sqlalchemy.orm import Session

from app.models import Paper, UserFeedback, FeedbackTypeEnum

class ColdStartService:
    """
    冷启动推荐服务 (Cloud Cold Start)
    
    当无法获取用户个性化推荐池时（如新用户、同步延迟），
    提供基于全局热度 (Hot) 和时效性 (Latest) 的兜底推荐。
    """

    def __init__(self, session: Session):
        self.session = session

    def get_cold_start_pool(self, limit: int = 50) -> List[UUID]:
        """
        获取冷启动推荐池
        
        策略:
        1. 优先获取全局热榜 (Hot Papers)
        2. 如果热榜数量不足，用最新论文 (Latest Papers) 补足
        
        Args:
            limit: 推荐数量
            
        Returns:
            论文 ID 列表
        """
        # 1. 获取热榜
        hot_papers = self.get_hot_papers(limit=limit)
        
        # 如果热榜已经够了，直接返回
        if len(hot_papers) >= limit:
            return hot_papers
        
        # 2. 获取最新论文来补足
        remaining = limit - len(hot_papers)
        # 排除已经包含在热榜里的 ID
        exclude_ids = set(hot_papers)
        
        latest_papers = self.get_latest_papers(limit=remaining * 2, exclude_ids=exclude_ids)
        
        # 合并结果
        result = hot_papers + latest_papers
        return result[:limit]

    def get_hot_papers(self, limit: int = 50, days: int = 7) -> List[UUID]:
        """
        获取全局热榜 (基于用户反馈)
        
        Score = Like * 1 + Bookmark * 2
        仅统计最近 `days` 天发布的论文，保证新鲜度。
        
        Args:
            limit: 数量限制
            days: 论文发布时间窗口 (天)
            
        Returns:
            按热度排序的论文 ID 列表
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # 聚合查询: 计算每篇论文的分数
        # 注意: 这里不管是 Like 还是 Bookmark 都是 UserFeedback 表的一条记录
        # 我们需要根据 feedback_type 给不同权重
        
        # 方法 A: 简单 Count (所有交互都算 1 分)
        # stmt = select(UserFeedback.paper_id, func.count(UserFeedback.id).label("score")) \
        #     .join(Paper) \
        #     .where(Paper.submitted_date >= cutoff_date) \
        #     .group_by(UserFeedback.paper_id) \
        #     .order_by(desc("score")) \
        #     .limit(limit)
            
        # 方法 B: 加权分数 (Like=1, Bookmark=2)
        # 使用 Case 语句在 SQL 中计算
        score_expr = func.sum(
            case(
                (UserFeedback.feedback_type == FeedbackTypeEnum.BOOKMARK, 2),
                (UserFeedback.feedback_type == FeedbackTypeEnum.LIKE, 1),
                else_=0
            )
        ).label("total_score")

        stmt = select(UserFeedback.paper_id) \
            .join(Paper) \
            .where(
                and_(
                    Paper.submitted_date >= cutoff_date,
                    # 过滤掉 dislike (虽然 dislike 也是一种交互，但我们不推荐被讨厌的)
                    UserFeedback.feedback_type.in_([FeedbackTypeEnum.LIKE, FeedbackTypeEnum.BOOKMARK])
                )
            ) \
            .group_by(UserFeedback.paper_id) \
            .order_by(desc(score_expr)) \
            .limit(limit)
            
        result = self.session.execute(stmt).scalars().all()
        return list(result)

    def get_latest_papers(self, limit: int = 50, exclude_ids: set[UUID] = None) -> List[UUID]:
        """
        获取最新发布的论文
        
        Args:
            limit: 数量限制
            exclude_ids: 需要排除的论文 ID (通常是已经出现在热榜里的)
            
        Returns:
            按提交时间倒序的论文 ID 列表
        """
        stmt = select(Paper.id).order_by(Paper.submitted_date.desc())
        
        if exclude_ids:
            stmt = stmt.where(Paper.id.notin_(exclude_ids))
            
        stmt = stmt.limit(limit)
        
        result = self.session.execute(stmt).scalars().all()
        return list(result)
