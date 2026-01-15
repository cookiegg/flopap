#!/usr/bin/env python3
"""
候选池翻译脚本
功能：对筛选后的候选池论文进行批量翻译
特点：
1. 先保存翻译结果到文件，再转储到数据库
2. 支持断点续传，避免重复翻译
3. 充分利用50个API KEY并发处理
4. 错误隔离，单篇失败不影响整体进度
"""

import json
import os
import sys
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.db.session import SessionLocal
from app.services.candidate_pool import CandidatePoolService
from app.services.translation_pure import translate_single_paper
from app.services.llm import get_deepseek_clients, distribute_papers
from app.models import Paper, PaperTranslation
from app.core.config import settings
from sqlalchemy import select
from loguru import logger


def translate_papers_to_files(
    papers: List[Paper], 
    output_dir: str, 
    max_workers: int = 50
) -> Dict[str, int]:
    """
    翻译论文并保存到JSON文件
    
    Args:
        papers: 论文列表
        output_dir: 输出目录
        max_workers: 最大并发数
        
    Returns:
        处理结果统计
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 过滤已存在的文件（断点续传）
    papers_to_translate = []
    for paper in papers:
        filename = f"{output_dir}/translation_{paper.id}.json"
        if not os.path.exists(filename):
            papers_to_translate.append(paper)
    
    logger.info(f"需要翻译 {len(papers_to_translate)} 篇论文（跳过已存在文件 {len(papers) - len(papers_to_translate)} 篇）")
    
    if not papers_to_translate:
        return {"success": 0, "failed": 0, "skipped": len(papers)}
    
    # 获取DeepSeek客户端池
    clients = get_deepseek_clients()
    paper_groups = distribute_papers(papers_to_translate, len(clients))
    
    success_count = 0
    failed_count = 0
    
    # 并发翻译
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_paper = {}
        
        for client, paper_group in zip(clients, paper_groups):
            for paper in paper_group:
                future = executor.submit(translate_single_paper, client, paper)
                future_to_paper[future] = paper
        
        for future in as_completed(future_to_paper):
            paper = future_to_paper[future]
            try:
                result = future.result()
                if result:
                    title_zh, summary_zh = result
                    
                    # 构建翻译数据
                    translation_data = {
                        'paper_id': str(paper.id),
                        'arxiv_id': paper.arxiv_id,
                        'title_en': paper.title,
                        'title_zh': title_zh,
                        'summary_en': paper.summary,
                        'summary_zh': summary_zh,
                        'timestamp': datetime.now().isoformat(),
                        'model_name': settings.deepseek_model_name or 'deepseek-chat'
                    }
                    
                    # 保存到JSON文件
                    filename = f"{output_dir}/translation_{paper.id}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(translation_data, f, ensure_ascii=False, indent=2)
                    
                    success_count += 1
                    if success_count % 20 == 0:
                        logger.info(f"已完成 {success_count}/{len(papers_to_translate)} 篇翻译")
                else:
                    failed_count += 1
                    logger.error(f"翻译论文 {paper.id} 失败")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"翻译论文 {paper.id} 异常: {e}")
    
    return {"success": success_count, "failed": failed_count, "skipped": len(papers) - len(papers_to_translate)}


def load_translations_to_database(output_dir: str) -> Dict[str, int]:
    """
    从JSON文件批量加载翻译结果到数据库
    
    Args:
        output_dir: 翻译文件目录
        
    Returns:
        处理结果统计
    """
    if not os.path.exists(output_dir):
        logger.error(f"输出目录不存在: {output_dir}")
        return {"success": 0, "failed": 0, "skipped": 0}
    
    json_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
    logger.info(f"找到 {len(json_files)} 个翻译文件")
    
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    with SessionLocal() as session:
        for filename in json_files:
            try:
                filepath = os.path.join(output_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                paper_id = data['paper_id']
                
                # 检查是否已存在完整翻译
                existing = session.execute(
                    select(PaperTranslation).where(PaperTranslation.paper_id == paper_id)
                ).scalar_one_or_none()
                
                if existing and existing.title_zh and existing.summary_zh:
                    skipped_count += 1
                    continue
                
                # 创建或更新翻译记录
                if existing:
                    existing.title_zh = data['title_zh']
                    existing.summary_zh = data['summary_zh']
                    existing.model_name = data.get('model_name', 'deepseek-chat')
                else:
                    translation = PaperTranslation(
                        paper_id=paper_id,
                        title_zh=data['title_zh'],
                        summary_zh=data['summary_zh'],
                        model_name=data.get('model_name', 'deepseek-chat')
                    )
                    session.add(translation)
                
                success_count += 1
                
                # 批量提交，提高性能
                if success_count % 50 == 0:
                    session.commit()
                    logger.info(f"已保存 {success_count} 条翻译记录到数据库")
                
            except Exception as e:
                failed_count += 1
                logger.error(f"处理文件 {filename} 失败: {e}")
        
        # 最终提交
        session.commit()
    
    return {"success": success_count, "failed": failed_count, "skipped": skipped_count}


def get_translation_status(batch_id: str, filter_type: str) -> Dict[str, int]:
    """
    获取候选池翻译状态
    
    Args:
        batch_id: 批次ID
        filter_type: 筛选类型
        
    Returns:
        翻译状态统计
    """
    with SessionLocal() as session:
        # 获取候选池论文ID
        candidate_paper_ids = CandidatePoolService.get_candidate_paper_ids(
            session, batch_id, filter_type
        )
        
        # 检查翻译状态
        translated_count = 0
        for paper_id in candidate_paper_ids:
            translation = session.execute(
                select(PaperTranslation).where(PaperTranslation.paper_id == paper_id)
            ).scalar_one_or_none()
            
            if translation and translation.title_zh and translation.summary_zh:
                translated_count += 1
        
        return {
            "total": len(candidate_paper_ids),
            "translated": translated_count,
            "remaining": len(candidate_paper_ids) - translated_count
        }


def main():
    parser = argparse.ArgumentParser(description="候选池论文翻译脚本")
    parser.add_argument('batch_id', help='批次ID')
    parser.add_argument('filter_type', help='筛选类型 (cs, ai-ml-cv, math, physics, all)')
    parser.add_argument('--max-workers', type=int, default=50, help='最大并发数 (默认: 50)')
    parser.add_argument('--output-dir', help='输出目录 (默认: translation_results_<filter_type>)')
    parser.add_argument('--only-translate', action='store_true', help='只翻译到文件，不保存到数据库')
    parser.add_argument('--only-load', action='store_true', help='只从文件加载到数据库')
    parser.add_argument('--status', action='store_true', help='查看翻译状态')
    
    args = parser.parse_args()
    
    # 设置默认输出目录
    if not args.output_dir:
        args.output_dir = f"translation_results_{args.filter_type}"
    
    # 查看状态
    if args.status:
        status = get_translation_status(args.batch_id, args.filter_type)
        print(f"\n📊 候选池翻译状态:")
        print(f"  批次ID: {args.batch_id}")
        print(f"  筛选类型: {args.filter_type}")
        print(f"  总论文数: {status['total']} 篇")
        print(f"  已翻译: {status['translated']} 篇")
        print(f"  未翻译: {status['remaining']} 篇")
        print(f"  完成率: {status['translated']/status['total']*100:.1f}%")
        return
    
    # 只加载文件到数据库
    if args.only_load:
        logger.info("从文件加载翻译结果到数据库...")
        result = load_translations_to_database(args.output_dir)
        logger.success(f"数据库加载完成: 成功 {result['success']}, 失败 {result['failed']}, 跳过 {result['skipped']}")
        return
    
    # 翻译阶段
    with SessionLocal() as session:
        papers = CandidatePoolService.get_candidate_papers(session, args.batch_id, args.filter_type)
        logger.info(f"候选池包含 {len(papers)} 篇 {args.filter_type} 论文")
    
    if not papers:
        logger.warning("候选池为空，请先创建候选池")
        return
    
    logger.info(f"开始翻译并保存到文件 ({args.output_dir})...")
    translate_result = translate_papers_to_files(papers, args.output_dir, args.max_workers)
    logger.success(f"翻译完成: 成功 {translate_result['success']}, 失败 {translate_result['failed']}, 跳过 {translate_result['skipped']}")
    
    # 自动加载到数据库（除非指定只翻译）
    if not args.only_translate:
        logger.info("加载翻译结果到数据库...")
        load_result = load_translations_to_database(args.output_dir)
        logger.success(f"数据库加载完成: 成功 {load_result['success']}, 失败 {load_result['failed']}, 跳过 {load_result['skipped']}")
        
        # 显示最终状态
        final_status = get_translation_status(args.batch_id, args.filter_type)
        print(f"\n🎉 翻译任务完成!")
        print(f"  候选池: {final_status['total']} 篇 {args.filter_type} 论文")
        print(f"  翻译完成: {final_status['translated']} 篇 ({final_status['translated']/final_status['total']*100:.1f}%)")


if __name__ == "__main__":
    main()
