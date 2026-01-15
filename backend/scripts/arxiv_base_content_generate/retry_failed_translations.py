#!/usr/bin/env python3
import sys
from pathlib import Path
backend_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_root))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.paper import Paper
from app.services.content_generation.translation_generate import translate_single_paper

from app.services.llm import get_deepseek_clients

def retry_failed_translations():
    print('=== 重试翻译失败的论文 ===')
    
    # 从日志中提取的失败论文ID
    failed_paper_ids = [
        'cee4a1d5-b5c6-4a8c-b89f-afcad709fc46',  # ${D}^{3}${ETOR}
        '616882bf-f8af-4dae-920e-7eba9d3892c5',  # milliMamba
        'e9dd0755-18c4-44e7-84c5-80cfc690e806',  # Self-motion
        '74c8dd10-5dce-4bc6-817b-4356e3cfb381'   # LLM-Assisted
    ]
    
    db = SessionLocal()
    clients = get_deepseek_clients()
    client = clients[0]
    
    try:
        for paper_id in failed_paper_ids:
            paper = db.query(Paper).filter(Paper.id == paper_id).first()
            if paper:
                print(f'\n📄 重试翻译: {paper.title[:50]}...')
                result = translate_single_paper(client, paper)
                if result:
                    print(f'   ✅ 翻译成功')
                    print(f'   标题: {result[0][:50]}...')
                    print(f'   摘要: {result[1][:50]}...')
                else:
                    print(f'   ❌ 翻译仍然失败')
            else:
                print(f'\n❌ 未找到论文: {paper_id}')
    
    except Exception as e:
        print(f'❌ 重试失败: {e}')
    finally:
        db.close()

if __name__ == "__main__":
    retry_failed_translations()
