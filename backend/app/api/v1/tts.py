"""
TTS音频服务 API v1 - Standalone Edition
提供论文TTS音频文件访问 (Local-only)
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from pathlib import Path
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.services.tts_file_service import tts_service
from app.core.config import settings
from cachetools import TTLCache
import threading

router = APIRouter()

# TTS URL 缓存：5 小时 TTL，最多缓存 10000 个条目
_tts_url_cache = TTLCache(maxsize=10000, ttl=5 * 60 * 60)
_cache_lock = threading.Lock()


def _get_cached_response(paper_id: str):
    """从缓存获取响应"""
    with _cache_lock:
        return _tts_url_cache.get(paper_id)


def _set_cached_response(paper_id: str, response: dict):
    """缓存响应"""
    with _cache_lock:
        _tts_url_cache[paper_id] = response


@router.get("/audio/{paper_id}")
async def get_tts_audio_url(
    paper_id: str,
    db: Session = Depends(get_db)
):
    """
    获取论文TTS音频访问URL (Standalone Edition - Local only)
    
    Args:
        paper_id: 论文ID
        
    Returns:
        包含音频URL和文件信息的响应
    """
    # 1. 检查缓存
    cached = _get_cached_response(paper_id)
    if cached:
        return cached
    
    # 2. 查询数据库获取文件名
    from app.models import PaperTTS
    tts_record = db.query(PaperTTS).filter(PaperTTS.paper_id == paper_id).first()
    
    if tts_record and tts_record.file_path:
        filename = tts_record.file_path
    else:
        # 兼容旧逻辑或降级方案
        # 优先检查是否存在 .mp3, .wav, 然后是 .opus
        for ext in ['.mp3', '.wav', '.opus']:
             if tts_service.file_exists(f"{paper_id}{ext}"):
                 filename = f"{paper_id}{ext}"
                 break
        else:
             filename = f"{paper_id}.opus"
    
    # 3. 检查文件是否存在
    if not tts_service.file_exists(filename):
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Audio file not found",
                "paper_id": paper_id,
                "filename": filename
            }
        )
    
    # 4. 生成访问URL (local only)
    audio_url = tts_service.get_file_url(filename)
    
    # 5. 获取文件大小
    file_size = tts_record.file_size if tts_record else None
    
    if file_size is None:
        try:
            file_path = Path(settings.tts_directory) / filename
            file_size = file_path.stat().st_size
        except:
            pass
    
    # 6. 构建响应
    response = {
        "audio_url": audio_url,
        "paper_id": paper_id,
        "filename": filename,
        "mode": "local",
        "file_size": file_size
    }
    
    # 7. 缓存响应
    _set_cached_response(paper_id, response)
    
    return response

@router.get("/file/{filename}")
async def serve_tts_file(filename: str):
    """
    直接提供TTS音频文件 (Standalone Edition)
    
    Args:
        filename: 音频文件名
        
    Returns:
        音频文件响应
    """
    # 安全检查：允许 .opus, .mp3, .wav
    allowed_exts = {
        '.opus': 'audio/opus',
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav'
    }
    
    ext = Path(filename).suffix.lower()
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    file_path = Path(settings.tts_directory) / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(
        path=str(file_path),
        media_type=allowed_exts[ext],
        filename=filename,
        headers={
            "Cache-Control": "public, max-age=3600",  # 缓存1小时
            "Access-Control-Allow-Origin": "*"
        }
    )

@router.get("/list")
async def list_tts_files(limit: int = 10):
    """
    列出可用的TTS文件（开发测试用）
    
    Args:
        limit: 返回文件数量限制
        
    Returns:
        文件列表信息
    """
    try:
        tts_dir = Path(settings.tts_directory)
        if not tts_dir.exists():
            raise HTTPException(status_code=500, detail="TTS directory not found")
        
        opus_files = list(tts_dir.glob("*.opus"))
        files = []
        
        for file_path in opus_files[:limit]:
            paper_id = file_path.stem
            files.append({
                "paper_id": paper_id,
                "filename": file_path.name,
                "size": file_path.stat().st_size,
                "url": tts_service.get_file_url(file_path.name)
            })
        
        return {
            "files": files,
            "total_count": len(opus_files),
            "showing": len(files),
            "directory": str(tts_dir),
            "mode": "local"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
