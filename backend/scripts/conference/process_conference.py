#!/usr/bin/env python3
"""
通用会议论文处理脚本

支持:
- 从 data/paperlists 导入指定会议论文到数据库
- 为所有活跃用户生成推荐池
- 生成翻译/AI解读/TTS内容

用法:
  python process_conference.py <conference_id> [options]
  python process_conference.py iclr2025 --import      # 导入论文
  python process_conference.py iclr2025 --pool        # 生成推荐池
  python process_conference.py iclr2025 --content     # 生成内容
  python process_conference.py iclr2025 --all         # 执行所有步骤
  python process_conference.py --list                 # 列出可用会议
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from uuid import UUID

# 添加backend根目录到路径
backend_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_root))

from sqlalchemy import select, distinct
from sqlalchemy.orm import Session
from loguru import logger

from app.db.session import SessionLocal
from app.models import Paper, UserFeedback, UserPaperRanking, PaperTranslation, PaperInterpretation
from app.services.data_ingestion.conference_import import (
    import_conference_papers,
    get_available_2025_conferences,
    SUPPORTED_2025_CONFERENCES
)
from app.services.recommendation.user_ranking_service import UserRankingService


class ConferenceProcessor:
    """通用会议处理器"""
    
    def __init__(self, conference_id: str):
        self.conference_id = conference_id
        self.session: Optional[Session] = None
        self.ranking_service = None
        
    def setup_session(self):
        """设置数据库会话"""
        self.session = SessionLocal()
        self.ranking_service = UserRankingService(self.session)
        
    def cleanup_session(self):
        """清理数据库会话"""
        if self.session:
            self.session.close()
    
    @property
    def source_key(self) -> str:
        """获取数据库中的source标识"""
        return f"conf/{self.conference_id}"
    
    # ==================== IMPORT ====================
    
    def run_import(self) -> Dict:
        """导入会议论文到数据库"""
        logger.info(f"开始导入会议论文: {self.conference_id}")
        
        try:
            batch = import_conference_papers(self.session, self.conference_id)
            result = {
                'success': True,
                'batch_id': str(batch.id),
                'paper_count': batch.item_count,
                'message': f"成功导入 {batch.item_count} 篇论文"
            }
            logger.info(result['message'])
            return result
        except Exception as e:
            logger.error(f"导入失败: {e}")
            return {'success': False, 'message': str(e)}
    
    # ==================== POOL GENERATION ====================
    
    def get_active_users(self) -> List[str]:
        """获取活跃用户列表"""
        # 从UserFeedback表获取有反馈行为的用户
        feedback_users = set(self.session.execute(
            select(distinct(UserFeedback.user_id))
        ).scalars().all())
        
        # 从UserPaperRanking表获取有排序表的用户
        ranking_users = set(self.session.execute(
            select(distinct(UserPaperRanking.user_id))
        ).scalars().all())
        
        all_users = feedback_users.union(ranking_users)
        logger.info(f"找到 {len(all_users)} 个活跃用户")
        return list(all_users)
    
    def get_conference_papers(self) -> List[UUID]:
        """获取该会议的所有论文ID"""
        papers = self.session.execute(
            select(Paper.id).where(
                Paper.source == self.source_key
            )
        ).scalars().all()
        
        logger.info(f"找到 {len(papers)} 篇 {self.conference_id} 论文")
        return list(papers)
    
    def check_existing_ranking(self, user_id: str) -> bool:
        """检查用户是否已有该会议的排序表"""
        existing = self.session.execute(
            select(UserPaperRanking.id).where(
                UserPaperRanking.user_id == user_id,
                UserPaperRanking.source_key == self.conference_id
            )
        ).scalar_one_or_none()
        return existing is not None
    
    def run_pool_generation(self, force_update: bool = False, max_users: int = None) -> Dict:
        """为所有活跃用户生成推荐池"""
        logger.info(f"开始为 {self.conference_id} 生成推荐池...")
        
        paper_ids = self.get_conference_papers()
        if not paper_ids:
            return {'success': False, 'message': '未找到该会议的论文，请先运行 --import'}
        
        users = self.get_active_users()
        if not users:
            return {'success': False, 'message': '未找到活跃用户'}
        
        if max_users:
            users = users[:max_users]
            logger.info(f"限制处理用户数量为: {max_users}")
        
        # 启用优化版排序算法
        try:
            from app.services.recommendation.user_paper_ranking_optimized import patch_ranking_service
            patch_ranking_service()
        except ImportError:
            logger.warning("优化版排序服务不可用，使用默认版本")
        
        results = {'total': len(users), 'success': 0, 'failed': 0, 'skipped': 0}
        
        for i, user_id in enumerate(users, 1):
            try:
                if not force_update and self.check_existing_ranking(user_id):
                    results['skipped'] += 1
                    continue
                
                success = self.ranking_service.update_user_ranking(
                    user_id=user_id,
                    source_key=self.conference_id,
                    paper_ids=paper_ids,
                    force_update=force_update
                )
                
                if success:
                    results['success'] += 1
                else:
                    results['failed'] += 1
                    
            except Exception as e:
                logger.error(f"用户 {user_id} 排序表生成失败: {e}")
                results['failed'] += 1
            
            if i % 10 == 0:
                logger.info(f"进度: {i}/{len(users)} - 成功: {results['success']}, 失败: {results['failed']}, 跳过: {results['skipped']}")
        
        results['message'] = f"处理完成: 成功 {results['success']}, 失败 {results['failed']}, 跳过 {results['skipped']}"
        results['success_flag'] = results['failed'] == 0
        logger.info(results['message'])
        return results
    
    # ==================== CONTENT GENERATION ====================
    
    def get_papers_without_content(self, limit: int = 100) -> List[Paper]:
        """获取没有翻译和AI解读的论文"""
        from sqlalchemy import text
        
        query = text("""
            SELECT p.* FROM papers p
            WHERE p.source = :source
            AND NOT EXISTS (
                SELECT 1 FROM paper_translations pt WHERE pt.paper_id = p.id
            )
            AND NOT EXISTS (
                SELECT 1 FROM paper_interpretations pi WHERE pi.paper_id = p.id
            )
            ORDER BY RANDOM()
            LIMIT :limit
        """)
        
        result = self.session.execute(query, {"source": self.source_key, "limit": limit})
        paper_rows = result.fetchall()
        
        papers = []
        for row in paper_rows:
            paper = self.session.get(Paper, row.id)
            if paper:
                # 强制加载属性并从session分离
                _ = paper.id, paper.title, paper.summary, paper.authors, paper.categories, paper.arxiv_id
                self.session.expunge(paper)
                papers.append(paper)
        
        return papers
    
    def run_content_generation(self, steps: List[str] = None, batch_size: int = 50) -> Dict:
        """生成翻译/AI解读/TTS内容"""
        if steps is None:
            steps = ['trans', 'ai', 'tts']
        
        logger.info(f"开始为 {self.conference_id} 生成内容: {steps}")
        
        papers = self.get_papers_without_content(limit=batch_size)
        if not papers:
            return {'success': True, 'message': '所有论文都已有内容，无需生成'}
        
        logger.info(f"找到 {len(papers)} 篇需要生成内容的论文")
        
        results = {'translations': 0, 'interpretations': 0, 'tts': 0}
        
        # 生成翻译
        if 'trans' in steps:
            try:
                from app.services.content_generation.translation_generate_v2 import generate_translations_for_papers
                translations = generate_translations_for_papers(papers, max_workers=50)
                
                # 保存到数据库
                with SessionLocal() as save_session:
                    for paper in papers:
                        if paper.id in translations:
                            title_zh, summary_zh = translations[paper.id]
                            existing = save_session.query(PaperTranslation).filter(
                                PaperTranslation.paper_id == paper.id
                            ).first()
                            if not existing:
                                translation = PaperTranslation(
                                    paper_id=paper.id,
                                    title_zh=title_zh,
                                    summary_zh=summary_zh,
                                    model_name="deepseek-reasoner"
                                )
                                save_session.add(translation)
                                results['translations'] += 1
                    save_session.commit()
                logger.info(f"翻译完成: {results['translations']} 篇")
            except Exception as e:
                logger.error(f"翻译生成失败: {e}")
        
        # 生成AI解读
        if 'ai' in steps:
            try:
                from app.services.content_generation.ai_interpretation_generate_v2 import generate_interpretations_for_papers
                interpretations = generate_interpretations_for_papers(papers, max_workers=50)
                
                with SessionLocal() as save_session:
                    for paper in papers:
                        if paper.id in interpretations:
                            existing = save_session.query(PaperInterpretation).filter(
                                PaperInterpretation.paper_id == paper.id
                            ).first()
                            if not existing:
                                interpretation = PaperInterpretation(
                                    paper_id=paper.id,
                                    interpretation=interpretations[paper.id],
                                    language="zh",
                                    model_name="deepseek-reasoner"
                                )
                                save_session.add(interpretation)
                                results['interpretations'] += 1
                    save_session.commit()
                logger.info(f"AI解读完成: {results['interpretations']} 篇")
            except Exception as e:
                logger.error(f"AI解读生成失败: {e}")
        
        # TTS生成 (可选)
        if 'tts' in steps:
            logger.info("TTS生成暂未实现通用版本")
        
        results['message'] = f"内容生成完成: 翻译 {results['translations']} 篇, AI解读 {results['interpretations']} 篇"
        results['success'] = True
        logger.info(results['message'])
        return results
    
    # ==================== MAIN RUNNER ====================
    
    def run(self, import_papers: bool = False, pool: bool = False, content: bool = False,
            force_update: bool = False, max_users: int = None, content_steps: List[str] = None) -> Dict:
        """运行指定的处理步骤"""
        results = {}
        
        try:
            self.setup_session()
            
            if import_papers:
                results['import'] = self.run_import()
            
            if pool:
                results['pool'] = self.run_pool_generation(force_update=force_update, max_users=max_users)
            
            if content:
                results['content'] = self.run_content_generation(steps=content_steps)
            
        finally:
            self.cleanup_session()
        
        return results


def list_available_conferences():
    """列出可用的会议数据"""
    print("📋 可用的会议数据:")
    print("-" * 60)
    
    available = get_available_2025_conferences()
    
    if not available:
        print("❌ 未找到任何会议数据文件")
        return
    
    for conf in available:
        size_mb = conf['file_size'] / (1024 * 1024)
        print(f"✅ {conf['id']:<15} {conf['name']:<20} ({size_mb:.1f} MB)")
    
    print(f"\n📊 总计: {len(available)} 个会议")


def get_conference_status(conference_id: str) -> Dict:
    """获取会议处理状态"""
    with SessionLocal() as session:
        source_key = f"conf/{conference_id}"
        
        # 论文数量
        paper_count = session.execute(
            select(Paper.id).where(Paper.source == source_key)
        ).scalars().all()
        
        # 已翻译数量
        translated_count = 0
        if paper_count:
            from sqlalchemy import func
            translated_count = session.query(func.count(PaperTranslation.id)).join(
                Paper, PaperTranslation.paper_id == Paper.id
            ).filter(Paper.source == source_key).scalar() or 0
        
        # 用户排序表数量
        ranking_count = session.query(UserPaperRanking).filter(
            UserPaperRanking.source_key == conference_id
        ).count()
        
        return {
            'conference_id': conference_id,
            'paper_count': len(paper_count),
            'translated_count': translated_count,
            'ranking_count': ranking_count
        }


def main():
    parser = argparse.ArgumentParser(description="通用会议论文处理脚本")
    parser.add_argument('conference', nargs='?', help='会议ID (如: iclr2025)')
    parser.add_argument('--list', action='store_true', help='列出可用会议')
    parser.add_argument('--status', action='store_true', help='显示会议处理状态')
    parser.add_argument('--import', dest='import_papers', action='store_true', help='导入论文到数据库')
    parser.add_argument('--pool', action='store_true', help='生成推荐池')
    parser.add_argument('--content', action='store_true', help='生成内容 (翻译/AI/TTS)')
    parser.add_argument('--all', action='store_true', help='执行所有步骤')
    parser.add_argument('--force', action='store_true', help='强制更新已存在的数据')
    parser.add_argument('--max-users', type=int, help='限制处理的最大用户数')
    parser.add_argument('--steps', nargs='+', choices=['trans', 'ai', 'tts'], 
                        default=['trans', 'ai'], help='内容生成步骤')
    
    args = parser.parse_args()
    
    if args.list:
        list_available_conferences()
        return
    
    if not args.conference:
        parser.print_help()
        return
    
    if args.conference not in SUPPORTED_2025_CONFERENCES:
        print(f"❌ 不支持的会议: {args.conference}")
        print(f"支持的会议: {', '.join(SUPPORTED_2025_CONFERENCES.keys())}")
        sys.exit(1)
    
    if args.status:
        status = get_conference_status(args.conference)
        print(f"📊 {args.conference} 状态:")
        print(f"  论文数: {status['paper_count']}")
        print(f"  已翻译: {status['translated_count']}")
        print(f"  用户排序表: {status['ranking_count']}")
        return
    
    # 执行处理
    processor = ConferenceProcessor(args.conference)
    
    import_papers = args.import_papers or args.all
    pool = args.pool or args.all
    content = args.content or args.all
    
    if not (import_papers or pool or content):
        parser.print_help()
        return
    
    print(f"🚀 开始处理会议: {args.conference}")
    print(f"   步骤: {'导入 ' if import_papers else ''}{'推荐池 ' if pool else ''}{'内容生成' if content else ''}")
    
    results = processor.run(
        import_papers=import_papers,
        pool=pool,
        content=content,
        force_update=args.force,
        max_users=args.max_users,
        content_steps=args.steps
    )
    
    print("\n📋 处理结果:")
    for step, result in results.items():
        status = "✅" if result.get('success') or result.get('success_flag') else "❌"
        print(f"  {status} {step}: {result.get('message', result)}")


if __name__ == "__main__":
    main()
