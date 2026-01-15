#!/usr/bin/env python3
"""
CS候选池TTS生成 - 支持分片并发处理
基于production脚本架构，支持offset/limit参数
"""
import asyncio
import argparse
import sys
import random
import uuid
import subprocess
import re
from pathlib import Path
from uuid import UUID
from datetime import datetime

backend_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_root))

import edge_tts
import pendulum
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import SessionLocal
from app.services.data_ingestion.arxiv_candidate_pool import CandidatePoolServiceV2
from app.models.paper_tts import PaperTTS

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

from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    reraise=True
)
async def generate_single_tts(paper_id: str, content: str, voice: str, output_path: Path):
    """生成单个TTS文件 (带重试机制)"""
    try:
        await asyncio.sleep(random.uniform(0.1, 0.3))
        
        clean_content = clean_markdown_for_tts(content)
        
        if len(clean_content) < 10:
            print(f"❌ 内容过短: {paper_id}")
            return False
        
        communicate = edge_tts.Communicate(clean_content, voice)
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
        print(f"❌ TTS生成失败 {paper_id}: {e}")
        raise  # Re-raise for tenacity to catch and retry

async def process_batch(papers, voice, output_dir, concurrency):
    """处理一批论文"""
    semaphore = asyncio.Semaphore(concurrency)
    
    async def process_single(paper):
        async with semaphore:
            paper_id, title_en, title_zh, interpretation = paper
            
            output_path = output_dir / f"{paper_id}.opus"
            if output_path.exists() and output_path.stat().st_size > 1000:
                print(f"⏭️  跳过已存在: {paper_id}")
                return paper_id, True
            
            full_content = f"论文标题：{title_zh}\n英文标题：{title_en}\nAI解读：{interpretation}"
            success = await generate_single_tts(str(paper_id), full_content, voice, output_path)
            return paper_id, success
    
    tasks = [process_single(paper) for paper in papers]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return results

def get_cs_papers_batch(db, offset, limit, target_date):
    """获取CS候选池论文的指定范围"""
    # 获取CS候选池所有论文ID
    paper_ids = CandidatePoolServiceV2.get_candidate_papers_by_date(
        session=db,
        target_date=target_date,
        filter_type='cs'
    )
    
    # 分片处理
    batch_ids = paper_ids[offset:offset + limit]
    
    if not batch_ids:
        return []
    
    # 获取论文内容
    papers = []
    for paper_id in batch_ids:
        paper = db.execute(
            text("SELECT title FROM papers WHERE id = :paper_id"),
            {"paper_id": paper_id}
        ).fetchone()
        
        translation = db.execute(
            text("SELECT title_zh FROM paper_translations WHERE paper_id = :paper_id"),
            {"paper_id": paper_id}
        ).fetchone()
        
        interpretation = db.execute(
            text("SELECT interpretation FROM paper_interpretations WHERE paper_id = :paper_id"),
            {"paper_id": paper_id}
        ).fetchone()
        
        if paper and translation and interpretation:
            papers.append((paper_id, paper[0], translation[0], interpretation[0]))
    
    return papers

def save_tts_records(db, results, output_dir):
    """保存TTS记录到数据库"""
    for paper_id, success in results:
        if success and isinstance(paper_id, UUID):
            output_path = output_dir / f"{paper_id}.opus"
            if output_path.exists():
                file_size = output_path.stat().st_size
                
                existing = db.query(PaperTTS).filter(PaperTTS.paper_id == paper_id).first()
                if not existing:
                    tts_record = PaperTTS(
                        paper_id=paper_id,
                        file_path=f"{paper_id}.opus",
                        file_size=file_size,
                        voice_model="zh-CN-XiaoxiaoNeural",
                        generated_at=datetime.utcnow()
                    )
                    db.add(tts_record)
    
    db.commit()

async def main():
    parser = argparse.ArgumentParser(description="CS候选池TTS生成")
    parser.add_argument("--days-ago", type=int, help="处理N天前的数据")
    parser.add_argument("--date", type=str, help="指定日期 YYYY-MM-DD")
    parser.add_argument("--offset", type=int, default=0, help="起始偏移量")
    parser.add_argument("--limit", type=int, default=50, help="处理数量")
    parser.add_argument("--concurrency", type=int, default=6, help="并发数")
    parser.add_argument("--voice", default="zh-CN-XiaoxiaoNeural", help="语音模型")
    parser.add_argument("--output-dir", default="/data/proj/flopap/data/tts_opus", help="输出目录")
    args = parser.parse_args()
    
    # 确定目标日期
    if args.date:
        target_date = pendulum.parse(args.date).date()
    elif args.days_ago is not None:
        target_date = (pendulum.today() - pendulum.duration(days=args.days_ago)).date()
    else:
        # 默认逻辑: 如果没传，可以根据当前业务习惯默认 T-3
        target_date = (pendulum.today() - pendulum.duration(days=3)).date()

    print(f'🚀 CS候选池TTS生成 - 日期:{target_date} 偏移:{args.offset} 数量:{args.limit} 并发:{args.concurrency}')
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    db = SessionLocal()
    
    try:
        # 获取论文批次
        papers = get_cs_papers_batch(db, args.offset, args.limit, target_date)
        print(f'📝 获取论文: {len(papers)} 篇')
        
        if not papers:
            print('❌ 无论文需要处理')
            return
        
        # 并发生成TTS
        results = await process_batch(papers, args.voice, output_dir, args.concurrency)
        
        # 保存数据库记录
        save_tts_records(db, results, output_dir)
        
        # 统计结果
        success_count = sum(1 for _, success in results if success)
        print(f'\n📊 批次完成: 成功 {success_count}/{len(papers)}')
        
    except Exception as e:
        print(f'❌ 执行失败: {e}')
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
