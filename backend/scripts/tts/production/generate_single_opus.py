#!/usr/bin/env python3
"""
AI解读TTS生成脚本 - 单个OPUS文件，低码率优化
"""

import asyncio
import argparse
import subprocess
import re
import sys
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
    
    # 处理JSON格式的解读内容
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

async def generate_single_tts(paper_id: str, content: str, voice: str, output_path: Path):
    """生成单个TTS文件"""
    try:
        # 清理内容
        clean_content = clean_markdown_for_tts(content)
        
        if len(clean_content) < 10:
            print(f"❌ 内容过短: {paper_id}")
            return False
        
        # 生成TTS
        communicate = edge_tts.Communicate(clean_content, voice)
        
        # 临时WAV文件
        temp_wav = output_path.with_suffix('.wav')
        
        # 保存为WAV
        await communicate.save(str(temp_wav))
        
        # 转换为低码率OPUS
        cmd = [
            'ffmpeg', '-i', str(temp_wav),
            '-c:a', 'libopus',
            '-b:a', '24k',  # 24kbps码率
            '-vbr', 'on',   # 可变比特率
            '-compression_level', '10',  # 最高压缩
            '-frame_duration', '60',     # 60ms帧长度
            '-y',  # 覆盖输出文件
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ FFmpeg转换失败: {paper_id}")
            print(f"   错误: {result.stderr}")
            return False
        
        # 删除临时WAV文件
        temp_wav.unlink(missing_ok=True)
        
        # 检查输出文件
        if output_path.exists() and output_path.stat().st_size > 1000:
            file_size = output_path.stat().st_size / 1024
            print(f"✅ {paper_id}: {file_size:.1f}KB")
            return True
        else:
            print(f"❌ 输出文件异常: {paper_id}")
            return False
            
    except Exception as e:
        print(f"❌ 生成失败 {paper_id}: {e}")
        return False

async def process_papers(source_filter: str, voice: str, output_dir: Path, concurrency: int):
    """批量处理论文"""
    
    # 查询论文
    db = SessionLocal()
    try:
        query = """
        SELECT pi.paper_id, pi.interpretation
        FROM paper_interpretations pi
        JOIN papers p ON pi.paper_id = p.id
        WHERE pi.interpretation IS NOT NULL 
        AND LENGTH(pi.interpretation) > 50
        """
        
        params = {}
        if source_filter:
            query += " AND p.source = :source"
            params['source'] = source_filter
        
        query += " ORDER BY pi.paper_id"
        
        result = db.execute(text(query), params)
        papers = result.fetchall()
        
    finally:
        db.close()
    
    if not papers:
        print("❌ 未找到符合条件的论文")
        return
    
    print(f"📚 找到 {len(papers)} 篇论文")
    
    # 创建输出目录
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # 并发控制
    semaphore = asyncio.Semaphore(concurrency)
    
    async def process_single_paper(paper_id, content):
        async with semaphore:
            output_file = output_dir / f"{paper_id}.opus"
            
            # 跳过已存在的文件
            if output_file.exists():
                print(f"⏭️  跳过已存在: {paper_id}")
                return True
            
            return await generate_single_tts(paper_id, content, voice, output_file)
    
    # 批量处理
    tasks = [process_single_paper(str(paper[0]), paper[1]) for paper in papers]
    
    print(f"🚀 开始批量生成 (并发数: {concurrency})...")
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 统计结果
    success_count = sum(1 for r in results if r is True)
    total_count = len(results)
    
    print(f"\n📊 生成完成!")
    print(f"✅ 成功: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    # 计算总大小
    total_size = sum(f.stat().st_size for f in output_dir.glob("*.opus"))
    print(f"💾 总大小: {total_size/1024/1024:.1f} MB")
    print(f"📁 输出目录: {output_dir}")

async def main():
    parser = argparse.ArgumentParser(description="AI解读TTS生成 - 单文件低码率版本")
    parser.add_argument("--source", help="论文来源过滤 (如: conf/iclr2024)")
    parser.add_argument("--voice", default="zh-CN-XiaoxiaoNeural", help="语音模型")
    parser.add_argument("--output-dir", default="/data/proj/flopap/data/tts_opus", help="输出目录")
    parser.add_argument("--concurrency", type=int, default=6, help="并发数")
    
    args = parser.parse_args()
    
    print("🎵 AI解读TTS生成器 - 单文件低码率版本")
    print(f"📚 论文来源: {args.source or '全部'}")
    print(f"🎤 语音模型: {args.voice}")
    print(f"⚡ 并发数: {args.concurrency}")
    print(f"🎛️  码率设置: 24kbps VBR")
    print(f"📁 输出目录: {args.output_dir}")
    print("-" * 50)
    
    output_dir = Path(args.output_dir)
    
    await process_papers(args.source, args.voice, output_dir, args.concurrency)

if __name__ == "__main__":
    asyncio.run(main())
