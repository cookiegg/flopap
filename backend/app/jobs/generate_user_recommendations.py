"""
用户推荐池生成任务
为所有用户生成个性化推荐
"""
from __future__ import annotations

import argparse
from typing import Optional

import pendulum
from loguru import logger

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User
from app.services.data_ingestion.arxiv_candidate_pool import CandidatePoolServiceV2
from app.services.recommendation.user_ranking_service import UserRankingService
from app.services.recommendation.recommendation_facade import RecommendationFacade


def get_target_date(override: Optional[str]) -> pendulum.Date:
    """计算目标日期"""
    if override:
        try:
            return pendulum.parse(override).date()
        except Exception as exc:
            logger.error("无法解析日期 {}: {}", override, exc)
            raise SystemExit(2)
    
    now_et = pendulum.now("America/New_York")
    return now_et.subtract(days=settings.arxiv_submission_delay_days).date()


def main(argv: Optional[list[str]] = None) -> int:
    """
    为所有用户生成推荐池
    
    Returns:
        退出码 (0=成功, 非0=失败)
    """
    parser = argparse.ArgumentParser(description="生成用户推荐池")
    parser.add_argument(
        "--target-date",
        type=str,
        default=None,
        help="指定日期 (YYYY-MM-DD)，默认使用 T-3",
    )
    parser.add_argument(
        "--pool-ratio",
        type=float,
        default=0.1,
        help="推荐比例 (默认 0.1 即 10%%)",
    )
    args = parser.parse_args(argv)

    target_date = get_target_date(args.target_date)
    logger.info("生成 {} 的用户推荐池, 比例={}", target_date, args.pool_ratio)

    try:
        with SessionLocal() as session:
            # 获取所有用户
            users = session.query(User).all()
            logger.info("找到 {} 个用户", len(users))
            
            # 获取CS候选池
            cs_paper_ids = CandidatePoolServiceV2.get_candidate_papers_by_date(
                session=session,
                target_date=target_date,
                filter_type='cs'
            )
            
            if not cs_paper_ids:
                logger.warning("CS候选池为空，请先运行 generate_cs_pool")
                return 1
            
            logger.info("CS候选池: {} 篇论文", len(cs_paper_ids))
            
            # 初始化服务
            ranking_service = UserRankingService(session)
            facade = RecommendationFacade(session)
            
            success_count = 0
            for user in users:
                try:
                    # 生成排序表
                    source_key = f'arxiv_day_{target_date.strftime("%Y%m%d")}'
                    ranking_success = ranking_service.update_user_ranking(
                        user_id=user.id,
                        source_key=source_key,
                        paper_ids=cs_paper_ids,
                        force_update=True
                    )
                    
                    if ranking_success:
                        # 获取推荐
                        recommendations = facade.get_user_recommendations(
                            user_id=user.id,
                            source_key=source_key,
                            pool_ratio=args.pool_ratio
                        )
                        logger.debug("用户 {}: {} 篇推荐", user.id, len(recommendations) if recommendations else 0)
                        success_count += 1
                        
                except Exception as e:
                    logger.warning("用户 {} 推荐生成失败: {}", user.id, e)
            
            session.commit()
            logger.success("推荐池生成完成: {}/{} 用户成功", success_count, len(users))
        return 0
        
    except Exception as e:
        logger.exception("推荐池生成失败: {}", e)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
