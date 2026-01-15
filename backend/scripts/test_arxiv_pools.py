#!/usr/bin/env python3
"""
临时测试脚本 V2: 使用现有数据生成完整的 D0-D6 推荐池
"""
import sys
from pathlib import Path
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(backend_root))

from datetime import date, timedelta
from loguru import logger

from app.db.session import SessionLocal
from app.models.user import User
from app.models import Paper
from app.services.recommendation.user_ranking_service import UserRankingService
from app.services.recommendation.arxiv_pool_service import ArxivPoolService
from sqlalchemy import select, and_, func


def get_dates_with_papers(db, limit=7):
    """获取有 CS 论文的日期列表 (降序)"""
    stmt = (
        select(func.date(Paper.submitted_date))
        .where(Paper.primary_category.like('cs.%'))
        .group_by(func.date(Paper.submitted_date))
        .order_by(func.date(Paper.submitted_date).desc())
        .limit(limit)
    )
    return [row[0] for row in db.execute(stmt).all()]


def generate_test_pools():
    """使用现有数据生成完整的 D0-D6 推荐池"""
    
    today = date.today()
    db = SessionLocal()
    
    try:
        # 获取用户
        users = db.query(User).all()
        logger.info(f"找到 {len(users)} 个用户")
        
        ranking_service = UserRankingService(db)
        
        # 获取有数据的 7 个日期
        paper_dates = get_dates_with_papers(db, 7)
        logger.info(f"找到 {len(paper_dates)} 个有论文的日期: {paper_dates}")
        
        if len(paper_dates) < 7:
            logger.warning(f"只有 {len(paper_dates)} 天有数据，不足 7 天，将复用数据")
        
        # 生成 D0-D6 池
        for user in users:
            logger.info(f"\n=== 用户 {user.id} ===")
            
            for day_offset in range(7):
                # 映射: D0 用最新日期, D1 用第二新...
                paper_date_index = min(day_offset, len(paper_dates) - 1)
                paper_date = paper_dates[paper_date_index]
                
                # 获取该日期的 CS 论文
                papers_stmt = select(Paper.id).where(
                    and_(
                        Paper.primary_category.like('cs.%'),
                        func.date(Paper.submitted_date) == paper_date
                    )
                ).limit(100)  # 每天限制100篇
                
                paper_ids = list(db.execute(papers_stmt).scalars().all())
                
                if not paper_ids:
                    logger.debug(f"  D{day_offset}: 无论文")
                    continue
                
                # 使用今天的日期减去 offset 作为 source_key
                pool_date = today - timedelta(days=day_offset)
                source_key = f"{ArxivPoolService.SOURCE_PREFIX}{pool_date.strftime('%Y%m%d')}"
                
                # 生成排序
                success = ranking_service.update_user_ranking(
                    user_id=user.id,
                    source_key=source_key,
                    paper_ids=paper_ids,
                    force_update=True
                )
                
                if success:
                    logger.info(f"  D{day_offset} ({pool_date}): 用 {paper_date} 的 {len(paper_ids)} 篇论文 -> {source_key}")
                else:
                    logger.warning(f"  D{day_offset}: 生成失败")
        
        logger.info("\n=== 测试池生成完成 ===")
        
        # 测试读取
        logger.info("\n=== 测试读取 ===")
        arxiv_service = ArxivPoolService(db)
        
        test_user_id = users[0].id if users else 'default'
        
        today_pool = arxiv_service.get_today_pool(test_user_id)
        week_pool = arxiv_service.get_week_pool(test_user_id)
        
        logger.info(f"用户 {test_user_id}:")
        logger.info(f"  Today Pool: {len(today_pool)} 篇")
        logger.info(f"  Week Pool: {len(week_pool)} 篇")
        logger.info(f"  比例: Week/Today = {len(week_pool)/max(1,len(today_pool)):.1f}x")
        
        stats = arxiv_service.get_pool_stats(test_user_id)
        logger.info(f"  统计: today={stats['today_count']}, week_total={stats['week_count']}")
        for day_stat in stats['week_days']:
            logger.info(f"    {day_stat['date']}: {day_stat['count']} 篇")
        
    except Exception as e:
        logger.exception(f"生成失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    generate_test_pools()
