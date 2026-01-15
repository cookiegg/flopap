#!/usr/bin/env python3
import sys
from pathlib import Path
backend_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_root))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.paper import Paper

def main():
    print('=== 检查翻译解析失败的论文 ===')
    
    # 从日志中提取的失败论文ID
    failed_paper_ids = [
        'cee4a1d5-b5c6-4a8c-b89f-afcad709fc46',  # ${D}^{3}${ETOR}
        '616882bf-f8af-4dae-920e-7eba9d3892c5',  # milliMamba
        'e9dd0755-18c4-44e7-84c5-80cfc690e806',  # Self-motion
        '74c8dd10-5dce-4bc6-817b-4356e3cfb381'   # LLM-Assisted
    ]
    
    db = SessionLocal()
    
    try:
        for paper_id in failed_paper_ids:
            paper = db.query(Paper).filter(Paper.id == paper_id).first()
            if paper:
                print(f'\n📄 Paper ID: {paper_id}')
                print(f'   ArXiv ID: {paper.arxiv_id}')
                print(f'   标题: {paper.title}')
                print(f'   摘要长度: {len(paper.summary)} 字符')
                
                # 检查标题中的特殊字符
                special_chars = ['$', '{', '}', '\\', '^', '_', '&']
                found_chars = [char for char in special_chars if char in paper.title]
                if found_chars:
                    print(f'   ⚠️  标题特殊字符: {found_chars}')
                
                # 检查摘要中的特殊字符
                abstract_special = [char for char in special_chars if char in paper.summary[:200]]
                if abstract_special:
                    print(f'   ⚠️  摘要特殊字符: {abstract_special}')
                
                print(f'   摘要开头: {paper.summary[:150]}...')
            else:
                print(f'\n❌ 未找到论文: {paper_id}')
    
    except Exception as e:
        print(f'❌ 检查失败: {e}')
    finally:
        db.close()

if __name__ == "__main__":
    main()
