#!/usr/bin/env python3
"""
优化的批量TTS生成脚本
基于final_fix.py的成功经验，适用于任意论文来源
"""

import asyncio
import argparse
import subprocess
import json
import uuid
import random
import re
from pathlib import Path
from typing import List, Tuple
from uuid import UUID
import sys

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
    """将内容分割为6个片段，修正版本"""
    segments = []
    content = content.strip()
    
    sentences = re.split(r'[。！？]', content)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) == 0:
        # 如果没有句子，按字符分割
        chars_per_segment = len(content) // target_segments
        for i in range(target_segments):
            start = i * chars_per_segment
            end = start + chars_per_segment if i < target_segments - 1 else len(content)
            segment_text = content[start:end]
            if segment_text.strip():
                segments.append((f'part_{i+1}', segment_text))
            else:
                segments.append((f'part_{i+1}', '这是一个简短的片段。'))
    elif len(sentences) <= target_segments:
        # 句子数少于或等于目标片段数
        for i, sentence in enumerate(sentences):
            segments.append((f'part_{i+1}', sentence + '。'))
        
        # 补充剩余片段，使用最后一句的重复或简短文本
        last_sentence = sentences[-1] if sentences else "这是补充内容"
        while len(segments) < target_segments:
            segments.append((f'part_{len(segments)+1}', f'{last_sentence}。'))
    else:
        # 句子数多于目标片段数，正常分组
        sentences_per_segment = len(sentences) // target_segments
        remainder = len(sentences) % target_segments
        
        start_idx = 0
        for i in range(target_segments):
            segment_size = sentences_per_segment + (1 if i < remainder else 0)
            segment_sentences = sentences[start_idx:start_idx + segment_size]
            segment_text = '。'.join(segment_sentences) + '。'
            segments.append((f'part_{i+1}', segment_text))
            start_idx += segment_size
    
    return segments[:target_segments]


async def generate_segment_tts(text: str, output_path: Path, voice: str = "zh-CN-XiaoxiaoNeural") -> bool:
    """生成单个片段的TTS音频"""
    try:
        if not text.strip():
            return False
        
        await asyncio.sleep(random.uniform(0.3, 0.8))
        
        clean_text = clean_markdown_for_tts(text)
        if len(clean_text) > 800:
            clean_text = clean_text[:800] + "。"
        
        communicate = edge_tts.Communicate(clean_text, voice)
        
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
        
        return output_path.exists() and output_path.stat().st_size > 0
        
    except Exception as e:
        print(f"    ❌ 生成失败: {e}")
        if 'temp_wav' in locals() and temp_wav.exists():
            temp_wav.unlink()
        return False


async def process_paper(paper_id: UUID, title_en: str, title_zh: str, interpretation: str, output_dir: Path, voice: str) -> dict:
    """处理单篇论文"""
    paper_dir = output_dir / str(paper_id)
    paper_dir.mkdir(exist_ok=True)
    
    # 检查已存在的文件
    existing_count = 0
    for i in range(6):
        segment_file = paper_dir / f"segment_{i:02d}_part_{i+1}.opus"
        if segment_file.exists() and segment_file.stat().st_size > 0:
            existing_count += 1
    
    if existing_count == 6:
        return {'status': 'skipped', 'generated': 0}
    
    # 准备内容并分段
    full_content = f"论文标题：{title_zh}\n英文标题：{title_en}\nAI解读：{interpretation}"
    segments = segment_interpretation(full_content, target_segments=6)
    
    generated = 0
    for i, (segment_type, segment_text) in enumerate(segments):
        segment_file = paper_dir / f"segment_{i:02d}_{segment_type}.opus"
        
        # 跳过已存在的文件
        if segment_file.exists() and segment_file.stat().st_size > 0:
            continue
        
        if await generate_segment_tts(segment_text, segment_file, voice):
            generated += 1
    
    return {'status': 'processed', 'generated': generated}


async def main():
    parser = argparse.ArgumentParser(description="优化的批量TTS生成")
    parser.add_argument("--source", required=True, help="论文来源 (如: conf/iclr2024)")
    parser.add_argument("--concurrency", type=int, default=6, help="并发数")
    parser.add_argument("--voice", default="zh-CN-XiaoxiaoNeural", help="语音模型")
    parser.add_argument("--output-dir", default="backend/data/tts", help="输出目录")
    parser.add_argument("--batch-size", type=int, default=100, help="批处理大小")
    
    args = parser.parse_args()
    
    print(f"🎵 批量TTS生成启动")
    print(f"📚 论文来源: {args.source}")
    print(f"⚡ 并发数: {args.concurrency}")
    print(f"🎤 语音模型: {args.voice}")
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取论文数据
    db = SessionLocal()
    try:
        query = text("""
            SELECT 
                pi.paper_id, 
                p.title,
                COALESCE(pt.title_zh, p.title) as title_zh,
                pi.interpretation
            FROM paper_interpretations pi
            JOIN papers p ON pi.paper_id = p.id
            LEFT JOIN paper_translations pt ON pi.paper_id = pt.paper_id
            WHERE pi.interpretation IS NOT NULL 
            AND LENGTH(pi.interpretation) > 50
            AND p.source = :source
            ORDER BY pi.paper_id
        """)
        
        result = db.execute(query, {"source": args.source})
        papers = [(
            row[0] if isinstance(row[0], UUID) else UUID(row[0]), 
            row[1], row[2], row[3]
        ) for row in result.fetchall()]
        
    finally:
        db.close()
    
    if not papers:
        print(f"❌ 未找到来源为 '{args.source}' 的论文")
        return
    
    print(f"📊 找到 {len(papers)} 篇论文")
    
    # 分批处理
    total_processed = 0
    total_generated = 0
    
    semaphore = asyncio.Semaphore(args.concurrency)
    
    async def process_with_semaphore(paper_data):
        async with semaphore:
            paper_id, title_en, title_zh, interpretation = paper_data
            return await process_paper(paper_id, title_en, title_zh, interpretation, output_dir, args.voice)
    
    for i in range(0, len(papers), args.batch_size):
        batch = papers[i:i + args.batch_size]
        print(f"\n🔄 处理批次 {i//args.batch_size + 1}/{(len(papers) + args.batch_size - 1)//args.batch_size}")
        print(f"📝 当前批次: {len(batch)} 篇论文")
        
        tasks = [process_with_semaphore(paper_data) for paper_data in batch]
        results = await asyncio.gather(*tasks)
        
        batch_processed = sum(1 for r in results if r['status'] == 'processed')
        batch_generated = sum(r['generated'] for r in results)
        
        total_processed += batch_processed
        total_generated += batch_generated
        
        print(f"✅ 批次完成: 处理 {batch_processed} 篇，生成 {batch_generated} 个片段")
    
    print(f"\n🎉 全部完成！")
    print(f"📊 统计:")
    print(f"  总论文数: {len(papers)}")
    print(f"  处理论文: {total_processed}")
    print(f"  生成片段: {total_generated}")


if __name__ == "__main__":
    asyncio.run(main())
