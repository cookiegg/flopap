#!/usr/bin/env python3
"""
简化的TTS生成脚本 - 不依赖新数据库表
"""
import argparse
import asyncio
import sys
from pathlib import Path
from uuid import UUID

# 添加backend根目录到路径
backend_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_root))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.content_generation.tts_generate import (
    batch_generate_tts,
    get_random_papers_for_tts
)

async def main():
    parser = argparse.ArgumentParser(description="简化TTS生成")
    parser.add_argument("--count", "-c", type=int, default=2, help="生成数量")
    parser.add_argument("--voice", default="zh-CN-XiaoxiaoNeural", help="语音模型")
    parser.add_argument("--max-workers", type=int, default=3, help="并发数")
    parser.add_argument("--save-dir", default="./data/tts", help="输出目录")
    args = parser.parse_args()
    
    # 创建输出目录
    output_dir = Path(args.save_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # 获取数据库会话
    db = SessionLocal()
    
    try:
        # 获取随机论文
        print(f"获取随机 {args.count} 篇论文...")
        paper_ids = get_random_papers_for_tts(db, args.count)
        
        if not paper_ids:
            print("未找到可用论文")
            return
        
        print(f"找到 {len(paper_ids)} 篇论文")
        
        # 生成TTS（直接调用异步函数）
        print(f"开始生成TTS（并发数：{args.max_workers}）...")
        from app.services.content_generation.tts_generate import batch_generate_tts_async
        tts_results = await batch_generate_tts_async(
            session=db,
            paper_ids=paper_ids,
            voice=args.voice,
            max_workers=args.max_workers
        )
        
        # 保存文件
        print(f"\n保存音频文件到 {output_dir}/")
        for paper_id, audio_bytes in tts_results.items():
            output_file = output_dir / f"{paper_id}.wav"
            output_file.write_bytes(audio_bytes)
            print(f"✓ {output_file.name} ({len(audio_bytes)} 字节)")
        
        print(f"\n✅ 完成！成功生成 {len(tts_results)}/{len(paper_ids)} 个文件")
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
