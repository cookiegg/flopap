#!/usr/bin/env python3
"""
候选池AI解读生成脚本
功能：对筛选后的候选池论文进行批量AI解读生成
特点：
1. 先保存AI解读结果到文件，再转储到数据库
2. 支持断点续传，避免重复生成
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
from app.services.ai_interpretation import generate_ai_interpretation
from app.services.llm import get_deepseek_clients, distribute_papers
from app.models import Paper
from app.models.paper import PaperInterpretation
from app.core.config import settings
from sqlalchemy import select
from loguru import logger


def generate_interpretations_to_files(
    papers: List[Paper], 
    output_dir: str, 
    max_workers: int = 50
) -> Dict[str, int]:
    """
    生成AI解读并保存到JSON文件
    
    Args:
        papers: 论文列表
        output_dir: 输出目录
        max_workers: 最大并发数
        
    Returns:
        处理结果统计
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 过滤已存在的文件（断点续传）
    papers_to_interpret = []
    for paper in papers:
        filename = f"{output_dir}/interpretation_{paper.id}.json"
        if not os.path.exists(filename):
            papers_to_interpret.append(paper)
    
    logger.info(f"需要生成AI解读 {len(papers_to_interpret)} 篇论文（跳过已存在文件 {len(papers) - len(papers_to_interpret)} 篇）")
    
    if not papers_to_interpret:
        return {"success": 0, "failed": 0, "skipped": len(papers)}
    
    # 获取DeepSeek客户端池
    clients = get_deepseek_clients()
    paper_groups = distribute_papers(papers_to_interpret, len(clients))
    
    success_count = 0
    failed_count = 0
    
    # 并发生成AI解读
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_paper = {}
        
        for client, paper_group in zip(clients, paper_groups):
            for paper in paper_group:
                future = executor.submit(generate_ai_interpretation, client, paper)
                future_to_paper[future] = paper
        
        for future in as_completed(future_to_paper):
            paper = future_to_paper[future]
            try:
                ai_interpretation = future.result()
                if ai_interpretation and ai_interpretation.strip():
                    
                    # 构建AI解读数据
                    interpretation_data = {
                        'paper_id': str(paper.id),
                        'arxiv_id': paper.arxiv_id,
                        'title': paper.title,
                        'ai_interpretation': ai_interpretation,
                        'timestamp': datetime.now().isoformat(),
                        'model_name': settings.deepseek_model_name or 'deepseek-chat'
                    }
                    
                    # 保存到JSON文件
                    filename = f"{output_dir}/interpretation_{paper.id}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(interpretation_data, f, ensure_ascii=False, indent=2)
                    
                    success_count += 1
                    if success_count % 20 == 0:
                        logger.info(f"已完成 {success_count}/{len(papers_to_interpret)} 篇AI解读")
                else:
                    failed_count += 1
                    logger.error(f"生成论文 {paper.id} AI解读失败")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"生成论文 {paper.id} AI解读异常: {e}")
    
    return {"success": success_count, "failed": failed_count, "skipped": len(papers) - len(papers_to_interpret)}


def load_interpretations_to_database(output_dir: str) -> Dict[str, int]:
    """
    从JSON文件批量加载AI解读结果到数据库
    
    Args:
        output_dir: AI解读文件目录
        
    Returns:
        处理结果统计
    """
    if not os.path.exists(output_dir):
        logger.error(f"输出目录不存在: {output_dir}")
        return {"success": 0, "failed": 0, "skipped": 0}
    
    json_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
    logger.info(f"找到 {len(json_files)} 个AI解读文件")
    
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
                
                # 检查是否已存在AI解读
                existing = session.execute(
                    select(PaperInterpretation).where(PaperInterpretation.paper_id == paper_id)
                ).scalar_one_or_none()
                
                if existing and existing.interpretation and existing.interpretation.strip():
                    skipped_count += 1
                    continue
                
                # 创建或更新AI解读记录
                if existing:
                    existing.interpretation = data['ai_interpretation']
                    if not existing.model_name:
                        existing.model_name = data.get('model_name', 'deepseek-chat')
                else:
                    interpretation = PaperInterpretation(
                        paper_id=paper_id,
                        interpretation=data['ai_interpretation'],
                        language='zh',
                        model_name=data.get('model_name', 'deepseek-chat')
                    )
                    session.add(interpretation)
                
                success_count += 1
                
                # 批量提交，提高性能
                if success_count % 50 == 0:
                    session.commit()
                    logger.info(f"已保存 {success_count} 条AI解读记录到数据库")
                
            except Exception as e:
                failed_count += 1
                logger.error(f"处理文件 {filename} 失败: {e}")
        
        # 最终提交
        session.commit()
    
    return {"success": success_count, "failed": failed_count, "skipped": skipped_count}


def get_interpretation_status(batch_id: str, filter_type: str) -> Dict[str, int]:
    """
    获取候选池AI解读状态
    
    Args:
        batch_id: 批次ID
        filter_type: 筛选类型
        
    Returns:
        AI解读状态统计
    """
    with SessionLocal() as session:
        # 获取候选池论文ID
        candidate_paper_ids = CandidatePoolService.get_candidate_paper_ids(
            session, batch_id, filter_type
        )
        
        # 检查AI解读状态
        interpreted_count = 0
        for paper_id in candidate_paper_ids:
            translation = session.execute(
                select(PaperTranslation).where(PaperTranslation.paper_id == paper_id)
            ).scalar_one_or_none()
            
            if translation and translation.ai_interpretation and translation.ai_interpretation.strip():
                interpreted_count += 1
        
        return {
            "total": len(candidate_paper_ids),
            "interpreted": interpreted_count,
            "remaining": len(candidate_paper_ids) - interpreted_count
        }


def main():
    parser = argparse.ArgumentParser(description="候选池论文AI解读生成脚本")
    parser.add_argument('batch_id', help='批次ID')
    parser.add_argument('filter_type', help='筛选类型 (cs, ai-ml-cv, math, physics, all)')
    parser.add_argument('--max-workers', type=int, default=50, help='最大并发数 (默认: 50)')
    parser.add_argument('--output-dir', help='输出目录 (默认: interpretation_results_<filter_type>)')
    parser.add_argument('--only-interpret', action='store_true', help='只生成AI解读到文件，不保存到数据库')
    parser.add_argument('--only-load', action='store_true', help='只从文件加载到数据库')
    parser.add_argument('--status', action='store_true', help='查看AI解读状态')
    
    args = parser.parse_args()
    
    # 设置默认输出目录
    if not args.output_dir:
        args.output_dir = f"interpretation_results_{args.filter_type}"
    
    # 查看状态
    if args.status:
        status = get_interpretation_status(args.batch_id, args.filter_type)
        print(f"\n📊 候选池AI解读状态:")
        print(f"  批次ID: {args.batch_id}")
        print(f"  筛选类型: {args.filter_type}")
        print(f"  总论文数: {status['total']} 篇")
        print(f"  已生成AI解读: {status['interpreted']} 篇")
        print(f"  未生成AI解读: {status['remaining']} 篇")
        print(f"  完成率: {status['interpreted']/status['total']*100:.1f}%")
        return
    
    # 只加载文件到数据库
    if args.only_load:
        logger.info("从文件加载AI解读结果到数据库...")
        result = load_interpretations_to_database(args.output_dir)
        logger.success(f"数据库加载完成: 成功 {result['success']}, 失败 {result['failed']}, 跳过 {result['skipped']}")
        return
    
    # AI解读生成阶段
    with SessionLocal() as session:
        papers = CandidatePoolService.get_candidate_papers(session, args.batch_id, args.filter_type)
        logger.info(f"候选池包含 {len(papers)} 篇 {args.filter_type} 论文")
    
    if not papers:
        logger.warning("候选池为空，请先创建候选池")
        return
    
    logger.info(f"开始生成AI解读并保存到文件 ({args.output_dir})...")
    interpret_result = generate_interpretations_to_files(papers, args.output_dir, args.max_workers)
    logger.success(f"AI解读生成完成: 成功 {interpret_result['success']}, 失败 {interpret_result['failed']}, 跳过 {interpret_result['skipped']}")
    
    # 自动加载到数据库（除非指定只生成）
    if not args.only_interpret:
        logger.info("加载AI解读结果到数据库...")
        load_result = load_interpretations_to_database(args.output_dir)
        logger.success(f"数据库加载完成: 成功 {load_result['success']}, 失败 {load_result['failed']}, 跳过 {load_result['skipped']}")
        
        # 显示最终状态
        final_status = get_interpretation_status(args.batch_id, args.filter_type)
        print(f"\n🎉 AI解读生成任务完成!")
        print(f"  候选池: {final_status['total']} 篇 {args.filter_type} 论文")
        print(f"  AI解读完成: {final_status['interpreted']} 篇 ({final_status['interpreted']/final_status['total']*100:.1f}%)")


if __name__ == "__main__":
    main()
