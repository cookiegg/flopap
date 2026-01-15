#!/usr/bin/env python3

import sys
import os
import json
from pathlib import Path

# 添加项目根目录到路径  
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.session import SessionLocal
from app.services.ai_interpretation import generate_ai_interpretation
from app.services.llm import get_deepseek_clients
from app.models import Paper, PaperInterpretation

def main():
    db = SessionLocal()
    
    # Get admin pushed papers without AI interpretations
    result = db.execute(text("""
        SELECT DISTINCT apc.paper_id, p.title, p.summary 
        FROM admin_pushed_content apc
        JOIN papers p ON apc.paper_id = p.id
        LEFT JOIN paper_interpretations pi ON apc.paper_id = pi.paper_id
        WHERE apc.is_active = true AND pi.paper_id IS NULL
    """)).fetchall()
    
    if not result:
        print("✅ 所有管理员推送论文都已有AI解读")
        db.close()
        return
    
    print(f"🔄 开始为 {len(result)} 篇管理员推送论文生成AI解读...")
    
    # Get AI client
    clients = get_deepseek_clients()
    client = clients[0] if clients else None
    
    if not client:
        print("❌ 无法获取AI客户端")
        db.close()
        return
    
    for i, (paper_id, title, summary) in enumerate(result, 1):
        try:
            print(f"[{i}/{len(result)}] 处理论文 ID: {paper_id}")
            
            # Get paper object
            paper = db.query(Paper).filter(Paper.id == paper_id).first()
            if not paper:
                print(f"❌ 找不到论文 {paper_id}")
                continue
            
            # Generate AI interpretation
            interpretation = generate_ai_interpretation(client, paper)
            
            if not interpretation:
                print(f"❌ 论文 {paper_id} AI解读生成失败")
                continue
            
            # Save to file first (backup)
            os.makedirs('ai_interpretations/admin', exist_ok=True)
            with open(f'ai_interpretations/admin/{paper_id}.json', 'w', encoding='utf-8') as f:
                json.dump({'paper_id': str(paper_id), 'interpretation': interpretation}, f, ensure_ascii=False, indent=2)
            
            # Use ORM model like translation script
            paper_interpretation = PaperInterpretation(
                paper_id=paper_id,
                interpretation=interpretation,
                language='zh',
                model_name='deepseek-chat'
            )
            
            db.add(paper_interpretation)
            db.commit()
            print(f"✅ 完成论文 {paper_id}")
            
        except Exception as e:
            print(f"❌ 论文 {paper_id} 处理失败: {e}")
            db.rollback()
            continue
    
    db.close()
    print("🎉 管理员推送论文AI解读生成完成！")

if __name__ == "__main__":
    main()
