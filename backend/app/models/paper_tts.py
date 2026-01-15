"""
TTS音频数据模型
"""
from __future__ import annotations

import uuid
import os
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class PaperTTS(TimestampMixin, Base):
    """
    论文TTS音频记录
    
    存储论文AI解读的TTS音频文件元数据。
    音频文件存储在文件系统中，数据库只保存元数据。
    支持多种中文语音模型，默认使用XiaoxiaoNeural。
    """
    __tablename__ = "paper_tts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 文件信息
    file_path: Mapped[str] = mapped_column(String(512), nullable=False, comment="音频文件相对路径，基于backend/data/tts/")
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, comment="文件大小（字节）")
    
    # 生成参数
    voice_model: Mapped[str] = mapped_column(String(64), nullable=False, default="zh-CN-XiaoxiaoNeural", comment="使用的语音模型")
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="内容哈希，用于去重和缓存")
    
    # 状态信息
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, comment="音频生成时间")
    
    # 关联关系
    paper: Mapped["Paper"] = relationship("Paper", backref="tts_files")

    def get_full_path(self, base_dir: str = "backend/data/tts") -> str:
        """
        获取音频文件的完整路径
        
        Args:
            base_dir: TTS文件存储的基础目录
            
        Returns:
            音频文件的完整路径
        """
        return os.path.join(base_dir, self.file_path)
    
    def file_exists(self, base_dir: str = "backend/data/tts") -> bool:
        """
        检查音频文件是否存在
        
        Args:
            base_dir: TTS文件存储的基础目录
            
        Returns:
            文件是否存在
        """
        full_path = self.get_full_path(base_dir)
        return os.path.exists(full_path)
    
    @property
    def file_size_mb(self) -> float:
        """获取文件大小（MB）"""
        return self.file_size / (1024 * 1024)

    __table_args__ = (
        {
            "comment": "存储论文TTS音频文件的元数据，音频文件存储在文件系统中",
        },
    )
