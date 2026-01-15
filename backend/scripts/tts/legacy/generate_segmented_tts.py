#!/usr/bin/env python3
"""
AI解读分段TTS生成脚本
将AI解读内容按段落切分，生成OPUS 24kHz格式的音频片段
"""

import argparse
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
    text = re.sub(r'```[^`]*```', '', text)  # 代码块
    text = re.sub(r'`([^`]+)`', r'\1', text)  # 行内代码
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # 加粗
    text = re.sub(r'\*([^*]+)\*', r'\1', text)  # 斜体
    text = re.sub(r'#{1,6}\s*', '', text)  # 标题
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # 链接
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)  # 列表
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)  # 数字列表
    text = re.sub(r'\n{3,}', '\n\n', text)  # 多余换行
    
    return text.strip()


class AIInterpretationSegmenter:
    """AI解读内容分段器"""
    
    @staticmethod
    def segment_interpretation(content: str, target_segments: int = 6) -> List[Tuple[str, str]]:
        """
        将AI解读内容按结构化段落分割为指定数量的片段
        
        Args:
            content: AI解读内容
            target_segments: 目标片段数量
            
        Returns:
            List of (segment_type, text) tuples
        """
        segments = []
        
        # 清理内容
        content = content.strip()
        
        # 先按主要结构分割
        major_sections = []
        
        # 按标题和重要标记分割
        parts = re.split(r'(?=##\s)|(?=\*\*(?:核心创新点|主要贡献|研究背景|核心方法|实验结果|学术价值)\*\*)', content)
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # 识别段落类型
            if part.startswith('##'):
                title = re.sub(r'^##\s*', '', part).strip()
                major_sections.append(('title', title))
            elif any(keyword in part for keyword in ['核心创新点', '主要贡献', '研究背景', '核心方法', '实验结果', '学术价值']):
                major_sections.append(('key_section', part))
            else:
                major_sections.append(('content', part))
        
        # 如果没有明显结构，按长度均匀分割
        if len(major_sections) <= 1:
            text_length = len(content)
            segment_length = text_length // target_segments
            
            sentences = re.split(r'[。！？]', content)
            current_segment = ""
            segment_count = 0
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                
                if len(current_segment + sentence) > segment_length and current_segment and segment_count < target_segments - 1:
                    segments.append((f'part_{segment_count + 1}', current_segment.strip()))
                    current_segment = sentence + "。"
                    segment_count += 1
                else:
                    current_segment += sentence + "。"
            
            if current_segment:
                segments.append((f'part_{segment_count + 1}', current_segment.strip()))
        
        else:
            # 合并小段落，确保达到目标数量
            if len(major_sections) > target_segments:
                # 需要合并
                segments_per_group = len(major_sections) // target_segments
                remainder = len(major_sections) % target_segments
                
                current_group = ""
                group_count = 0
                items_in_group = 0
                target_items = segments_per_group + (1 if group_count < remainder else 0)
                
                for section_type, text in major_sections:
                    if items_in_group >= target_items and group_count < target_segments - 1:
                        segments.append((f'section_{group_count + 1}', current_group.strip()))
                        current_group = text
                        group_count += 1
                        items_in_group = 1
                        target_items = segments_per_group + (1 if group_count < remainder else 0)
                    else:
                        if current_group:
                            current_group += "\n\n" + text
                        else:
                            current_group = text
                        items_in_group += 1
                
                if current_group:
                    segments.append((f'section_{group_count + 1}', current_group.strip()))
            
            elif len(major_sections) < target_segments:
                # 需要拆分长段落
                for section_type, text in major_sections:
                    if len(text) > 300:  # 长段落需要拆分
                        sentences = re.split(r'[。！？]', text)
                        mid_point = len(sentences) // 2
                        
                        part1 = "。".join(sentences[:mid_point]).strip() + "。"
                        part2 = "。".join(sentences[mid_point:]).strip()
                        
                        segments.append((section_type + '_1', part1))
                        segments.append((section_type + '_2', part2))
                    else:
                        segments.append((section_type, text))
            
            else:
                # 数量刚好
                segments = major_sections
        
        # 确保不超过目标数量
        if len(segments) > target_segments:
            # 合并最后几个段落
            excess = len(segments) - target_segments
            if excess > 0:
                last_segments = segments[-(excess + 1):]
                combined_text = "\n\n".join([text for _, text in last_segments])
                segments = segments[:-(excess + 1)]
                segments.append(('final_section', combined_text))
        
        # 确保至少有目标数量的段落
        while len(segments) < target_segments and segments:
            # 找最长的段落进行拆分
            longest_idx = max(range(len(segments)), key=lambda i: len(segments[i][1]))
            section_type, text = segments[longest_idx]
            
            if len(text) > 100:  # 只拆分足够长的段落
                sentences = re.split(r'[。！？]', text)
                if len(sentences) > 2:
                    mid_point = len(sentences) // 2
                    part1 = "。".join(sentences[:mid_point]).strip() + "。"
                    part2 = "。".join(sentences[mid_point:]).strip()
                    
                    segments[longest_idx] = (section_type + '_1', part1)
                    segments.insert(longest_idx + 1, (section_type + '_2', part2))
                else:
                    break
            else:
                break
        
        return segments[:target_segments]


async def generate_segment_tts(text: str, output_path: Path, voice: str = "zh-CN-XiaoxiaoNeural") -> bool:
    """生成单个片段的TTS音频"""
    try:
        # 清理markdown语法
        clean_text = clean_markdown_for_tts(text)
        
        # 生成TTS
        communicate = edge_tts.Communicate(clean_text, voice)
        
        # 先生成WAV文件
        temp_wav = output_path.with_suffix('.wav')
        await communicate.save(str(temp_wav))
        
        # 转换为OPUS 24kHz
        cmd = [
            "ffmpeg",
            "-i", str(temp_wav),
            "-c:a", "libopus",
            "-ar", "24000",
            "-b:a", "20k",
            "-application", "voip",
            "-y",
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # 删除临时WAV文件
        if temp_wav.exists():
            temp_wav.unlink()
        
        return True
        
    except Exception as e:
        print(f"  ❌ 生成失败: {e}")
        return False


async def process_paper_interpretation(
    paper_id: UUID, 
    title_en: str,
    title_zh: str,
    interpretation: str, 
    output_dir: Path,
    voice: str = "zh-CN-XiaoxiaoNeural"
) -> Dict[str, any]:
    """处理单篇论文的AI解读"""
    
    print(f"\n🎵 处理论文: {paper_id}")
    print(f"  📖 标题: {title_zh}")
    
    # 创建论文专用目录
    paper_dir = output_dir / str(paper_id)
    paper_dir.mkdir(exist_ok=True)
    
    # 准备完整内容（包含标题朗读）
    full_content = f"""
论文标题：{title_zh}

英文标题：{title_en}

AI解读：{interpretation}
    """.strip()
    
    # 分段
    segmenter = AIInterpretationSegmenter()
    segments = segmenter.segment_interpretation(full_content, target_segments=6)
    
    print(f"  📝 分割为 {len(segments)} 个片段")
    
    results = {
        'paper_id': paper_id,
        'title_zh': title_zh,
        'title_en': title_en,
        'total_segments': len(segments),
        'successful_segments': 0,
        'failed_segments': 0,
        'segment_files': [],
        'total_size': 0
    }
    
    # 生成每个片段的音频
    for i, (segment_type, text) in enumerate(segments):
        segment_file = paper_dir / f"segment_{i:02d}_{segment_type}.opus"
        
        print(f"  🔄 片段 {i+1}/{len(segments)}: {segment_type} ({len(text)} 字符)")
        
        success = await generate_segment_tts(text, segment_file, voice)
        
        if success and segment_file.exists():
            file_size = segment_file.stat().st_size
            results['successful_segments'] += 1
            results['segment_files'].append({
                'index': i,
                'type': segment_type,
                'file': str(segment_file),
                'size': file_size,
                'text_length': len(text),
                'text_preview': text[:100] + '...' if len(text) > 100 else text
            })
            results['total_size'] += file_size
            print(f"    ✅ 成功: {file_size:,} bytes")
        else:
            results['failed_segments'] += 1
            print(f"    ❌ 失败")
    
    # 生成片段索引文件
    index_file = paper_dir / "segments.json"
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump({
            'paper_id': str(paper_id),
            'title_zh': title_zh,
            'title_en': title_en,
            'total_segments': results['total_segments'],
            'segments': results['segment_files']
        }, f, ensure_ascii=False, indent=2)
    
    print(f"  📊 完成: {results['successful_segments']}/{results['total_segments']} 片段")
    print(f"  💾 总大小: {results['total_size']:,} bytes")
    
    return results


async def main():
    parser = argparse.ArgumentParser(description="AI解读分段TTS生成")
    parser.add_argument("--batch-size", type=int, default=5, help="每批处理数量")
    parser.add_argument("--voice", default="zh-CN-XiaoxiaoNeural", help="语音模型")
    parser.add_argument("--output-dir", default="backend/data/tts_segments", help="输出目录")
    parser.add_argument("--start-offset", type=int, default=0, help="起始偏移")
    parser.add_argument("--source", default="all", help="数据源 (all/neurips2025)")
    args = parser.parse_args()
    
    print(f"🎵 AI解读分段TTS生成器")
    print(f"配置: 每批{args.batch_size}篇，语音模型: {args.voice}")
    
    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    db = SessionLocal()
    
    try:
        # 构建查询
        if args.source == "neurips2025":
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
        else:
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
                LIMIT :limit OFFSET :offset
            """)
        
        # 获取论文数据
        result = db.execute(query, {"limit": args.batch_size, "offset": args.start_offset})
        papers = [(
            row[0] if isinstance(row[0], UUID) else UUID(row[0]), 
            row[1], 
            row[2], 
            row[3]
        ) for row in result.fetchall()]
        
        if not papers:
            print("❌ 没有找到可处理的论文")
            return
        
        print(f"📚 找到 {len(papers)} 篇论文")
        
        # 处理每篇论文
        total_results = {
            'processed_papers': 0,
            'total_segments': 0,
            'successful_segments': 0,
            'total_size': 0
        }
        
        for paper_id, title_en, title_zh, interpretation in papers:
            try:
                result = await process_paper_interpretation(
                    paper_id, title_en, title_zh, interpretation, output_dir, args.voice
                )
                
                total_results['processed_papers'] += 1
                total_results['total_segments'] += result['total_segments']
                total_results['successful_segments'] += result['successful_segments']
                total_results['total_size'] += result['total_size']
                
            except Exception as e:
                print(f"❌ 处理论文 {paper_id} 失败: {e}")
                continue
        
        # 输出总结
        print(f"\n🎉 处理完成！")
        print(f"📊 统计:")
        print(f"  处理论文: {total_results['processed_papers']}")
        print(f"  总片段数: {total_results['total_segments']}")
        print(f"  成功片段: {total_results['successful_segments']}")
        print(f"  成功率: {total_results['successful_segments']/total_results['total_segments']*100:.1f}%")
        print(f"  总大小: {total_results['total_size']:,} bytes ({total_results['total_size']/1024/1024:.1f} MB)")
        print(f"📁 输出目录: {output_dir}")
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
