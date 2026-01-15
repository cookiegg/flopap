#!/usr/bin/env python3
"""会议数据源内容生成脚本 - 为会议论文生成翻译和AI解读"""

import argparse
import sys
from pathlib import Path
from typing import List
from uuid import UUID

from loguru import logger
from sqlalchemy import select

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.db.session import SessionLocal
from app.models import ConferenceRecommendationPool, Paper
from app.services.translation_pure import translate_and_save_papers
from app.services.ai_interpretation_pure import interpret_and_save_papers


class ConferenceContentGenerator:
    """会议数据源内容生成器"""
    
    def __init__(self):
        self.session = SessionLocal()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
    
    def get_conference_papers(self, conference_source: str, active_only: bool = True) -> List[UUID]:
        """获取指定会议的论文ID列表"""
        stmt = (
            select(Paper.id)
            .join(ConferenceRecommendationPool, Paper.id == ConferenceRecommendationPool.paper_id)
            .where(ConferenceRecommendationPool.source == conference_source)
        )
        
        if active_only:
            stmt = stmt.where(ConferenceRecommendationPool.is_active.is_(True))
        
        paper_ids = list(self.session.execute(stmt).scalars())
        
        logger.info("找到会议 {} 的论文: {} 篇", conference_source, len(paper_ids))
        return paper_ids
    
    def get_conference_recommendation_pool(self, conference_source: str) -> List[UUID]:
        """获取会议推荐池中的论文ID列表"""
        return self.get_conference_papers(conference_source, active_only=True)
    
    def get_all_conference_papers(self, conference_source: str) -> List[UUID]:
        """获取会议的所有论文ID列表（包括非活跃的）"""
        return self.get_conference_papers(conference_source, active_only=False)
    
    def generate_conference_content(
        self,
        conference_source: str,
        full_conference: bool = False,
        include_translation: bool = True,
        include_interpretation: bool = True,
        max_workers: int = 30
    ) -> dict:
        """
        为会议论文生成内容
        
        Args:
            conference_source: 会议来源 (如 'neurips2025', 'icml2024')
            full_conference: 是否处理整个会议的所有论文，否则只处理推荐池
            include_translation: 是否生成翻译
            include_interpretation: 是否生成AI解读
            max_workers: 并发线程数
            
        Returns:
            生成结果统计
        """
        logger.info("开始为会议 {} 生成内容 (全量: {})", conference_source, full_conference)
        
        # 获取论文ID列表
        if full_conference:
            paper_ids = self.get_all_conference_papers(conference_source)
        else:
            paper_ids = self.get_conference_recommendation_pool(conference_source)
        
        if not paper_ids:
            return {"error": f"未找到会议 {conference_source} 的论文"}
        
        results = {
            "conference_source": conference_source,
            "full_conference": full_conference,
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
    
    def list_available_conferences(self) -> List[str]:
        """列出所有可用的会议来源"""
        stmt = select(ConferenceRecommendationPool.source).distinct()
        sources = list(self.session.execute(stmt).scalars())
        
        logger.info("可用的会议来源: {}", sources)
        return sources


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="会议数据源内容生成")
    parser.add_argument("--conference", help="会议来源 (如 neurips2025, icml2024)")
    parser.add_argument("--full", action="store_true", help="处理整个会议的所有论文")
    parser.add_argument("--no-translation", action="store_true", help="跳过翻译")
    parser.add_argument("--no-interpretation", action="store_true", help="跳过AI解读")
    parser.add_argument("--workers", type=int, default=30, help="并发线程数")
    parser.add_argument("--list", action="store_true", help="列出所有可用的会议来源")
    
    args = parser.parse_args()
    
    try:
        with ConferenceContentGenerator() as generator:
            if args.list:
                # 列出可用会议
                sources = generator.list_available_conferences()
                print("可用的会议来源:")
                for source in sources:
                    print(f"  - {source}")
                return 0
            
            if not args.conference:
                parser.error("必须指定 --conference 或使用 --list")
            
            # 生成会议内容
            results = generator.generate_conference_content(
                conference_source=args.conference,
                full_conference=args.full,
                include_translation=not args.no_translation,
                include_interpretation=not args.no_interpretation,
                max_workers=args.workers
            )
            
            if "error" in results:
                logger.error("生成失败: {}", results["error"])
                return 1
            
            logger.success("会议内容生成完成: {}", results)
            return 0
            
    except Exception as e:
        logger.error("会议内容生成失败: {}", str(e))
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
