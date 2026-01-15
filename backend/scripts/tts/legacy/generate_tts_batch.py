#!/usr/bin/env python3
"""
TTS批量生成脚本 - 内部使用

用法：
  python scripts/tts/generate_tts_batch.py --count 5                    # 随机生成5篇
  python scripts/tts/generate_tts_batch.py --paper-ids uuid1 uuid2      # 指定论文ID
  python scripts/tts/generate_tts_batch.py --save-dir ./tts_output      # 指定输出目录
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
    batch_generate_tts_with_storage,
    get_random_papers_for_tts
)


async def main():
    parser = argparse.ArgumentParser(description="批量生成论文TTS语音")
    parser.add_argument("--count", "-c", type=int, help="随机生成数量")
    parser.add_argument("--paper-ids", nargs="+", help="指定论文ID列表")
    parser.add_argument("--voice", default="zh-CN-XiaoxiaoNeural", help="语音模型")
    parser.add_argument("--max-workers", type=int, default=5, help="并发数")
    parser.add_argument("--save-dir", default="./tts_output", help="输出目录")
    args = parser.parse_args()
    
    # 创建输出目录
    output_dir = Path(args.save_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # 获取数据库会话
    db = SessionLocal()
    
    try:
        # 确定要处理的论文ID
        if args.paper_ids:
            paper_ids = [UUID(pid) for pid in args.paper_ids]
            print(f"处理指定的 {len(paper_ids)} 篇论文")
        elif args.count:
            paper_ids = get_random_papers_for_tts(db, args.count)
            print(f"随机选择 {len(paper_ids)} 篇论文")
        else:
            print("请指定 --count 或 --paper-ids")
            return
        
        if not paper_ids:
            print("未找到可用论文")
            return
        
        # 生成TTS
        print(f"开始生成TTS（并发数：{args.max_workers}）...")
        tts_file_paths = batch_generate_tts_with_storage(
            session=db,
            paper_ids=paper_ids,
            voice=args.voice,
            max_workers=args.max_workers,
            save_to_storage=True
        )
        
        print(f"\n生成完成！文件路径:")
        for paper_id, file_path in tts_file_paths.items():
            print(f"✓ {paper_id}: {file_path}")
        
        print(f"\n完成！成功生成 {len(tts_file_paths)}/{len(paper_ids)} 个文件")
        
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
