#!/usr/bin/env python3
"""
为15篇已完成内容的NeurIPS论文生成TTS语音
"""
import sys
from pathlib import Path

# 添加backend根目录到路径
backend_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_root))

from app.db.session import SessionLocal
from app.services.content_generation.tts_generate import batch_generate_tts_with_storage

# 15篇已完成内容的论文ID（排除失败的DQVis Dataset）
COMPLETED_PAPERS = [
    'b8b00dbc-cfb6-4e30-9ea4-451b9db7627c',
    'd7d30888-50e4-4601-891f-7e83b5402b11',
    'd810d631-8432-4ed4-9004-209efdaf42a1',
    'd0d3a0f3-57e0-4092-8a7c-23c549eb854d',
    '080bd375-f12c-4281-b8f9-4a25de68ef0c',
    '7792523a-deb3-4679-8ec9-bc134f117bb3',
    '9ab9992e-bf61-4356-8841-3f666ae868ff',
    'cf6ebd5e-3f7e-43ae-8fc8-00ab01899c15',
    '5acda317-f2b2-4e4c-8bc8-f3202ac98f0f',
    'da3d1f6a-7777-4b9b-acf1-ac4c801c4f79',
    'acdf9d39-aca1-4e74-b927-fd41f314acc5',
    '273030d5-a4c7-4066-b4a5-15792544a6a5',
    '10a11f07-1840-4a2c-ad66-29991a260f02',
    '03406616-29e6-4d93-9eba-f8b5f94f8097',
    'c2002268-92a9-4290-a491-635509c743e0',
]

def main():
    print(f"🎵 开始为15篇已完成内容的NeurIPS论文生成TTS语音")
    
    db = SessionLocal()
    
    try:
        print(f"📝 论文数量: {len(COMPLETED_PAPERS)} 篇")
        
        # 生成TTS
        tts_file_paths = batch_generate_tts_with_storage(
            session=db,
            paper_ids=COMPLETED_PAPERS,
            voice="zh-CN-XiaoxiaoNeural",
            max_workers=20,  # 使用20个并发
            save_to_storage=True
        )
        
        success_count = len(tts_file_paths)
        
        print(f"🎉 TTS生成完成!")
        print(f"成功生成: {success_count}/{len(COMPLETED_PAPERS)} 个TTS文件")
        print(f"成功率: {success_count/len(COMPLETED_PAPERS)*100:.1f}%")
        
    except Exception as e:
        print(f"❌ TTS生成失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
