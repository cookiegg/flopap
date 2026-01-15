#!/usr/bin/env python3

import sys
import os
import json
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加项目根目录到路径  
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.db.session import SessionLocal
from app.models import Paper, AdminPushedContent
from app.models.paper import PaperInterpretation
from app.services.ai_interpretation import generate_ai_interpretation
from app.services.llm import get_deepseek_clients, distribute_papers
from app.core.config import settings
from sqlalchemy import select

def process_single_paper(client, paper):
    """处理单篇论文的AI解读"""
    try:
        interpretation = generate_ai_interpretation(client, paper)
        if interpretation:
            return {
                'paper_id': str(paper.id),
                'arxiv_id': paper.arxiv_id,
                'title': paper.title,
                'interpretation': interpretation,
                'timestamp': datetime.now().isoformat(),
                'model_name': settings.deepseek_model_name or 'deepseek-chat'
            }
    except Exception as e:
        print(f"论文 {paper.id} 处理失败: {e}")
    return None

def interpret_admin_pushed_papers():
    output_dir = 'admin_interpretation_results'
    os.makedirs(output_dir, exist_ok=True)
    
    with SessionLocal() as session:
        # 获取需要AI解读的管理员推送论文
        stmt = select(Paper).join(
            AdminPushedContent, Paper.id == AdminPushedContent.paper_id
        ).outerjoin(
            PaperInterpretation, Paper.id == PaperInterpretation.paper_id
        ).where(
            AdminPushedContent.is_active == True,
            PaperInterpretation.interpretation.is_(None)
        )
        
        papers_to_interpret = list(session.execute(stmt).scalars().all())
        
        print(f'需要AI解读的管理员推送论文: {len(papers_to_interpret)} 篇')
        
        if not papers_to_interpret:
            print('所有管理员推送论文都已有AI解读')
            return
        
        clients = get_deepseek_clients()
        paper_groups = distribute_papers(papers_to_interpret, len(clients))
        
        # 并发处理
        with ThreadPoolExecutor(max_workers=len(clients)) as executor:
            future_to_paper = {}
            
            for client, paper_group in zip(clients, paper_groups):
                for paper in paper_group:
                    future = executor.submit(process_single_paper, client, paper)
                    future_to_paper[future] = paper
            
            success_count = 0
            for future in as_completed(future_to_paper):
                paper = future_to_paper[future]
                result = future.result()
                
                if result:
                    # 保存到文件
                    filename = f'{output_dir}/admin_interpretation_{paper.id}.json'
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    
                    # 保存到数据库
                    paper_interpretation = PaperInterpretation(
                        paper_id=paper.id,
                        interpretation=result['interpretation'],
                        language='zh',
                        model_name=result['model_name']
                    )
                    session.add(paper_interpretation)
                    success_count += 1
                    print(f'✅ 完成: {paper.title[:50]}...')
                else:
                    print(f'❌ 失败: {paper.title[:50]}...')
        
        session.commit()
        print(f'\n管理员推送论文AI解读完成: {success_count} 篇')

if __name__ == "__main__":
    interpret_admin_pushed_papers()

if __name__ == "__main__":
    interpret_admin_pushed_papers()
