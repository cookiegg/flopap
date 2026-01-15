#!/usr/bin/env python3
"""
为100篇有AI解读的论文生成6分段OPUS 24kHz音频
保存到 backend/data/tts/ 目录
"""

import asyncio
import re
import sys
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Tuple
from uuid import UUID

# 添加backend根目录到路径
backend_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_root))

import edge_tts
from sqlalchemy import text
from app.db.session import SessionLocal


def clean_markdown_for_tts(text: str) -> str:
    """清理markdown语法，使其适合TTS"""
    if not text:
        return text
    
    # 处理JSON格式的内容
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
    
    # 清理markdown语法
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
    """将AI解读内容分割为6个片段"""
    segments = []
    content = content.strip()
    
    # 按句子分割
    sentences = re.split(r'[。！？]', content)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) <= target_segments:
        # 句子数不够，每个句子一个片段
        for i, sentence in enumerate(sentences):
            segments.append((f'part_{i+1}', sentence + '。'))
    else:
        # 均匀分配句子到各个片段
        sentences_per_segment = len(sentences) // target_segments
        remainder = len(sentences) % target_segments
        
        start_idx = 0
        for i in range(target_segments):
            segment_size = sentences_per_segment + (1 if i < remainder else 0)
            segment_sentences = sentences[start_idx:start_idx + segment_size]
            segment_text = '。'.join(segment_sentences) + '。'
            segments.append((f'part_{i+1}', segment_text))
            start_idx += segment_size
    
    # 确保有6个片段
    while len(segments) < target_segments:
        segments.append((f'part_{len(segments)+1}', ''))
    
    return segments[:target_segments]


async def generate_segment_tts(text: str, output_path: Path, voice: str = "zh-CN-XiaoxiaoNeural") -> bool:
    """生成单个片段的TTS音频"""
    try:
        if not text.strip():
            return False
            
        clean_text = clean_markdown_for_tts(text)
        communicate = edge_tts.Communicate(clean_text, voice)
        
        # 先生成WAV文件
        temp_wav = output_path.with_suffix('.wav')
        await communicate.save(str(temp_wav))
        
        # 转换为OPUS 24kHz
        cmd = [
            "ffmpeg", "-i", str(temp_wav),
            "-c:a", "libopus", "-ar", "24000", "-b:a", "20k",
            "-application", "voip", "-y", str(output_path)
        ]
        
        subprocess.run(cmd, capture_output=True, check=True)
        
        # 删除临时WAV文件
        if temp_wav.exists():
            temp_wav.unlink()
        
        return True
        
    except Exception as e:
        print(f"  ❌ 生成失败: {e}")
        return False


async def process_paper(paper_id: UUID, title_en: str, title_zh: str, interpretation: str, output_dir: Path, voice: str) -> Dict:
    """处理单篇论文"""
    print(f"\n🎵 处理论文: {paper_id}")
    print(f"  📖 标题: {title_zh}")
    
    # 创建论文目录
    paper_dir = output_dir / str(paper_id)
    paper_dir.mkdir(exist_ok=True)
    
    # 准备完整内容
    full_content = f"论文标题：{title_zh}\n英文标题：{title_en}\nAI解读：{interpretation}"
    
    # 分段
    segments = segment_interpretation(full_content, target_segments=6)
    print(f"  📝 分割为 {len(segments)} 个片段")
    
    results = {'successful': 0, 'total': len(segments), 'size': 0}
    
    # 生成每个片段的音频
    for i, (segment_type, text) in enumerate(segments):
        segment_file = paper_dir / f"segment_{i:02d}_{segment_type}.opus"
        
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
    print("🎵 为100篇论文生成6分段OPUS 24kHz音频")
    
    # 创建输出目录
    output_dir = Path("backend/data/tts")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    db = SessionLocal()
    
    try:
        # 获取100篇有AI解读的论文
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
            ORDER BY pi.paper_id
            LIMIT 100
        """)
        
        result = db.execute(query)
        papers = [(
            row[0] if isinstance(row[0], UUID) else UUID(row[0]), 
            row[1], row[2], row[3]
        ) for row in result.fetchall()]
        
        if not papers:
            print("❌ 没有找到可处理的论文")
            return
        
        print(f"📚 找到 {len(papers)} 篇论文")
        
        # 处理每篇论文 - 12个并发
        total_stats = {'processed': 0, 'successful_segments': 0, 'total_segments': 0, 'total_size': 0}
        
        semaphore = asyncio.Semaphore(12)
        
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
        
        # 输出统计
        print(f"\n🎉 处理完成！")
        print(f"📊 统计:")
        print(f"  处理论文: {total_stats['processed']}")
        print(f"  成功片段: {total_stats['successful_segments']}/{total_stats['total_segments']}")
        print(f"  成功率: {total_stats['successful_segments']/total_stats['total_segments']*100:.1f}%")
        print(f"  总大小: {total_stats['total_size']:,} bytes ({total_stats['total_size']/1024/1024:.1f} MB)")
        print(f"📁 输出目录: {output_dir}")
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
