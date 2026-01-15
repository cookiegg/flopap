#!/usr/bin/env python3
"""
重新生成失败的CS候选池TTS文件
"""
import asyncio
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

# 失败的论文ID列表
FAILED_PAPER_IDS = [
    "8837cd1c-108a-48aa-ace5-08abbb6d94e3",
    "6dc30c80-10e6-412d-8223-534abf4204d0", 
    "01751577-2e5a-4617-8e0a-571d12cb9d37",
    "6000ffe7-9e53-4e97-bdaf-60e332d7f274",
    "8e246396-9d6f-4132-95a2-a2a6812fa2c7",
    "d911f9e0-f9bf-438d-9867-889c3e1c79f9",
    "55967b25-0e66-4244-b95f-76ebe6db0b46",
    "b1f3ec3e-fc3a-4e9f-a2d1-687761b4873f",
    "5f107a30-629c-4896-816b-3eaead9c25bf"
]

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
        await asyncio.sleep(random.uniform(0.2, 0.5))
        
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
        return False

async def process_failed_papers():
    """处理失败的论文"""
    output_dir = Path('/data/proj/flopap/data/tts_opus')
    voice = "zh-CN-XiaoxiaoNeural"
    
    db = SessionLocal()
    
    try:
        # 获取失败论文的内容
        papers_content = []
        for paper_id_str in FAILED_PAPER_IDS:
            paper_id = UUID(paper_id_str)
            
            # 检查文件是否已存在
            output_path = output_dir / f"{paper_id}.opus"
            if output_path.exists():
                print(f"⏭️  跳过已存在: {paper_id}")
                continue
            
            # 获取论文内容
            translation = db.execute(
                text("SELECT title_zh, summary_zh FROM paper_translations WHERE paper_id = :paper_id"),
                {"paper_id": paper_id}
            ).fetchone()
            
            interpretation = db.execute(
                text("SELECT interpretation FROM paper_interpretations WHERE paper_id = :paper_id"),
                {"paper_id": paper_id}
            ).fetchone()
            
            if translation and interpretation:
                content = f"{translation[0]}\n\n{translation[1]}\n\n{interpretation[0]}"
                papers_content.append((paper_id, content))
        
        print(f'📝 需要重新生成: {len(papers_content)} 篇')
        
        if not papers_content:
            print('✅ 所有文件都已存在')
            return
        
        # 并发生成TTS
        semaphore = asyncio.Semaphore(9)  # 9个并发
        
        async def process_single(paper_data):
            async with semaphore:
                paper_id, content = paper_data
                output_path = output_dir / f"{paper_id}.opus"
                success = await generate_single_tts(str(paper_id), content, voice, output_path)
                return paper_id, success
        
        tasks = [process_single(paper_data) for paper_data in papers_content]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 保存数据库记录
        success_count = 0
        for paper_id, success in results:
            if success and isinstance(paper_id, UUID):
                output_path = output_dir / f"{paper_id}.opus"
                if output_path.exists():
                    file_size = output_path.stat().st_size
                    
                    existing = db.query(PaperTTS).filter(PaperTTS.paper_id == paper_id).first()
                    if not existing:
                        tts_record = PaperTTS(
                            paper_id=paper_id,
                            file_path=str(output_path),
                            file_size=file_size,
                            voice_model="zh-CN-XiaoxiaoNeural",
                            generated_at=datetime.utcnow()
                        )
                        db.add(tts_record)
                        success_count += 1
        
        db.commit()
        
        print(f'\n📊 重新生成完成: 成功 {success_count}/{len(papers_content)}')
        
    except Exception as e:
        print(f'❌ 执行失败: {e}')
    finally:
        db.close()

async def main():
    print('🔄 重新生成失败的CS候选池TTS文件')
    await process_failed_papers()

if __name__ == "__main__":
    asyncio.run(main())
