"""
用户排序表管理服务
单一职责：管理用户的论文排序表
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import List, Optional
from uuid import UUID

from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, and_

from app.models import UserPaperRanking, UserFeedback
from app.services.recommendation.user_paper_ranking import generate_paper_ranking


class UserRankingService:
    """用户排序表管理服务"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def update_user_ranking(
        self,
        user_id: str,
        source_key: str,
        paper_ids: List[UUID],
        force_update: bool = False,
        limit: Optional[int] = None
    ) -> bool:
        """更新用户排序表"""
        try:
            # 静态数据源需要预过滤
            if self._is_static_source(source_key):
                paper_ids = self._filter_user_feedback_papers(user_id, paper_ids)
            
            # 生成排序 (全量打分)
            scored_papers = generate_paper_ranking(self.session, paper_ids, user_id)
            if not scored_papers:
                return False
            
            # 截取 Top N
            if limit and limit > 0:
                scored_papers = scored_papers[:limit]
            
            # 保存排序表
            self._save_ranking(user_id, source_key, scored_papers)
            return True
            
        except Exception as e:
            logger.error(f"更新排序表失败: {e}")
            return False
    
    def get_user_ranking(
        self,
        user_id: str,
        source_key: str
    ) -> Optional[UserPaperRanking]:
        """获取用户排序表"""
        stmt = select(UserPaperRanking).where(
            and_(
                UserPaperRanking.user_id == user_id,
                UserPaperRanking.source_key == source_key
            )
        )
        return self.session.execute(stmt).scalar_one_or_none()
    
    def cleanup_expired_rankings(self) -> int:
        """清理过期的动态数据源排序表 (保留7天)"""
        cutoff_date = date.today() - timedelta(days=7)
        
        # 清理arxiv动态数据源的过期排序表
        result = self.session.execute(
            delete(UserPaperRanking).where(
                and_(
                    UserPaperRanking.pool_date < cutoff_date,
                    UserPaperRanking.source_key.like('arxiv_%')
                )
            )
        )
        
        self.session.commit()
        logger.info(f"清理了 {result.rowcount} 条过期的arxiv排序表")
        return result.rowcount
    
    def get_user_rankings_by_source_type(
        self,
        user_id: str,
        source_type: str = "dynamic"
    ) -> List[UserPaperRanking]:
        """获取用户指定类型的所有排序表"""
        if source_type == "dynamic":
            # 获取arxiv相关的排序表
            stmt = select(UserPaperRanking).where(
                and_(
                    UserPaperRanking.user_id == user_id,
                    UserPaperRanking.source_key.like('arxiv_%')
                )
            ).order_by(UserPaperRanking.pool_date.desc())
        else:
            # 获取静态数据源排序表
            stmt = select(UserPaperRanking).where(
                and_(
                    UserPaperRanking.user_id == user_id,
                    ~UserPaperRanking.source_key.like('arxiv_%')
                )
            )
        
        return self.session.execute(stmt).scalars().all()
    
    def _is_static_source(self, source_key: str) -> bool:
        """判断是否为静态数据源"""
        static_prefixes = ['neurips', 'icml', 'iclr', 'conf_']
        return any(source_key.startswith(prefix) for prefix in static_prefixes)
    
    def _filter_user_feedback_papers(
        self,
        user_id: str,
        paper_ids: List[UUID]
    ) -> List[UUID]:
        """过滤用户已反馈的论文"""
        stmt = select(UserFeedback.paper_id).where(
            UserFeedback.user_id == user_id
        )
        feedback_paper_ids = set(self.session.execute(stmt).scalars().all())
        return [pid for pid in paper_ids if pid not in feedback_paper_ids]
    
    def _save_ranking(self, user_id: str, source_key: str, scored_papers):
        """保存排序表到数据库"""
        # 如果source_key已经包含日期格式，不再添加日期后缀
        if self._is_dynamic_source(source_key) and not self._has_date_suffix(source_key):
            source_key = f"{source_key}_{date.today().strftime('%Y-%m-%d')}"
        
        # 删除相同source_key的旧排序表
        self.session.execute(
            delete(UserPaperRanking).where(
                and_(
                    UserPaperRanking.user_id == user_id,
                    UserPaperRanking.source_key == source_key
                )
            )
        )
        
        # 创建新排序表
        paper_ids = [UUID(sp.paper_id) for sp in scored_papers]
        scores = [sp.score for sp in scored_papers]
        
        new_ranking = UserPaperRanking(
            user_id=user_id,
            pool_date=date.today(),
            source_key=source_key,
            paper_ids=paper_ids,
            scores=scores
        )
        
        self.session.add(new_ranking)
        self.session.commit()
        logger.info(f"保存用户 {user_id} 数据源 {source_key} 排序表: {len(paper_ids)} 篇论文")
    
    def _has_date_suffix(self, source_key: str) -> bool:
        """检查source_key是否已包含日期格式"""
        import re
        # 检查是否包含 YYYYMMDD 或 YYYY-MM-DD 格式
        return bool(re.search(r'\d{8}|\d{4}-\d{2}-\d{2}', source_key))
    
    def _is_dynamic_source(self, source_key: str) -> bool:
        """判断是否为动态数据源"""
        dynamic_prefixes = ['arxiv']
        return any(source_key.startswith(prefix) for prefix in dynamic_prefixes)
