"""
TTS存储服务 - 管理音频文件的存储和元数据
"""
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.paper_tts import PaperTTS


from app.core.config import settings

class TTSStorageManager:
    """TTS存储管理器"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or settings.tts_directory)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_filename(self) -> str:
        """生成UUID文件名（与现有文件保持一致）"""
        return f"{uuid4()}.opus"
    
    def _calculate_content_hash(self, content: str) -> str:
        """计算内容哈希"""
        return hashlib.md5(content.encode()).hexdigest()
    
    def save_tts_file(
        self, 
        session: Session,
        paper_id: UUID, 
        audio_bytes: bytes, 
        voice_model: str,
        content: str
    ) -> Optional[PaperTTS]:
        """保存TTS文件和元数据"""
        try:
            # 检查是否已存在相同内容的TTS
            content_hash = self._calculate_content_hash(content)
            existing = session.scalar(
                select(PaperTTS).where(
                    PaperTTS.paper_id == paper_id,
                    PaperTTS.voice_model == voice_model,
                    PaperTTS.content_hash == content_hash
                )
            )
            
            if existing:
                full_path = self.base_dir / existing.file_path
                if full_path.exists():
                    logger.info(f"TTS文件已存在: {existing.file_path}")
                    return existing
                else:
                    # 文件不存在，删除数据库记录
                    session.delete(existing)
                    session.commit()
            
            # 生成新文件名
            filename = self._generate_filename()
            file_path = self.base_dir / filename
            
            # 保存音频文件
            file_path.write_bytes(audio_bytes)
            
            # 保存元数据到数据库（使用文件名作为相对路径）
            tts_record = PaperTTS(
                paper_id=paper_id,
                file_path=filename,  # 直接使用文件名
                file_size=len(audio_bytes),
                voice_model=voice_model,
                content_hash=content_hash
            )
            
            session.add(tts_record)
            session.commit()
            
            logger.success(f"TTS文件保存成功: {filename} ({len(audio_bytes)} bytes)")
            return tts_record
            
        except Exception as e:
            session.rollback()
            logger.error(f"保存TTS文件失败: {e}")
            return None
    
    def get_tts_file_path(self, session: Session, paper_id: UUID, voice_model: str) -> Optional[Path]:
        """获取TTS文件路径"""
        try:
            record = session.scalar(
                select(PaperTTS).where(
                    PaperTTS.paper_id == paper_id,
                    PaperTTS.voice_model == voice_model
                )
            )
            
            if record:
                full_path = self.base_dir / record.file_path
                if full_path.exists():
                    return full_path
                else:
                    # 文件不存在，删除数据库记录
                    logger.warning(f"TTS文件不存在，删除记录: {record.file_path}")
                    session.delete(record)
                    session.commit()
            
            return None
            
        except Exception as e:
            logger.error(f"获取TTS文件路径失败: {e}")
            return None
    
    def cleanup_orphaned_files(self, session: Session) -> int:
        """清理孤儿文件（文件存在但数据库无记录）"""
        try:
            # 获取所有数据库记录的文件名
            records = session.execute(select(PaperTTS.file_path)).scalars().all()
            db_files = set(records)
            
            # 获取所有实际文件
            actual_files = set()
            for file_path in self.base_dir.glob("*.wav"):
                actual_files.add(file_path.name)
            
            # 找出孤儿文件
            orphaned_files = actual_files - db_files
            
            cleaned_count = 0
            for filename in orphaned_files:
                file_path = self.base_dir / filename
                try:
                    file_path.unlink()
                    cleaned_count += 1
                    logger.info(f"删除孤儿文件: {filename}")
                except Exception as e:
                    logger.error(f"删除文件失败 {filename}: {e}")
            
            logger.info(f"清理了 {cleaned_count} 个孤儿文件")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"清理孤儿文件失败: {e}")
            return 0
    
    def cleanup_orphaned_records(self, session: Session) -> int:
        """清理孤儿记录（数据库有记录但文件不存在）"""
        try:
            records = session.execute(select(PaperTTS)).scalars().all()
            
            cleaned_count = 0
            for record in records:
                file_path = self.base_dir / record.file_path
                if not file_path.exists():
                    session.delete(record)
                    cleaned_count += 1
                    logger.info(f"删除孤儿记录: {record.file_path}")
            
            session.commit()
            logger.info(f"清理了 {cleaned_count} 个孤儿记录")
            return cleaned_count
            
        except Exception as e:
            session.rollback()
            logger.error(f"清理孤儿记录失败: {e}")
            return 0
    
    def cleanup_old_files(self, session: Session, days: int = 30):
        """清理旧文件"""
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        old_records = session.scalars(
            select(PaperTTS).where(PaperTTS.generated_at < cutoff_date)
        ).all()
        
        cleaned_count = 0
        for record in old_records:
            file_path = self.base_dir / record.file_path
            if file_path.exists():
                file_path.unlink()
                cleaned_count += 1
            session.delete(record)
        
        session.commit()
        logger.info(f"清理了 {cleaned_count} 个旧TTS文件")
        return cleaned_count


# 全局实例
tts_storage = TTSStorageManager()
