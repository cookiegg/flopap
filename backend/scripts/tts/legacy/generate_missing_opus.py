#!/usr/bin/env python3
"""
生成缺失的OPUS文件 - 只处理不完整的论文
"""

import asyncio
import argparse
import re
import sys
import subprocess
import json
import uuid
from pathlib import Path
from typing import List, Tuple
from uuid import UUID

backend_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_root))

import edge_tts
from sqlalchemy import text
from app.db.session import SessionLocal


def clean_markdown_for_tts(text: str) -> str:
    """清理markdown语法"""
    if not text:
        return text
    
    if text.strip().startswith('```json'):
        try:
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


def segment_interpretation(content: str, target_segments: int = 6) -> List[Tuple[str, str]]:
    """将内容分割为6个片段"""
    segments = []
    content = content.strip()
    
    sentences = re.split(r'[。！？]', content)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) <= target_segments:
        for i, sentence in enumerate(sentences):
            segments.append((f'part_{i+1}', sentence + '。'))
    else:
        sentences_per_segment = len(sentences) // target_segments
        remainder = len(sentences) % target_segments
        
        start_idx = 0
        for i in range(target_segments):
            segment_size = sentences_per_segment + (1 if i < remainder else 0)
            segment_sentences = sentences[start_idx:start_idx + segment_size]
            segment_text = '。'.join(segment_sentences) + '。'
            segments.append((f'part_{i+1}', segment_text))
            start_idx += segment_size
    
    while len(segments) < target_segments:
        segments.append((f'part_{len(segments)+1}', ''))
    
    return segments[:target_segments]


async def generate_segment_tts(text: str, output_path: Path, voice: str = "zh-CN-XiaoxiaoNeural") -> bool:
    """生成单个片段的TTS音频"""
    try:
        if not text.strip():
            return False
        
        # 添加随机延迟避免突发请求
        import random
        await asyncio.sleep(random.uniform(0.1, 0.5))
            
        clean_text = clean_markdown_for_tts(text)
        communicate = edge_tts.Communicate(clean_text, voice)
        
        # 使用唯一临时文件名
        temp_wav = output_path.parent / f"temp_{uuid.uuid4().hex[:8]}.wav"
        await communicate.save(str(temp_wav))
        
        cmd = [
            "ffmpeg", "-i", str(temp_wav),
            "-c:a", "libopus", "-ar", "24000", "-b:a", "20k",
            "-application", "voip", "-y", str(output_path)
        ]
        
        subprocess.run(cmd, capture_output=True, check=True)
        
        if temp_wav.exists():
            temp_wav.unlink()
        
        return True
        
    except Exception as e:
        print(f"  ❌ 生成失败: {e}")
        if 'temp_wav' in locals() and temp_wav.exists():
            temp_wav.unlink()
        return False


def check_missing_segments(paper_dir: Path) -> List[int]:
    """检查缺失的片段"""
    missing = []
    for i in range(6):
        opus_file = paper_dir / f"segment_{i:02d}_part_{i+1}.opus"
        if not opus_file.exists():
            missing.append(i)
    return missing


async def process_missing_paper(paper_id: UUID, missing_segments: List[int]) -> int:
    """处理缺失片段的论文"""
    db = SessionLocal()
    
    try:
        # 获取论文信息
        query_sql = text("""
            SELECT 
                p.title,
                COALESCE(pt.title_zh, p.title) as title_zh,
                pi.interpretation
            FROM papers p
            LEFT JOIN paper_translations pt ON p.id = pt.paper_id
            LEFT JOIN paper_interpretations pi ON p.id = pi.paper_id
            WHERE p.id = :paper_id
            AND pi.interpretation IS NOT NULL
        """)
        
        result = db.execute(query_sql, {"paper_id": paper_id})
        row = result.fetchone()
        
        if not row:
            print(f"❌ 论文 {paper_id} 没有AI解读")
            return 0
        
        title_en, title_zh, interpretation = row
        
        # 准备完整内容并分段
        full_content = f"论文标题：{title_zh}\n英文标题：{title_en}\nAI解读：{interpretation}"
        segments = segment_interpretation(full_content, target_segments=6)
        
        paper_dir = Path("backend/data/tts") / str(paper_id)
        paper_dir.mkdir(exist_ok=True)
        
        success_count = 0
        
        # 只生成缺失的片段
        for segment_idx in missing_segments:
            if segment_idx < len(segments):
                segment_type, segment_text = segments[segment_idx]
                segment_file = paper_dir / f"segment_{segment_idx:02d}_{segment_type}.opus"
                
                print(f"  🔄 生成片段 {segment_idx+1}: {len(segment_text)} 字符")
                
                if await generate_segment_tts(segment_text, segment_file):
                    success_count += 1
                    print(f"    ✅ 成功")
                else:
                    print(f"    ❌ 失败")
        
        return success_count
        
    finally:
        db.close()


async def main():
    parser = argparse.ArgumentParser(description="生成缺失的OPUS文件")
    parser.add_argument("--batch-id", type=int, default=0, help="批次ID (0-2)")
    parser.add_argument("--concurrency", type=int, default=8, help="并发数")
    args = parser.parse_args()
    
    if args.batch_id < 0 or args.batch_id > 2:
        print("❌ 批次ID必须在0-2之间")
        return
    
    print(f"🔧 生成缺失的OPUS文件 - 批次{args.batch_id+1}/3，并发:{args.concurrency}")
    
    tts_dir = Path("backend/data/tts")
    if not tts_dir.exists():
        print("❌ TTS目录不存在")
        return
    
    # 统计不完整的论文
    all_incomplete_papers = []
    
    for paper_dir in tts_dir.iterdir():
        if not paper_dir.is_dir() or not paper_dir.name.count('-') == 4:
            continue
        
        missing_segments = check_missing_segments(paper_dir)
        if missing_segments:
            try:
                paper_id = UUID(paper_dir.name)
                all_incomplete_papers.append((paper_id, missing_segments))
            except ValueError:
                continue
    
    # 按批次分配论文
    total_papers = len(all_incomplete_papers)
    papers_per_batch = (total_papers + 2) // 3  # 向上取整
    start_idx = args.batch_id * papers_per_batch
    end_idx = min(start_idx + papers_per_batch, total_papers)
    
    incomplete_papers = all_incomplete_papers[start_idx:end_idx]
    
    print(f"📊 批次{args.batch_id+1}: {len(incomplete_papers)} 篇不完整论文 (总计:{total_papers}篇)")
    
    if not incomplete_papers:
        print("✅ 当前批次无需处理")
        return
    
    # 处理不完整的论文
    total_generated = 0
    
    # 使用信号量控制并发
    semaphore = asyncio.Semaphore(args.concurrency)
    
    async def process_with_semaphore(paper_data):
        async with semaphore:
            paper_id, missing_segments = paper_data
            print(f"\n🎵 处理论文: {paper_id} (缺失 {len(missing_segments)} 个片段)")
            return await process_missing_paper(paper_id, missing_segments)
    
    tasks = [process_with_semaphore(paper_data) for paper_data in incomplete_papers]
    results = await asyncio.gather(*tasks)
    
    total_generated = sum(results)
    
    print(f"\n🎉 批次{args.batch_id+1}补全完成！")
    print(f"📊 统计:")
    print(f"  处理论文: {len(incomplete_papers)}")
    print(f"  生成片段: {total_generated}")


if __name__ == "__main__":
    asyncio.run(main())
