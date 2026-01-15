"""
候选池服务 V2 - 基于 submitted_date 的时间分区设计
"""
from __future__ import annotations

from datetime import date, datetime, time, timezone
from typing import List
from uuid import UUID, uuid5, NAMESPACE_DNS

from loguru import logger
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import CandidatePool, Paper


def date_to_uuid(target_date: date) -> UUID:
    """将日期转换为确定性的UUID"""
    date_str = target_date.isoformat()
    return uuid5(NAMESPACE_DNS, f"candidate_pool_date_{date_str}")


class CandidatePoolServiceV2:
    """基于时间分区的候选池服务"""
    
    @staticmethod
    def create_filtered_pool_by_date(
        session: Session,
        target_date: date,
        filter_type: str,
        filter_func: callable
    ) -> List[UUID]:
        """基于提交日期创建筛选后的候选池"""
        date_uuid = date_to_uuid(target_date)
        
        # 1. 清除旧的候选池 (DELETE)
        session.execute(
            delete(CandidatePool).where(
                CandidatePool.batch_id == date_uuid,
                CandidatePool.filter_type == filter_type
            )
        )
        
        # 使用日期转换，忽略时区差异
        from sqlalchemy import cast, Date
        stmt = select(Paper).where(
            cast(Paper.submitted_date, Date) == target_date
        )
        papers = session.execute(stmt).scalars().all()
        
        # 3. 重新应用筛选逻辑 (FILTER)
        # 4. 重新插入候选池 (INSERT)
        filtered_paper_ids = []
        for paper in papers:
            if filter_func(paper):
                candidate = CandidatePool(
                    batch_id=date_uuid,
                    paper_id=paper.id,
                    filter_type=filter_type
                )
                session.add(candidate)
                filtered_paper_ids.append(paper.id)
        
        session.flush()
        logger.info(f"日期 {target_date} 筛选类型 {filter_type}: {len(filtered_paper_ids)} 篇论文")
        return filtered_paper_ids
    
    @staticmethod
    def get_candidate_papers_by_date(
        session: Session,
        target_date: date,
        filter_type: str
    ) -> List[UUID]:
        """获取指定日期候选池中的论文ID列表"""
        date_uuid = date_to_uuid(target_date)
        
        stmt = (
            select(CandidatePool.paper_id)
            .where(
                CandidatePool.batch_id == date_uuid,
                CandidatePool.filter_type == filter_type
            )
        )
        return list(session.execute(stmt).scalars().all())
    
    @staticmethod
    def get_papers_by_date_range(
        session: Session,
        start_date: date,
        end_date: date,
        filter_func: callable = None
    ) -> List[UUID]:
        """获取日期范围内的论文ID列表 (不依赖候选池)"""
        # 使用日期转换，忽略时区差异
        from sqlalchemy import cast, Date
        stmt = select(Paper.id).where(
            cast(Paper.submitted_date, Date) >= start_date,
            cast(Paper.submitted_date, Date) <= end_date
        )
        paper_ids = list(session.execute(stmt).scalars().all())
        
        if filter_func:
            # 需要获取Paper对象来应用筛选函数
            papers_stmt = select(Paper).where(Paper.id.in_(paper_ids))
            papers = session.execute(papers_stmt).scalars().all()
            filtered_ids = [paper.id for paper in papers if filter_func(paper)]
            return filtered_ids
        
        return paper_ids
    
    @staticmethod
    def get_date_statistics(
        session: Session,
        target_date: date
    ) -> dict:
        """获取指定日期的统计信息"""
        # 使用日期转换，忽略时区差异
        from sqlalchemy import cast, Date
        
        # 总论文数
        total_stmt = select(Paper.id).where(
            cast(Paper.submitted_date, Date) == target_date
        )
        total_count = len(list(session.execute(total_stmt).scalars().all()))
        
        # 各筛选类型的统计
        date_uuid = date_to_uuid(target_date)
        filter_stats = {}
        stmt = select(CandidatePool.filter_type, CandidatePool.paper_id).where(
            CandidatePool.batch_id == date_uuid
        )
        results = session.execute(stmt).all()
        
        for filter_type, paper_id in results:
            if filter_type not in filter_stats:
                filter_stats[filter_type] = 0
            filter_stats[filter_type] += 1
        
        return {
            'target_date': target_date,
            'total_papers': total_count,
            'filter_stats': filter_stats
        }


# 筛选函数
def cs_filter(paper: Paper) -> bool:
    if not paper.categories:
        return False
    return any(cat.startswith('cs.') for cat in paper.categories)


def ai_ml_cv_filter(paper: Paper) -> bool:
    if not paper.categories:
        return False
    target_categories = ['cs.AI', 'cs.LG', 'cs.CV', 'cs.CL', 'cs.RO']
    return any(
        any(cat.startswith(target) for target in target_categories)
        for cat in paper.categories
    )


def math_filter(paper: Paper) -> bool:
    if not paper.categories:
        return False
    return any(cat.startswith('math.') for cat in paper.categories)


def physics_filter(paper: Paper) -> bool:
    if not paper.categories:
        return False
    return any(cat.startswith('physics.') or cat.startswith('astro-ph.') or cat.startswith('cond-mat.') for cat in paper.categories)


def no_filter(paper: Paper) -> bool:
    return True


# 筛选器映射
FILTERS_V2 = {
    'cs': cs_filter,
    'ai-ml-cv': ai_ml_cv_filter,
    'math': math_filter,
    'physics': physics_filter,
    'all': no_filter,
}
