"""
每日数据处理调度器
按顺序执行: 论文获取 -> CS候选池 -> 用户推荐

用法:
    python -m app.jobs.daily_scheduler
    python -m app.jobs.daily_scheduler --target-date 2025-12-29
"""
from __future__ import annotations

import argparse
import time
from typing import Optional

import pendulum
from loguru import logger

from app.jobs.fetch_arxiv import main as fetch_arxiv_main
from app.jobs.generate_cs_pool import main as generate_cs_pool_main
from app.jobs.generate_user_recommendations import main as generate_recommendations_main


def main(argv: Optional[list[str]] = None) -> int:
    """
    每日数据处理调度器
    
    执行顺序:
    1. 获取arXiv论文
    2. 生成CS候选池
    3. 生成用户推荐
    """
    parser = argparse.ArgumentParser(description="每日数据处理调度器")
    parser.add_argument(
        "--target-date",
        type=str,
        default=None,
        help="指定日期 (YYYY-MM-DD)，默认使用 T-3",
    )
    parser.add_argument(
        "--skip-fetch",
        action="store_true",
        help="跳过论文获取步骤",
    )
    parser.add_argument(
        "--skip-pool",
        action="store_true",
        help="跳过候选池生成步骤",
    )
    parser.add_argument(
        "--skip-recommend",
        action="store_true",
        help="跳过推荐生成步骤",
    )
    args = parser.parse_args(argv)

    start_time = time.time()
    date_args = ["--target-date", args.target_date] if args.target_date else []
    
    logger.info("=== 开始每日数据处理 ===")
    if args.target_date:
        logger.info("目标日期: {}", args.target_date)
    else:
        from app.core.config import settings
        target = pendulum.now("America/New_York").subtract(days=settings.arxiv_submission_delay_days).date()
        logger.info("目标日期: {} (T-{})", target, settings.arxiv_submission_delay_days)
    
    results = {}
    
    # Step 1: 获取论文
    if not args.skip_fetch:
        logger.info("\n[1/3] 获取arXiv论文...")
        step_start = time.time()
        ret = fetch_arxiv_main(date_args)
        results["fetch"] = {"code": ret, "time": time.time() - step_start}
        if ret != 0:
            logger.error("论文获取失败，终止后续步骤")
            return ret
    else:
        logger.info("[1/3] 跳过论文获取")
        results["fetch"] = {"code": "skipped", "time": 0}
    
    # Step 2: 生成CS候选池
    if not args.skip_pool:
        logger.info("\n[2/3] 生成CS候选池...")
        step_start = time.time()
        ret = generate_cs_pool_main(date_args)
        results["pool"] = {"code": ret, "time": time.time() - step_start}
        if ret != 0:
            logger.error("候选池生成失败，终止后续步骤")
            return ret
    else:
        logger.info("[2/3] 跳过候选池生成")
        results["pool"] = {"code": "skipped", "time": 0}
    
    # Step 3: 生成用户推荐
    if not args.skip_recommend:
        logger.info("\n[3/3] 生成用户推荐...")
        step_start = time.time()
        ret = generate_recommendations_main(date_args)
        results["recommend"] = {"code": ret, "time": time.time() - step_start}
    else:
        logger.info("[3/3] 跳过推荐生成")
        results["recommend"] = {"code": "skipped", "time": 0}
    
    # 汇总结果
    total_time = time.time() - start_time
    logger.info("\n=== 每日数据处理完成 ===")
    logger.info("总耗时: {:.1f}s", total_time)
    for step, result in results.items():
        if result["code"] == "skipped":
            logger.info("  {}: 跳过", step)
        elif result["code"] == 0:
            logger.info("  {}: ✅ 成功 ({:.1f}s)", step, result["time"])
        else:
            logger.info("  {}: ❌ 失败 (code={})", step, result["code"])
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
