#!/usr/bin/env python3
"""
并行单OPUS生成脚本 - 支持多脚本*多并发
基于generate_single_opus.py改造
"""

import asyncio
import argparse
import subprocess
import re
import sys
import random
import uuid
from pathlib import Path
from uuid import UUID

backend_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_root))

import edge_tts
from sqlalchemy import text
from app.db.session import SessionLocal

def clean_markdown_for_tts(text: str) -> str:
    """清理markdown语法，优化TTS朗读"""
    if not text:
        return text
    
    if text.strip().startswith('```json'):
        try:
            import json
            json_match = re.search(r'```json\s*(\[.*?\])\s*```', text, re.DOTALL)
            if json_match:
                json_data = json.loads(json_match.group(1))
                content_parts = []
                for item in json_data:
                    if isinstance(item, dict) and 'zh' in item:
                        content_parts.append(item['zh'])
                text = '\n\n'.join(content_parts)
        except:
            pass
    
    text = re.sub(r'```[^`]*```', '', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'#{1,6}\s*', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

async def generate_single_tts(paper_id: str, content: str, voice: str, output_path: Path):
    """生成单个TTS文件"""
    try:
        # 随机延迟避免API限制
        await asyncio.sleep(random.uniform(0.5, 1.2))
        
        clean_content = clean_markdown_for_tts(content)
        
        if len(clean_content) < 10:
            print(f"❌ 内容过短: {paper_id}")
            return False
        
        communicate = edge_tts.Communicate(clean_content, voice)
        
        # 唯一临时文件名避免冲突
        temp_wav = output_path.parent / f"temp_{uuid.uuid4().hex[:8]}.wav"
        
        await communicate.save(str(temp_wav))
        
        cmd = [
            'ffmpeg', '-i', str(temp_wav),
            '-c:a', 'libopus',
            '-b:a', '24k',
            '-vbr', 'on',
            '-compression_level', '10',
            '-frame_duration', '60',
            '-y', str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if temp_wav.exists():
            temp_wav.unlink()
        
        if result.returncode != 0:
            print(f"❌ FFmpeg转换失败: {paper_id}")
            return False
        
        if output_path.exists() and output_path.stat().st_size > 1000:
            file_size = output_path.stat().st_size / 1024
            print(f"✅ {paper_id}: {file_size:.1f}KB")
            return True
        else:
            print(f"❌ 输出文件无效: {paper_id}")
            return False
            
    except Exception as e:
        print(f"❌ 生成失败 {paper_id}: {e}")
        if 'temp_wav' in locals() and temp_wav.exists():
            temp_wav.unlink()
        return False

async def process_batch(papers, voice, output_dir, concurrency):
    """处理一批论文"""
    semaphore = asyncio.Semaphore(concurrency)
    
    async def process_single(paper):
        async with semaphore:
            paper_id, title_en, title_zh, interpretation = paper
            
            output_path = output_dir / f"{paper_id}.opus"
            if output_path.exists() and output_path.stat().st_size > 1000:
                print(f"⏭️  跳过已存在: {paper_id}")
                return True
            
            full_content = f"论文标题：{title_zh}\n英文标题：{title_en}\nAI解读：{interpretation}"
            return await generate_single_tts(str(paper_id), full_content, voice, output_path)
    
    tasks = [process_single(paper) for paper in papers]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    success_count = sum(1 for r in results if r is True)
    return success_count, len(papers)

def get_papers_batch(db, offset, limit):
    """获取指定范围的论文"""
    query = text("""
        SELECT p.id, p.title_en, p.title_zh, p.ai_interpretation
        FROM papers p 
        WHERE p.ai_interpretation IS NOT NULL 
        AND LENGTH(p.ai_interpretation) > 100
        ORDER BY p.created_at DESC
        LIMIT :limit OFFSET :offset
    """)
    
    result = db.execute(query, {"limit": limit, "offset": offset})
    return result.fetchall()

async def main():
    parser = argparse.ArgumentParser(description="并行单OPUS生成")
    parser.add_argument("--offset", type=int, default=0, help="起始偏移量")
    parser.add_argument("--limit", type=int, default=50, help="处理数量")
    parser.add_argument("--concurrency", type=int, default=6, help="并发数")
    parser.add_argument("--voice", default="zh-CN-XiaoxiaoNeural", help="语音模型")
    parser.add_argument("--output-dir", default="./data/tts_single", help="输出目录")
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    db = SessionLocal()
    
    try:
        papers = get_papers_batch(db, args.offset, args.limit)
        
        if not papers:
            print("❌ 未找到论文")
            return
        
        print(f"🎵 处理 {len(papers)} 篇论文 (偏移:{args.offset}, 并发:{args.concurrency})")
        
        success, total = await process_batch(papers, args.voice, output_dir, args.concurrency)
        
        print(f"🎉 完成: {success}/{total} 成功")
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
