"""
arXiv论文抓取任务
每日定时运行，获取指定日期提交的论文
"""
from __future__ import annotations

import argparse
import sys
from typing import Optional

import pendulum
from loguru import logger

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.data_ingestion.ingestion import ingest_for_date


def get_target_date(override: Optional[str]) -> pendulum.Date:
    """
    计算目标日期
    
    Args:
        override: 手动指定的日期字符串 (YYYY-MM-DD)
        
    Returns:
        目标日期对象
    """
    if override:
        try:
            parsed = pendulum.parse(override)
            return parsed.date()
        except Exception as exc:
            logger.error("无法解析日期 {}: {}", override, exc)
            raise SystemExit(2)
    
    # 使用美东时间计算目标日期（arXiv基于美东时间发布）
    now_et = pendulum.now("America/New_York")
    target_et = now_et.subtract(days=settings.arxiv_submission_delay_days)
    logger.debug(
        "当前美东时间: {}, 目标日期: {}", 
        now_et.format("YYYY-MM-DD HH:mm:ss"), 
        target_et.format("YYYY-MM-DD")
    )
    return target_et.date()


def main(argv: Optional[list[str]] = None) -> int:
    """
    主函数：抓取并入库arXiv论文
    
    Args:
        argv: 命令行参数列表
        
    Returns:
        退出码 (0=成功, 非0=失败)
    """
    parser = argparse.ArgumentParser(
        description="抓取并入库指定日期提交的arXiv论文"
    )
    parser.add_argument(
        "--target-date",
        type=str,
        default=None,
        help="指定抓取的提交日期 (YYYY-MM-DD)，默认使用当前日期减去配置的延迟天数",
    )
    args = parser.parse_args(argv)

    target_date = get_target_date(args.target_date)
    logger.info("准备抓取 {} 的论文", target_date)

    try:
        with SessionLocal() as session:
            batch = ingest_for_date(session, target_date)
            # ingest_for_date内部已经commit，这里作为安全网
            session.commit()
            logger.success(
                "抓取完成: 批次ID={}, 论文数={}", 
                batch.id, 
                batch.item_count
            )
        return 0
        
    except Exception as e:
        logger.exception("抓取失败: {}", e)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
