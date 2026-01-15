"""
CS候选池生成任务
从当日论文中筛选CS领域论文
"""
from __future__ import annotations

import argparse
from typing import Optional

import pendulum
from loguru import logger

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.data_ingestion.arxiv_candidate_pool import CandidatePoolServiceV2, cs_filter


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
    生成CS候选论文池
    
    Returns:
        退出码 (0=成功, 非0=失败)
    """
    parser = argparse.ArgumentParser(description="生成CS候选论文池")
    parser.add_argument(
        "--target-date",
        type=str,
        default=None,
        help="指定日期 (YYYY-MM-DD)，默认使用 T-3",
    )
    args = parser.parse_args(argv)

    target_date = get_target_date(args.target_date)
    logger.info("生成 {} 的CS候选池", target_date)

    try:
        with SessionLocal() as session:
            paper_ids = CandidatePoolServiceV2.create_filtered_pool_by_date(
                session=session,
                target_date=target_date,
                filter_type='cs',
                filter_func=cs_filter
            )
            session.commit()
            logger.success("CS候选池生成完成: {} 篇论文", len(paper_ids))
        return 0
        
    except Exception as e:
        logger.exception("CS候选池生成失败: {}", e)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
