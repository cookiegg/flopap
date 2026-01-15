#!/usr/bin/env python3
"""arXiv数据源内容生成脚本 - 为arXiv论文生成翻译和AI解读"""

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import List, Optional
from uuid import UUID

import pendulum
from loguru import logger
from sqlalchemy import select

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.db.session import SessionLocal
from app.models import IngestionBatch, Paper
from app.services.translation_pure import translate_and_save_papers
from app.services.ai_interpretation_pure import interpret_and_save_papers


class ArxivContentGenerator:
    """arXiv数据源内容生成器"""
    
    def __init__(self):
        self.session = SessionLocal()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
    
    def get_arxiv_papers_by_date(self, source_date: date) -> List[UUID]:
        """获取指定日期的arXiv论文ID列表"""
        # 查找指定日期的摄取批次
        batch_stmt = (
            select(IngestionBatch)
            .where(IngestionBatch.source_date == source_date)
            .order_by(IngestionBatch.created_at.desc())
        )
        batch = self.session.scalar(batch_stmt)
        
        if not batch:
            logger.warning("未找到日期 {} 的arXiv摄取批次", source_date)
            return []
        
        # 获取该批次的所有论文ID
        papers_stmt = (
            select(Paper.id)
            .where(Paper.ingestion_batch_id == batch.id)
        )
        paper_ids = list(self.session.execute(papers_stmt).scalars())
        
        logger.info("找到日期 {} 的arXiv论文: {} 篇", source_date, len(paper_ids))
        return paper_ids
    
    def get_arxiv_papers_by_batch(self, batch_id: UUID) -> List[UUID]:
        """获取指定批次的arXiv论文ID列表"""
        papers_stmt = (
            select(Paper.id)
            .where(Paper.ingestion_batch_id == batch_id)
        )
        paper_ids = list(self.session.execute(papers_stmt).scalars())
        
        logger.info("找到批次 {} 的arXiv论文: {} 篇", batch_id, len(paper_ids))
        return paper_ids
    
    def get_latest_arxiv_papers(self) -> List[UUID]:
        """获取最新arXiv批次的论文ID列表"""
        # 获取最新的摄取批次
        batch_stmt = (
            select(IngestionBatch)
            .order_by(IngestionBatch.source_date.desc(), IngestionBatch.created_at.desc())
            .limit(1)
        )
        batch = self.session.scalar(batch_stmt)
        
        if not batch:
            logger.warning("未找到任何arXiv摄取批次")
            return []
        
        return self.get_arxiv_papers_by_batch(batch.id)
    
    def generate_daily_content(
        self,
        source_date: Optional[date] = None,
        include_translation: bool = True,
        include_interpretation: bool = True,
        max_workers: int = 30
    ) -> dict:
        """
        为arXiv每日新增论文生成内容
        
        Args:
            source_date: 目标日期，默认为3天前
            include_translation: 是否生成翻译
            include_interpretation: 是否生成AI解读
            max_workers: 并发线程数
            
        Returns:
            生成结果统计
        """
        if source_date is None:
            source_date = pendulum.now("UTC").subtract(days=3).date()
        
        logger.info("开始为arXiv日期 {} 生成内容", source_date)
        
        # 获取论文ID列表
        paper_ids = self.get_arxiv_papers_by_date(source_date)
        if not paper_ids:
            return {"error": "未找到论文"}
        
        results = {
            "source_date": source_date.isoformat(),
            "total_papers": len(paper_ids),
            "translation_count": 0,
            "interpretation_count": 0
        }
        
        # 生成翻译
        if include_translation:
            logger.info("开始生成翻译...")
            translation_count = translate_and_save_papers(
                self.session, paper_ids, max_workers
            )
            results["translation_count"] = translation_count
            logger.success("翻译完成: {} 篇", translation_count)
        
        # 生成AI解读
        if include_interpretation:
            logger.info("开始生成AI解读...")
            interpretation_count = interpret_and_save_papers(
                self.session, paper_ids, max_workers // 2  # AI解读更耗时，减少并发
            )
            results["interpretation_count"] = interpretation_count
            logger.success("AI解读完成: {} 篇", interpretation_count)
        
        return results
    
    def generate_batch_content(
        self,
        batch_id: UUID,
        include_translation: bool = True,
        include_interpretation: bool = True,
        max_workers: int = 30
    ) -> dict:
        """
        为指定arXiv批次生成内容
        
        Args:
            batch_id: 批次ID
            include_translation: 是否生成翻译
            include_interpretation: 是否生成AI解读
            max_workers: 并发线程数
            
        Returns:
            生成结果统计
        """
        logger.info("开始为arXiv批次 {} 生成内容", batch_id)
        
        # 获取论文ID列表
        paper_ids = self.get_arxiv_papers_by_batch(batch_id)
        if not paper_ids:
            return {"error": "未找到论文"}
        
        results = {
            "batch_id": str(batch_id),
            "total_papers": len(paper_ids),
            "translation_count": 0,
            "interpretation_count": 0
        }
        
        # 生成翻译
        if include_translation:
            logger.info("开始生成翻译...")
            translation_count = translate_and_save_papers(
                self.session, paper_ids, max_workers
            )
            results["translation_count"] = translation_count
            logger.success("翻译完成: {} 篇", translation_count)
        
        # 生成AI解读
        if include_interpretation:
            logger.info("开始生成AI解读...")
            interpretation_count = interpret_and_save_papers(
                self.session, paper_ids, max_workers // 2
            )
            results["interpretation_count"] = interpretation_count
            logger.success("AI解读完成: {} 篇", interpretation_count)
        
        return results
    
    def generate_latest_content(
        self,
        include_translation: bool = True,
        include_interpretation: bool = True,
        max_workers: int = 30
    ) -> dict:
        """
        为最新arXiv批次生成内容
        
        Args:
            include_translation: 是否生成翻译
            include_interpretation: 是否生成AI解读
            max_workers: 并发线程数
            
        Returns:
            生成结果统计
        """
        logger.info("开始为最新arXiv批次生成内容")
        
        # 获取论文ID列表
        paper_ids = self.get_latest_arxiv_papers()
        if not paper_ids:
            return {"error": "未找到论文"}
        
        results = {
            "total_papers": len(paper_ids),
            "translation_count": 0,
            "interpretation_count": 0
        }
        
        # 生成翻译
        if include_translation:
            logger.info("开始生成翻译...")
            translation_count = translate_and_save_papers(
                self.session, paper_ids, max_workers
            )
            results["translation_count"] = translation_count
            logger.success("翻译完成: {} 篇", translation_count)
        
        # 生成AI解读
        if include_interpretation:
            logger.info("开始生成AI解读...")
            interpretation_count = interpret_and_save_papers(
                self.session, paper_ids, max_workers // 2
            )
            results["interpretation_count"] = interpretation_count
            logger.success("AI解读完成: {} 篇", interpretation_count)
        
        return results


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="arXiv数据源内容生成")
    parser.add_argument("--date", help="指定日期 (YYYY-MM-DD)")
    parser.add_argument("--batch-id", help="指定批次ID")
    parser.add_argument("--latest", action="store_true", help="处理最新批次")
    parser.add_argument("--no-translation", action="store_true", help="跳过翻译")
    parser.add_argument("--no-interpretation", action="store_true", help="跳过AI解读")
    parser.add_argument("--workers", type=int, default=30, help="并发线程数")
    
    args = parser.parse_args()
    
    # 参数验证
    if not any([args.date, args.batch_id, args.latest]):
        parser.error("必须指定 --date, --batch-id 或 --latest 之一")
    
    try:
        with ArxivContentGenerator() as generator:
            if args.date:
                # 按日期生成
                source_date = pendulum.parse(args.date).date()
                results = generator.generate_daily_content(
                    source_date=source_date,
                    include_translation=not args.no_translation,
                    include_interpretation=not args.no_interpretation,
                    max_workers=args.workers
                )
            elif args.batch_id:
                # 按批次ID生成
                batch_id = UUID(args.batch_id)
                results = generator.generate_batch_content(
                    batch_id=batch_id,
                    include_translation=not args.no_translation,
                    include_interpretation=not args.no_interpretation,
                    max_workers=args.workers
                )
            else:
                # 最新批次生成
                results = generator.generate_latest_content(
                    include_translation=not args.no_translation,
                    include_interpretation=not args.no_interpretation,
                    max_workers=args.workers
                )
            
            if "error" in results:
                logger.error("生成失败: {}", results["error"])
                return 1
            
            logger.success("arXiv内容生成完成: {}", results)
            return 0
            
    except Exception as e:
        logger.error("arXiv内容生成失败: {}", str(e))
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
