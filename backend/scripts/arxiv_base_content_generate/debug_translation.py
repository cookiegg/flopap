#!/usr/bin/env python3
import sys
from pathlib import Path
backend_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_root))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.paper import Paper
from app.services.llm import get_deepseek_clients

def debug_specific_paper():
    print('=== 调试特定论文翻译 ===')
    
    paper_id = '74c8dd10-5dce-4bc6-817b-4356e3cfb381'  # LLM-Assisted
    
    db = SessionLocal()
    clients = get_deepseek_clients()
    client = clients[0]
    
    try:
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            print(f'❌ 未找到论文: {paper_id}')
            return
            
        print(f'📄 论文标题: {paper.title}')
        print(f'📄 摘要长度: {len(paper.summary)} 字符')
        
        # 手动构建prompt
        prompt = f"""请将以下英文论文标题和摘要翻译成中文：

标题：{paper.title}

摘要：{paper.summary}

请按以下格式返回：
标题：[中文标题]
摘要：[中文摘要]"""
        
        print('\n🔄 发送翻译请求...')
        
        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.3
        )
        
        content = response.choices[0].message.content.strip()
        print('\n📝 原始响应:')
        print(content)
        print('\n' + '='*50)
        
        # 测试解析
        lines = content.split('\n')
        title_zh = ""
        summary_zh = ""
        
        print('🔍 逐行解析:')
        for i, line in enumerate(lines):
            line = line.strip()
            print(f'  行{i}: "{line}"')
            if line.startswith('标题：'):
                title_zh = line[3:].strip()
                print(f'    -> 提取标题: "{title_zh}"')
            elif line.startswith('摘要：'):
                summary_zh = line[3:].strip()
                print(f'    -> 提取摘要: "{summary_zh}"')
        
        print(f'\n📊 解析结果:')
        print(f'  标题为空: {not title_zh}')
        print(f'  摘要为空: {not summary_zh}')
        print(f'  标题长度: {len(title_zh)}')
        print(f'  摘要长度: {len(summary_zh)}')
        
    except Exception as e:
        print(f'❌ 调试失败: {e}')
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_specific_paper()
