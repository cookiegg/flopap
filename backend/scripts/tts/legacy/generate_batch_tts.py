#!/usr/bin/env python3
"""
分批TTS生成脚本 - 支持指定偏移量和数量
"""

import asyncio
import argparse
import re
import sys
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Tuple
from uuid import UUID

backend_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_root))

import edge_tts
from sqlalchemy import text
from app.db.session import SessionLocal


def clean_markdown_for_tts(text: str) -> str:
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
    try:
        if not text.strip():
            return False
            
        clean_text = clean_markdown_for_tts(text)
        communicate = edge_tts.Communicate(clean_text, voice)
        
        temp_wav = output_path.with_suffix('.wav')
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
        return False


async def process_paper(paper_id: UUID, title_en: str, title_zh: str, interpretation: str, output_dir: Path, voice: str) -> Dict:
    print(f"\n🎵 处理论文: {paper_id}")
    print(f"  📖 标题: {title_zh}")
    
    paper_dir = output_dir / str(paper_id)
    paper_dir.mkdir(exist_ok=True)
    
    # 检查已存在的文件
    existing_files = []
    for i in range(6):
        segment_file = paper_dir / f"segment_{i:02d}_part_{i+1}.opus"
        if segment_file.exists() and segment_file.stat().st_size > 0:
            existing_files.append(i)
    
    if len(existing_files) == 6:
        total_size = sum((paper_dir / f"segment_{i:02d}_part_{i+1}.opus").stat().st_size for i in range(6))
        print(f"  ✅ 已存在完整音频文件，跳过生成")
        return {'successful': 6, 'total': 6, 'size': total_size}
    
    full_content = f"论文标题：{title_zh}\n英文标题：{title_en}\nAI解读：{interpretation}"
    
    segments = segment_interpretation(full_content, target_segments=6)
    print(f"  📝 分割为 {len(segments)} 个片段")
    
    results = {'successful': len(existing_files), 'total': len(segments), 'size': 0}
    
    for i, (segment_type, text) in enumerate(segments):
        segment_file = paper_dir / f"segment_{i:02d}_{segment_type}.opus"
        
        # 检查文件是否已存在
        if i in existing_files:
            file_size = segment_file.stat().st_size
            results['size'] += file_size
            print(f"  ⏭️  片段 {i+1}/{len(segments)}: 已存在 ({file_size:,} bytes)")
            continue
        
        print(f"  🔄 片段 {i+1}/{len(segments)}: {len(text)} 字符")
        
        success = await generate_segment_tts(text, segment_file, voice)
        
        if success and segment_file.exists():
            file_size = segment_file.stat().st_size
            results['successful'] += 1
            results['size'] += file_size
            print(f"    ✅ 成功: {file_size:,} bytes")
        else:
            print(f"    ❌ 失败")
    
    return results


async def main():
    parser = argparse.ArgumentParser(description="分批TTS生成")
    parser.add_argument("--offset", type=int, default=0, help="起始偏移")
    parser.add_argument("--limit", type=int, default=50, help="处理数量")
    parser.add_argument("--concurrency", type=int, default=12, help="并发数")
    args = parser.parse_args()
    
    print(f"🎵 分批TTS生成(NeurIPS 2025) - 偏移:{args.offset}, 数量:{args.limit}, 并发:{args.concurrency}")
    
    output_dir = Path("backend/data/tts")
    output_dir.mkdir(parents=True, exist_ok=True)
    
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
            AND LENGTH(pi.interpretation) > 100
            AND p.source = 'conf/neurips2025'
            ORDER BY pi.paper_id
            LIMIT :limit OFFSET :offset
        """)
        
        result = db.execute(query, {"limit": args.limit, "offset": args.offset})
        papers = [(
            row[0] if isinstance(row[0], UUID) else UUID(row[0]), 
            row[1], row[2], row[3]
        ) for row in result.fetchall()]
        
        if not papers:
            print("❌ 没有找到可处理的论文")
            return
        
        print(f"📚 找到 {len(papers)} 篇论文")
        
        total_stats = {'processed': 0, 'successful_segments': 0, 'total_segments': 0, 'total_size': 0}
        
        semaphore = asyncio.Semaphore(args.concurrency)
        
        async def process_with_semaphore(paper_data):
            async with semaphore:
                paper_id, title_en, title_zh, interpretation = paper_data
                try:
                    return await process_paper(paper_id, title_en, title_zh, interpretation, output_dir, "zh-CN-XiaoxiaoNeural")
                except Exception as e:
                    print(f"❌ 处理论文 {paper_id} 失败: {e}")
                    return {'successful': 0, 'total': 0, 'size': 0}
        
        tasks = [process_with_semaphore(paper_data) for paper_data in papers]
        results = await asyncio.gather(*tasks)
        
        for result in results:
            total_stats['processed'] += 1
            total_stats['successful_segments'] += result['successful']
            total_stats['total_segments'] += result['total']
            total_stats['total_size'] += result['size']
        
        print(f"\n🎉 批次完成！")
        print(f"📊 统计:")
        print(f"  处理论文: {total_stats['processed']}")
        print(f"  成功片段: {total_stats['successful_segments']}/{total_stats['total_segments']}")
        print(f"  成功率: {total_stats['successful_segments']/total_stats['total_segments']*100:.1f}%")
        print(f"  总大小: {total_stats['total_size']:,} bytes ({total_stats['total_size']/1024/1024:.1f} MB)")
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
