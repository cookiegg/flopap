#!/usr/bin/env python3
"""
最终清理：转换剩余WAV文件并补全最后的缺失片段
"""

import asyncio
import argparse
import re
import sys
import subprocess
import json
import uuid
import random
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


def convert_wav_to_opus(wav_path: Path) -> bool:
    """转换WAV为OPUS"""
    try:
        opus_path = wav_path.with_suffix('.opus')
        cmd = [
            "ffmpeg", "-i", str(wav_path),
            "-c:a", "libopus", "-ar", "24000", "-b:a", "20k",
            "-application", "voip", "-y", str(opus_path)
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        wav_path.unlink()
        return True
    except Exception as e:
        print(f"❌ 转换失败 {wav_path}: {e}")
        return False


async def generate_segment_tts(text: str, output_path: Path, voice: str = "zh-CN-XiaoxiaoNeural") -> bool:
    """生成单个片段的TTS音频"""
    try:
        if not text.strip():
            return False
        
        await asyncio.sleep(random.uniform(0.2, 0.8))
            
        clean_text = clean_markdown_for_tts(text)
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
        
        return True
        
    except Exception as e:
        print(f"  ❌ 生成失败: {e}")
        if 'temp_wav' in locals() and temp_wav.exists():
            temp_wav.unlink()
        return False


async def main():
    print("🔧 最终清理：转换WAV文件并补全缺失片段")
    
    tts_dir = Path("backend/data/tts")
    
    # 1. 转换剩余的WAV文件
    wav_files = list(tts_dir.glob("**/*.wav"))
    converted_count = 0
    
    print(f"📁 发现 {len(wav_files)} 个WAV文件需要转换")
    
    for wav_file in wav_files:
        if wav_file.stat().st_size > 0:
            if convert_wav_to_opus(wav_file):
                converted_count += 1
                print(f"✅ 转换: {wav_file.name}")
    
    print(f"📊 转换完成: {converted_count}/{len(wav_files)}")
    
    # 2. 找出仍然不完整的论文
    incomplete_papers = []
    
    for paper_dir in tts_dir.iterdir():
        if not paper_dir.is_dir() or not paper_dir.name.count('-') == 4:
            continue
        
        opus_files = list(paper_dir.glob('*.opus'))
        if len(opus_files) < 6:
            missing_segments = []
            for i in range(6):
                opus_file = paper_dir / f"segment_{i:02d}_part_{i+1}.opus"
                if not opus_file.exists():
                    missing_segments.append(i)
            
            try:
                paper_id = UUID(paper_dir.name)
                incomplete_papers.append((paper_id, missing_segments))
            except ValueError:
                continue
    
    print(f"📊 发现 {len(incomplete_papers)} 篇仍不完整的论文")
    
    if not incomplete_papers:
        print("✅ 所有论文都已完整")
        return
    
    # 3. 补全剩余缺失片段（单线程，更保守）
    db = SessionLocal()
    total_generated = 0
    
    try:
        for paper_id, missing_segments in incomplete_papers:
            print(f"\n🎵 处理论文: {paper_id} (缺失 {len(missing_segments)} 个片段)")
            
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
                continue
            
            title_en, title_zh, interpretation = row
            
            # 准备完整内容并分段
            full_content = f"论文标题：{title_zh}\n英文标题：{title_en}\nAI解读：{interpretation}"
            segments = segment_interpretation(full_content, target_segments=6)
            
            paper_dir = tts_dir / str(paper_id)
            
            # 只生成缺失的片段
            for segment_idx in missing_segments:
                if segment_idx < len(segments):
                    segment_type, segment_text = segments[segment_idx]
                    segment_file = paper_dir / f"segment_{segment_idx:02d}_{segment_type}.opus"
                    
                    print(f"  🔄 生成片段 {segment_idx+1}: {len(segment_text)} 字符")
                    
                    if await generate_segment_tts(segment_text, segment_file):
                        total_generated += 1
                        print(f"    ✅ 成功")
                    else:
                        print(f"    ❌ 失败")
    
    finally:
        db.close()
    
    print(f"\n🎉 最终清理完成！")
    print(f"📊 统计:")
    print(f"  转换WAV: {converted_count}")
    print(f"  处理论文: {len(incomplete_papers)}")
    print(f"  生成片段: {total_generated}")


if __name__ == "__main__":
    asyncio.run(main())
