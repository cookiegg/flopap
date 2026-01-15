"""
TTS 服务类 - 统一的语音生成入口

使用方法:
    from app.services.content_generation.tts_service import tts_service
    
    # 使用默认配置
    result = tts_service.generate_batch(session, paper_ids)
    
    # 自定义配置
    custom_service = TTSService(max_workers=10, voice="zh-CN-YunxiNeural")
    result = custom_service.generate_batch(session, paper_ids)
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from loguru import logger
from sqlalchemy.orm import Session

from app.services.content_generation.tts_generate import (
    generate_single_tts_async,
    get_papers_with_content,
    clean_markdown_for_tts,
)


@dataclass
class TTSConfig:
    """TTS 生成配置"""
    max_workers: int = 5
    voice: str = "zh-CN-XiaoxiaoNeural"
    request_delay_min: float = 0.5
    request_delay_max: float = 1.0
    timeout_seconds: float = 60.0


class TTSService:
    """
    TTS 语音生成服务
    
    统一管理 TTS 生成的并发、存储、日志等逻辑。
    """
    
    def __init__(self, config: Optional[TTSConfig] = None):
        self.config = config or TTSConfig()
    
    def generate_batch(
        self,
        session: Session,
        paper_ids: List[UUID],
        save_to_storage: bool = True
    ) -> Dict[UUID, str]:
        """
        批量生成 TTS 语音
        
        Args:
            session: 数据库会话
            paper_ids: 论文 ID 列表
            save_to_storage: 是否保存到存储系统
            
        Returns:
            Dict[UUID, str]: {paper_id: file_path} 映射
        """
        from app.services.content_generation.tts_storage import tts_storage
        
        # 1. 过滤已存在的文件
        existing_files = {}
        papers_to_generate = []
        
        for paper_id in paper_ids:
            if save_to_storage:
                existing_path = tts_storage.get_tts_file_path(
                    session, paper_id, self.config.voice
                )
                if existing_path:
                    existing_files[paper_id] = str(existing_path)
                    continue
            papers_to_generate.append(paper_id)
        
        if not papers_to_generate:
            logger.info("所有 TTS 文件都已存在")
            return existing_files
        
        logger.info(
            f"[TTSService] 开始生成 {len(papers_to_generate)} 个 TTS 文件 "
            f"(并发数: {self.config.max_workers})"
        )
        
        # 2. 准备数据
        papers_data_list = get_papers_with_content(session, papers_to_generate)
        paper_data_map = {
            row[0]: (row[1], row[2], row[3]) for row in papers_data_list
        }
        
        paper_content_map = {
            pid: f"论文标题：{zh}\n英文标题：{en}\nAI解读：{clean_markdown_for_tts(interpretation)}"
            for pid, (en, zh, interpretation) in paper_data_map.items()
        }
        
        # 3. 异步执行
        new_saved_files = asyncio.run(
            self._run_batch_async(
                papers_to_generate,
                paper_data_map,
                paper_content_map,
                save_to_storage
            )
        )
        
        existing_files.update(new_saved_files)
        return existing_files
    
    async def _run_batch_async(
        self,
        paper_ids: List[UUID],
        paper_data_map: Dict[UUID, Tuple[str, str, str]],
        paper_content_map: Dict[UUID, str],
        save_to_storage: bool
    ) -> Dict[UUID, str]:
        """异步批量处理"""
        semaphore = asyncio.Semaphore(self.config.max_workers)
        saved_files_local: Dict[UUID, str] = {}
        tasks = []
        
        for pid in paper_ids:
            if pid not in paper_data_map:
                continue
            
            task = self._process_single_task(
                semaphore,
                pid,
                paper_data_map[pid],
                paper_content_map,
                saved_files_local,
                save_to_storage
            )
            tasks.append(task)
        
        if not tasks:
            return {}
        
        await asyncio.gather(*tasks, return_exceptions=True)
        return saved_files_local
    
    async def _process_single_task(
        self,
        semaphore: asyncio.Semaphore,
        paper_id: UUID,
        paper_data: Tuple[str, str, str],
        paper_content_map: Dict[UUID, str],
        saved_files_local: Dict[UUID, str],
        save_to_storage: bool
    ) -> Tuple[UUID, Optional[bytes]]:
        """处理单个 TTS 任务"""
        title_en, title_zh, interpretation = paper_data
        
        async with semaphore:
            logger.debug(f"[TTSService] Starting: {paper_id}")
            start_time = time.time()
            
            try:
                # 1. 生成音频
                audio_bytes = await generate_single_tts_async(
                    (title_en, title_zh, interpretation),
                    self.config.voice
                )
                duration = time.time() - start_time
                
                if not audio_bytes:
                    logger.warning(f"[TTSService] Failed (No audio): {paper_id}")
                    return paper_id, None
                
                logger.debug(f"[TTSService] Generated: {paper_id} in {duration:.2f}s")
                
                # 2. 保存
                if save_to_storage:
                    content = paper_content_map.get(paper_id, "")
                    loop = asyncio.get_running_loop()
                    
                    saved_file_path = await loop.run_in_executor(
                        None,
                        self._save_in_thread,
                        paper_id, audio_bytes, content
                    )
                    
                    if saved_file_path:
                        from app.services.content_generation.tts_storage import tts_storage
                        full_path = tts_storage.base_dir / saved_file_path
                        saved_files_local[paper_id] = str(full_path)
                        logger.info(f"[TTSService] Saved: {paper_id}")
                
                return paper_id, audio_bytes
            
            except Exception as e:
                logger.error(f"[TTSService] Exception {paper_id}: {e}")
                return paper_id, None
    
    def _save_in_thread(
        self,
        paper_id: UUID,
        audio_bytes: bytes,
        content: str
    ) -> Optional[str]:
        """在独立线程中保存 TTS 文件"""
        from app.db.session import SessionLocal
        from app.services.content_generation.tts_storage import tts_storage
        
        try:
            with SessionLocal() as thread_session:
                record = tts_storage.save_tts_file(
                    thread_session, paper_id, audio_bytes, self.config.voice, content
                )
                if record:
                    return str(record.file_path)
        except Exception as e:
            logger.error(f"[TTSService] 线程保存异常 {paper_id}: {e}")
        return None


# 默认服务实例，供外部直接使用
tts_service = TTSService()
