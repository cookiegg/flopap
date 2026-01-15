#!/usr/bin/env python3
"""
最终修复：修正分段算法
"""

import asyncio
import subprocess
import json
import uuid
import random
import re
import time
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
    
    # 按句号分割
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
        
        await asyncio.sleep(random.uniform(0.5, 1.0))
        
        clean_text = clean_markdown_for_tts(text)
        if len(clean_text) > 800:  # 限制文本长度
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


async def main():
    print("🔧 最终修复不完整的论文")
    
    tts_dir = Path("backend/data/tts")
    
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
        
        query_sql = text("""
            SELECT 
                p.id,
                p.title,
                COALESCE(pt.title_zh, p.title) as title_zh,
                pi.interpretation
            FROM papers p
            LEFT JOIN paper_translations pt ON p.id = pt.paper_id
            LEFT JOIN paper_interpretations pi ON p.id = pi.paper_id
            WHERE p.id = ANY(:paper_ids)
            AND pi.interpretation IS NOT NULL
        """)
        
        result = db.execute(query_sql, {"paper_ids": paper_ids})
        
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
        print(f"\n🎵 [{i+1}/{len(incomplete_papers)}] 处理: {paper_id} (缺失 {len(missing_segments)} 个片段)")
        
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
                
                if await generate_segment_tts(segment_text, segment_file):
                    total_generated += 1
                    print(f"    ✅ 成功")
                else:
                    print(f"    ❌ 失败")
    
    print(f"\n🎉 修复完成！生成了 {total_generated} 个片段")


if __name__ == "__main__":
    asyncio.run(main())
