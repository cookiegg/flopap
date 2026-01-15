#!/usr/bin/env python3
"""用户推荐内容生成脚本 - 为用户推荐的论文生成翻译和AI解读"""

import argparse
import sys
from pathlib import Path
from typing import List
from uuid import UUID

import pendulum
from loguru import logger
from sqlalchemy import select

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.db.session import SessionLocal
from app.models import DailyRecommendationPool, Paper, PaperTranslation
from app.services.translation_pure import translate_and_save_papers
from app.services.ai_interpretation_pure import interpret_and_save_papers


class UserRecommendationContentGenerator:
    """用户推荐内容生成器"""
    
    def __init__(self):
        self.session = SessionLocal()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
    
    def get_daily_recommendation_papers(self, pool_date: pendulum.Date = None) -> List[UUID]:
        """获取日推荐池中的论文ID列表"""
        if pool_date is None:
            pool_date = pendulum.now("UTC").date()
        
        stmt = (
            select(Paper.id)
            .join(DailyRecommendationPool, Paper.id == DailyRecommendationPool.paper_id)
            .where(
                DailyRecommendationPool.pool_date == pool_date,
                DailyRecommendationPool.is_active.is_(True)
            )
        )
        
        paper_ids = list(self.session.execute(stmt).scalars())
        
        logger.info("找到日期 {} 的推荐池论文: {} 篇", pool_date, len(paper_ids))
        return paper_ids
    
    def get_papers_missing_translation(self, paper_ids: List[UUID]) -> List[UUID]:
        """获取缺少翻译的论文ID列表"""
        missing_ids = []
        
        for paper_id in paper_ids:
            existing = self.session.scalar(
                select(PaperTranslation).where(PaperTranslation.paper_id == paper_id)
            )
            if not existing or not existing.title_zh or not existing.summary_zh:
                missing_ids.append(paper_id)
        
        logger.info("缺少翻译的论文: {} 篇", len(missing_ids))
        return missing_ids
    
    def get_papers_missing_interpretation(self, paper_ids: List[UUID]) -> List[UUID]:
        """获取缺少AI解读的论文ID列表"""
        missing_ids = []
        
        for paper_id in paper_ids:
            existing = self.session.scalar(
                select(PaperTranslation).where(PaperTranslation.paper_id == paper_id)
            )
            if not existing or not existing.ai_interpretation:
                missing_ids.append(paper_id)
        
        logger.info("缺少AI解读的论文: {} 篇", len(missing_ids))
        return missing_ids
    
    def generate_user_recommendation_content(
        self,
        paper_ids: List[UUID] = None,
        pool_date: pendulum.Date = None,
        include_translation: bool = True,
        include_interpretation: bool = True,
        max_workers: int = 30,
        only_missing: bool = True
    ) -> dict:
        """
        为用户推荐论文生成内容
        
        Args:
            paper_ids: 指定的论文ID列表，如果为None则使用推荐池
            pool_date: 推荐池日期，默认为今天
            include_translation: 是否生成翻译
            include_interpretation: 是否生成AI解读
            max_workers: 并发线程数
            only_missing: 是否只处理缺失的内容
            
        Returns:
            生成结果统计
        """
        if paper_ids is None:
            paper_ids = self.get_daily_recommendation_papers(pool_date)
        
        if not paper_ids:
            return {"error": "未找到需要处理的论文"}
        
        logger.info("开始为用户推荐论文生成内容: {} 篇", len(paper_ids))
        
        results = {
            "total_papers": len(paper_ids),
            "translation_count": 0,
            "interpretation_count": 0,
            "pool_date": (pool_date or pendulum.now("UTC").date()).isoformat()
        }
        
        # 生成翻译
        if include_translation:
            translation_paper_ids = paper_ids
            if only_missing:
                translation_paper_ids = self.get_papers_missing_translation(paper_ids)
            
            if translation_paper_ids:
                logger.info("开始生成翻译: {} 篇", len(translation_paper_ids))
                translation_count = translate_and_save_papers(
                    self.session, translation_paper_ids, max_workers, force_retranslate=not only_missing
                )
                results["translation_count"] = translation_count
                logger.success("翻译完成: {} 篇", translation_count)
            else:
                logger.info("所有论文都已有翻译")
        
        # 生成AI解读
        if include_interpretation:
            interpretation_paper_ids = paper_ids
            if only_missing:
                interpretation_paper_ids = self.get_papers_missing_interpretation(paper_ids)
            
            if interpretation_paper_ids:
                logger.info("开始生成AI解读: {} 篇", len(interpretation_paper_ids))
                interpretation_count = interpret_and_save_papers(
                    self.session, interpretation_paper_ids, max_workers // 2, force_regenerate=not only_missing
                )
                results["interpretation_count"] = interpretation_count
                logger.success("AI解读完成: {} 篇", interpretation_count)
            else:
                logger.info("所有论文都已有AI解读")
        
        return results
    
    def generate_daily_pool_content(
        self,
        pool_date: pendulum.Date = None,
        include_translation: bool = True,
        include_interpretation: bool = True,
        max_workers: int = 30
    ) -> dict:
        """
        为日推荐池生成内容
        
        Args:
            pool_date: 推荐池日期，默认为今天
            include_translation: 是否生成翻译
            include_interpretation: 是否生成AI解读
            max_workers: 并发线程数
            
        Returns:
            生成结果统计
        """
        return self.generate_user_recommendation_content(
            paper_ids=None,
            pool_date=pool_date,
            include_translation=include_translation,
            include_interpretation=include_interpretation,
            max_workers=max_workers,
            only_missing=True
        )


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="用户推荐内容生成")
    parser.add_argument("--date", help="推荐池日期 (YYYY-MM-DD)，默认为今天")
    parser.add_argument("--paper-ids", nargs="+", help="指定论文ID列表")
    parser.add_argument("--no-translation", action="store_true", help="跳过翻译")
    parser.add_argument("--no-interpretation", action="store_true", help="跳过AI解读")
    parser.add_argument("--workers", type=int, default=30, help="并发线程数")
    parser.add_argument("--force-all", action="store_true", help="强制处理所有论文，不只是缺失的")
    
    args = parser.parse_args()
    
    try:
        with UserRecommendationContentGenerator() as generator:
            # 解析参数
            pool_date = None
            if args.date:
                pool_date = pendulum.parse(args.date).date()
            
            paper_ids = None
            if args.paper_ids:
                paper_ids = [UUID(pid) for pid in args.paper_ids]
            
            # 生成内容
            results = generator.generate_user_recommendation_content(
                paper_ids=paper_ids,
                pool_date=pool_date,
                include_translation=not args.no_translation,
                include_interpretation=not args.no_interpretation,
                max_workers=args.workers,
                only_missing=not args.force_all
            )
            
            if "error" in results:
                logger.error("生成失败: {}", results["error"])
                return 1
            
            logger.success("用户推荐内容生成完成: {}", results)
            return 0
            
    except Exception as e:
        logger.error("用户推荐内容生成失败: {}", str(e))
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
