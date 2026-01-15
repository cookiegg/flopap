"""
Arxiv 推荐池服务 - Today/Week 分层池实现

Today Pool (D0): 今日新论文，完整个性化排序
Week Pool (D1-D6): 前6天论文，仅过滤"不感兴趣"
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import List, Optional
from uuid import UUID

from loguru import logger
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session

from app.models import UserPaperRanking, UserFeedback, Paper
from app.services.recommendation.user_ranking_service import UserRankingService
from app.services.cache_service import CacheService


class ArxivPoolService:
    """Arxiv Today/Week 推荐池服务"""
    
    # source_key 前缀
    SOURCE_PREFIX = "arxiv_day_"
    
    def __init__(self, session: Session):
        self.session = session
        self.ranking_service = UserRankingService(session)
    
    def get_today_pool(self, user_id: str) -> List[UUID]:
        """
        获取今日推荐池 (D0)
        
        Returns:
            排序后的论文 ID 列表
        """
        # 尝试从缓存获取
        cached = CacheService.get_today_pool(user_id)
        if cached:
            logger.debug(f"Today Pool cache hit for user {user_id}")
            return [UUID(pid) for pid in cached]
        
        # T-3 规则：Arxiv 论文发布有延迟，实际"今日"论文对应 3 天前提交的论文
        # 与 fetch_daily_papers.py 保持一致
        import pendulum
        today_ny = pendulum.now("America/New_York")
        target_date = today_ny.subtract(days=3).date()
        source_key = f"{self.SOURCE_PREFIX}{target_date.strftime('%Y%m%d')}"
        
        ranking = self.ranking_service.get_user_ranking(user_id, source_key)
        
        if not ranking or not ranking.paper_ids:
            # 云端实时生成排序表
            logger.info(f"用户 {user_id} 今日排序表不存在，开始实时生成 (source_key={source_key})")
            paper_ids = self._generate_ranking_on_demand(user_id, source_key)
        else:
            paper_ids = ranking.paper_ids
        
        if not paper_ids:
            logger.warning(f"用户 {user_id} 今日推荐池为空")
            return []
        
        # 过滤今日不感兴趣的论文
        disliked_ids = self._get_disliked_paper_ids(user_id)
        filtered_ids = [pid for pid in paper_ids if pid not in disliked_ids]
        
        # 写入缓存
        CacheService.set_today_pool(user_id, [str(pid) for pid in filtered_ids])
        
        logger.debug(f"Today Pool: {len(paper_ids)} -> {len(filtered_ids)} (过滤 {len(disliked_ids)} 不感兴趣)")
        return filtered_ids
    
    def get_week_pool(self, user_id: str) -> List[UUID]:
        """
        获取一周推荐池 (D1-D6 合并)
        
        只过滤"不感兴趣"，保留点赞/收藏论文
        
        Returns:
            合并后的论文 ID 列表 (按原排序)
        """
        # 尝试从缓存获取
        cached = CacheService.get_week_pool(user_id)
        if cached:
            logger.debug(f"Week Pool cache hit for user {user_id}")
            return [UUID(pid) for pid in cached]
        
        # T-3 规则：与 get_today_pool 保持一致
        import pendulum
        today_ny = pendulum.now("America/New_York")
        today_target = today_ny.subtract(days=3).date()
        all_paper_ids: List[UUID] = []
        
        # 收集 D1 到 D6 (前6天，基于 T-3 规则的今日)
        for days_ago in range(1, 7):
            target_date = today_target - timedelta(days=days_ago)
            source_key = f"{self.SOURCE_PREFIX}{target_date.strftime('%Y%m%d')}"
            
            ranking = self.ranking_service.get_user_ranking(user_id, source_key)
            if ranking and ranking.paper_ids:
                all_paper_ids.extend(ranking.paper_ids)
        
        if not all_paper_ids:
            logger.warning(f"用户 {user_id} 一周推荐池为空")
            return []
        
        # 只过滤"不感兴趣"的论文
        disliked_ids = self._get_disliked_paper_ids(user_id)
        filtered_ids = [pid for pid in all_paper_ids if pid not in disliked_ids]
        
        # 去重 (保持顺序)
        seen = set()
        unique_ids = []
        for pid in filtered_ids:
            if pid not in seen:
                seen.add(pid)
                unique_ids.append(pid)
        
        # 写入缓存
        CacheService.set_week_pool(user_id, [str(pid) for pid in unique_ids])
        
        logger.debug(f"Week Pool: {len(all_paper_ids)} -> {len(unique_ids)} (过滤 {len(disliked_ids)} 不感兴趣, 去重)")
        return unique_ids
    
    def _get_disliked_paper_ids(self, user_id: str) -> set:
        """获取用户所有"不感兴趣"的论文 ID"""
        stmt = select(UserFeedback.paper_id).where(
            and_(
                UserFeedback.user_id == user_id,
                UserFeedback.feedback_type == 'dislike'
            )
        )
        return set(self.session.execute(stmt).scalars().all())
    
    def get_pool_stats(self, user_id: str) -> dict:
        """获取用户推荐池统计信息"""
        today = date.today()
        stats = {
            "today_count": 0,
            "week_count": 0,
            "week_days": [],
        }
        
        # Today
        today_source_key = f"{self.SOURCE_PREFIX}{today.strftime('%Y%m%d')}"
        today_ranking = self.ranking_service.get_user_ranking(user_id, today_source_key)
        if today_ranking:
            stats["today_count"] = len(today_ranking.paper_ids)
        
        # Week
        for days_ago in range(1, 7):
            target_date = today - timedelta(days=days_ago)
            source_key = f"{self.SOURCE_PREFIX}{target_date.strftime('%Y%m%d')}"
            ranking = self.ranking_service.get_user_ranking(user_id, source_key)
            
            day_count = len(ranking.paper_ids) if ranking else 0
            stats["week_days"].append({
                "date": target_date.isoformat(),
                "count": day_count
            })
            stats["week_count"] += day_count
        
        return stats
    
    # ==================== 云端实时排序生成 ====================
    
    def _generate_ranking_on_demand(self, user_id: str, source_key: str) -> List[UUID]:
        """
        云端实时生成排序表
        
        当预生成的排序表不存在时调用此方法：
        1. 获取今日 CS 论文候选池
        2. 使用 Embedding 相似度排序
        3. 冷启动用户使用时间排序
        
        Args:
            user_id: 用户 ID
            source_key: 数据源键 (如 arxiv_day_20260103)
            
        Returns:
            排序后的论文 ID 列表
        """
        import numpy as np
        from app.models import PaperEmbedding
        from app.core.config import settings
        from sqlalchemy import cast, Date
        
        # 1. 从 source_key 解析目标日期
        # source_key 格式: arxiv_day_YYYYMMDD
        try:
            date_str = source_key.replace(self.SOURCE_PREFIX, "")
            target_date = date(int(date_str[:4]), int(date_str[4:6]), int(date_str[6:8]))
        except (ValueError, IndexError):
            logger.error(f"无法解析 source_key: {source_key}")
            return []
        
        # 2. 获取目标日期的 CS 论文
        papers = self._get_cs_papers_by_date(target_date)
        if not papers:
            logger.warning(f"目标日期 {target_date} 无 CS 论文")
            return []
        
        paper_ids = [p.id for p in papers]
        logger.info(f"找到 {len(paper_ids)} 篇目标日期 CS 论文")
        
        # 3. 获取用户向量
        user_vector = self._get_user_profile_vector(user_id)
        
        if user_vector is not None:
            # 4. 使用 Embedding 相似度排序
            sorted_ids = self._rank_by_embedding_similarity(paper_ids, user_vector)
        else:
            # 5. 冷启动：按时间倒序
            logger.info(f"用户 {user_id} 无反馈数据，使用时间排序")
            sorted_ids = paper_ids  # 已按时间排序
        
        # 6. (可选) 保存生成的排序表供后续使用
        self._save_generated_ranking(user_id, source_key, sorted_ids)
        
        return sorted_ids
    
    def _get_cs_papers_by_date(self, target_date: date) -> List[Paper]:
        """获取指定日期的 CS 分类论文 (考虑时区)"""
        from sqlalchemy import text
        
        # 云端存储 UTC，本地存储 +08:00，需要统一用 Asia/Shanghai 时区比较
        stmt = select(Paper).where(
            text("(submitted_date AT TIME ZONE 'Asia/Shanghai')::date = :target_date"),
            Paper.source == 'arxiv',
            Paper.primary_category.like('cs.%')
        ).order_by(Paper.submitted_date.desc())
        
        return list(self.session.execute(stmt, {"target_date": target_date}).scalars().all())
    
    def _get_user_profile_vector(self, user_id: str):
        """获取用户偏好向量 (从 like/bookmark 论文计算)"""
        import numpy as np
        from sqlalchemy import cast, String
        from app.models import PaperEmbedding
        from app.core.config import settings
        
        # 查询用户正向反馈的论文 Embedding
        stmt = (
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
        
        vectors = [np.array(vec, dtype=np.float32) for vec in self.session.execute(stmt).scalars().all() if vec]
        
        if not vectors:
            return None
        
        # 计算平均向量并归一化
        stacked = np.vstack(vectors)
        profile = stacked.mean(axis=0)
        norm = np.linalg.norm(profile)
        
        if norm == 0:
            return None
        
        return profile / norm
    
    def _rank_by_embedding_similarity(self, paper_ids: List[UUID], user_vector) -> List[UUID]:
        """使用 Embedding 相似度对论文排序"""
        import numpy as np
        from app.models import PaperEmbedding
        from app.core.config import settings
        
        # 批量获取论文 Embedding
        stmt = select(PaperEmbedding.paper_id, PaperEmbedding.vector).where(
            PaperEmbedding.paper_id.in_(paper_ids),
            PaperEmbedding.model_name == settings.embedding_model_name
        )
        
        id_to_vector = {}
        for paper_id, vector in self.session.execute(stmt).all():
            if vector:
                id_to_vector[paper_id] = np.array(vector, dtype=np.float32)
        
        # 计算相似度
        scores = []
        valid_ids = []
        for pid in paper_ids:
            if pid in id_to_vector:
                vec = id_to_vector[pid]
                vec_norm = np.linalg.norm(vec)
                if vec_norm > 0:
                    similarity = float(np.dot(user_vector, vec / vec_norm))
                    scores.append(similarity)
                    valid_ids.append(pid)
        
        if not valid_ids:
            return paper_ids  # 无 Embedding，返回原顺序
        
        # 按相似度降序排序
        sorted_indices = np.argsort(scores)[::-1]
        sorted_ids = [valid_ids[i] for i in sorted_indices]
        
        # 添加没有 Embedding 的论文到末尾
        missing_ids = [pid for pid in paper_ids if pid not in id_to_vector]
        sorted_ids.extend(missing_ids)
        
        logger.info(f"Embedding 排序完成: {len(sorted_ids)} 篇 (有向量: {len(valid_ids)}, 无向量: {len(missing_ids)})")
        return sorted_ids
    
    def _save_generated_ranking(self, user_id: str, source_key: str, paper_ids: List[UUID]):
        """保存生成的排序表"""
        try:
            from app.models import UserPaperRanking
            
            # 检查是否已存在
            existing = self.session.query(UserPaperRanking).filter(
                UserPaperRanking.user_id == user_id,
                UserPaperRanking.source_key == source_key
            ).first()
            
            if existing:
                return  # 已存在，跳过
            
            ranking = UserPaperRanking(
                user_id=user_id,
                source_key=source_key,
                pool_date=date.today(),
                paper_ids=paper_ids,
                scores=[]  # 空列表满足 NOT NULL 约束
            )
            self.session.add(ranking)
            self.session.commit()
            logger.info(f"已保存生成的排序表: user={user_id}, source={source_key}, papers={len(paper_ids)}")
        except Exception as e:
            logger.error(f"保存排序表失败: {e}")
            self.session.rollback()
