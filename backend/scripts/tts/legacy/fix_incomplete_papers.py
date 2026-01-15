#!/usr/bin/env python3
"""
修复不完整论文的TTS文件
"""

import asyncio
import argparse
from pathlib import Path
from uuid import UUID
import sys

# 复用final_fix.py的核心逻辑
backend_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_root))

from sqlalchemy import text
from app.db.session import SessionLocal

# 导入生成函数
from generate_batch_tts_optimized import segment_interpretation, generate_segment_tts


async def main():
    parser = argparse.ArgumentParser(description="修复不完整的TTS文件")
    parser.add_argument("--source", help="论文来源过滤 (可选)")
    parser.add_argument("--voice", default="zh-CN-XiaoxiaoNeural", help="语音模型")
    parser.add_argument("--output-dir", default="backend/data/tts", help="TTS目录")
    
    args = parser.parse_args()
    
    print("🔧 修复不完整的TTS文件")
    
    tts_dir = Path(args.output_dir)
    
    # 找出不完整的论文
    incomplete_papers = []
    
    for paper_dir in tts_dir.iterdir():
        if not paper_dir.is_dir():
            continue
        
        try:
            paper_id = UUID(paper_dir.name)
        except ValueError:
            continue
        
        opus_files = list(paper_dir.glob('*.opus'))
        if len(opus_files) < 6:
            missing_segments = []
            for i in range(6):
                opus_file = paper_dir / f"segment_{i:02d}_part_{i+1}.opus"
                if not opus_file.exists():
                    missing_segments.append(i)
            
            if missing_segments:
                incomplete_papers.append((paper_id, missing_segments))
    
    print(f"📊 发现 {len(incomplete_papers)} 篇不完整论文")
    
    if not incomplete_papers:
        print("✅ 所有论文都已完整")
        return
    
    # 批量获取论文数据
    db = SessionLocal()
    paper_data = {}
    
    try:
        paper_ids = [str(pid) for pid, _ in incomplete_papers]
        
        where_clause = "p.id = ANY(:paper_ids)"
        params = {"paper_ids": paper_ids}
        
        if args.source:
            where_clause += " AND p.source = :source"
            params["source"] = args.source
        
        query_sql = text(f"""
            SELECT 
                p.id,
                p.title,
                COALESCE(pt.title_zh, p.title) as title_zh,
                pi.interpretation
            FROM papers p
            LEFT JOIN paper_translations pt ON p.id = pt.paper_id
            LEFT JOIN paper_interpretations pi ON p.id = pi.paper_id
            WHERE {where_clause}
            AND pi.interpretation IS NOT NULL
        """)
        
        result = db.execute(query_sql, params)
        
        for row in result:
            paper_data[row.id] = {
                'title_en': row.title,
                'title_zh': row.title_zh,
                'interpretation': row.interpretation
            }
    
    finally:
        db.close()
    
    # 生成缺失片段
    total_generated = 0
    
    for i, (paper_id, missing_segments) in enumerate(incomplete_papers):
        if paper_id not in paper_data:
            print(f"❌ 论文 {paper_id} 没有AI解读")
            continue
        
        data = paper_data[paper_id]
        print(f"\n🎵 [{i+1}/{len(incomplete_papers)}] 修复: {paper_id} (缺失 {len(missing_segments)} 个片段)")
        
        # 准备内容并分段
        full_content = f"论文标题：{data['title_zh']}\n英文标题：{data['title_en']}\nAI解读：{data['interpretation']}"
        segments = segment_interpretation(full_content, target_segments=6)
        
        paper_dir = tts_dir / str(paper_id)
        
        # 生成缺失片段
        for segment_idx in missing_segments:
            if segment_idx < len(segments):
                segment_type, segment_text = segments[segment_idx]
                segment_file = paper_dir / f"segment_{segment_idx:02d}_{segment_type}.opus"
                
                print(f"  🔄 片段 {segment_idx+1} ({len(segment_text)} 字符)")
                
                if await generate_segment_tts(segment_text, segment_file, args.voice):
                    total_generated += 1
                    print(f"    ✅ 成功")
                else:
                    print(f"    ❌ 失败")
    
    print(f"\n🎉 修复完成！生成了 {total_generated} 个片段")


if __name__ == "__main__":
    asyncio.run(main())
