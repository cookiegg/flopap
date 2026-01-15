#!/usr/bin/env python3
"""
补全脚本：转换残留WAV文件为OPUS，并生成缺失的片段
"""

import asyncio
import subprocess
import sys
from pathlib import Path
from uuid import UUID

backend_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_root))

from sqlalchemy import text
from app.db.session import SessionLocal


def convert_wav_to_opus(wav_path: Path) -> bool:
    """将WAV文件转换为OPUS"""
    try:
        opus_path = wav_path.with_suffix('.opus')
        
        cmd = [
            "ffmpeg", "-i", str(wav_path),
            "-c:a", "libopus", "-ar", "24000", "-b:a", "20k",
            "-application", "voip", "-y", str(opus_path)
        ]
        
        subprocess.run(cmd, capture_output=True, check=True)
        
        # 删除WAV文件
        wav_path.unlink()
        return True
        
    except Exception as e:
        print(f"❌ 转换失败 {wav_path}: {e}")
        return False


def check_paper_completeness(paper_dir: Path) -> dict:
    """检查论文目录的完整性"""
    result = {
        'wav_files': [],
        'opus_files': [],
        'missing_segments': []
    }
    
    # 检查6个片段
    for i in range(6):
        segment_base = f"segment_{i:02d}_part_{i+1}"
        wav_file = paper_dir / f"{segment_base}.wav"
        opus_file = paper_dir / f"{segment_base}.opus"
        
        if wav_file.exists():
            result['wav_files'].append(wav_file)
        elif opus_file.exists():
            result['opus_files'].append(opus_file)
        else:
            result['missing_segments'].append(i)
    
    return result


async def main():
    print("🔧 开始补全TTS文件")
    
    tts_dir = Path("backend/data/tts")
    if not tts_dir.exists():
        print("❌ TTS目录不存在")
        return
    
    # 统计信息
    total_papers = 0
    converted_wavs = 0
    missing_segments = 0
    complete_papers = 0
    
    # 遍历所有论文目录
    for paper_dir in tts_dir.iterdir():
        if not paper_dir.is_dir() or not paper_dir.name.count('-') == 4:
            continue
        
        total_papers += 1
        completeness = check_paper_completeness(paper_dir)
        
        # 转换WAV文件
        for wav_file in completeness['wav_files']:
            if convert_wav_to_opus(wav_file):
                converted_wavs += 1
                print(f"✅ 转换: {wav_file.name}")
        
        # 统计缺失片段
        missing_count = len(completeness['missing_segments'])
        missing_segments += missing_count
        
        # 检查是否完整
        total_segments = len(completeness['opus_files']) + len(completeness['wav_files'])
        if total_segments == 6:
            complete_papers += 1
        
        if total_papers % 100 == 0:
            print(f"📊 进度: {total_papers} 篇论文处理完成")
    
    print(f"\n🎉 补全完成！")
    print(f"📊 统计:")
    print(f"  总论文数: {total_papers}")
    print(f"  转换WAV: {converted_wavs}")
    print(f"  缺失片段: {missing_segments}")
    print(f"  完整论文: {complete_papers}")
    print(f"  完整率: {complete_papers/total_papers*100:.1f}%")


if __name__ == "__main__":
    asyncio.run(main())
