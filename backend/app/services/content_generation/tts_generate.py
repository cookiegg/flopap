"""
TTS语音生成服务 - 为论文生成语音文件

主要函数：
- generate_single_tts(paper_data: Tuple, voice: str) -> Optional[bytes]
  输入：论文数据元组，语音模型
  输出：语音文件字节数据或None
  功能：为单篇论文生成TTS语音

- batch_generate_tts(session: Session, paper_ids: List[UUID], max_workers: int = 5) -> Dict[UUID, bytes]
  输入：数据库会话，论文ID列表，最大并发数
  输出：{paper_id: audio_bytes}字典
  功能：批量生成论文TTS语音

- clean_markdown_for_tts(text: str) -> str
  输入：包含markdown的文本
  输出：清理后的纯文本
  功能：清理markdown语法，使其适合TTS
"""
from __future__ import annotations
import time

import asyncio
import re
import json
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from loguru import logger
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

try:
    import edge_tts
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    logger.warning("edge-tts未安装，TTS功能不可用")

from app.models import Paper, PaperTranslation, PaperInterpretation


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


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((Exception,)),
    reraise=True
)
async def generate_single_tts_async(
    paper_data: Tuple[str, str, str], 
    voice: str = "zh-CN-XiaoxiaoNeural"
) -> Optional[bytes]:
    """异步生成单篇论文的TTS语音 (带重试机制)"""
    if not TTS_AVAILABLE:
        logger.error("edge-tts未安装，无法生成TTS")
        return None
    
    try:
        # 添加显著的随机延迟(1-3秒)，避免速率限制 (Serial Mode)
        await asyncio.sleep(random.uniform(0.5, 1.0))
        
        title_en, title_zh, interpretation = paper_data
        
        # 清理markdown语法
        clean_interpretation = clean_markdown_for_tts(interpretation)
        
        # 组合文本内容
        content = f"""
论文标题：{title_zh}

英文标题：{title_en}

AI解读：{clean_interpretation}
        """.strip()
        
        # 生成语音 (EdgeTTS default is usually mp3)
        communicate = edge_tts.Communicate(content, voice)
        
        async def _fetch_audio():
            audio = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio += chunk["data"]
            return audio

        # 设置60秒超时
        audio_bytes = await asyncio.wait_for(_fetch_audio(), timeout=60.0)
        
        # 尝试转换为 Opus 格式 (使用 ffmpeg)
        try:
            import subprocess
            import tempfile
            import os
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_mp3:
                tmp_mp3.write(audio_bytes)
                tmp_mp3_path = tmp_mp3.name
                
            tmp_opus_path = tmp_mp3_path.replace(".mp3", ".opus")
            
            # 调用 ffmpeg 转换
            # -y: yes to overwrite
            # -i: input
            # -c:a libopus: codec
            # -b:a 48k: bitrate
            cmd = [
                "ffmpeg", "-y", "-i", tmp_mp3_path, 
                "-c:a", "libopus", "-b:a", "48k", 
                tmp_opus_path
            ]
            
            # 使用 asyncio.create_subprocess_exec (但这里为了简单先用 subprocess.run，因为是在线程池里跑或者本身就是 async)
            # generate_single_tts_async 是 async 的，subprocess.run 是阻塞的。
            # 应该用 asyncio.create_subprocess_exec 或 run_in_executor
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                with open(tmp_opus_path, "rb") as f:
                    opus_bytes = f.read()
                
                # 清理
                os.unlink(tmp_mp3_path)
                os.unlink(tmp_opus_path)
                
                logger.debug(f"已将音频转换为Opus格式 ({len(audio_bytes)} -> {len(opus_bytes)} bytes)")
                return opus_bytes
            else:
                logger.warning(f"FFmpeg转换失败，回退到原始格式: {stderr.decode()}")
                os.unlink(tmp_mp3_path)
                if os.path.exists(tmp_opus_path):
                    os.unlink(tmp_opus_path)
                return audio_bytes
                
        except Exception as e:
            logger.warning(f"音频转换异常: {str(e)}，使用原始音频")
            return audio_bytes
        
    except Exception as e:
        logger.warning(f"TTS生成尝试失败: {str(e)}")
        raise e


def generate_single_tts(
    paper_data: Tuple[str, str, str], 
    voice: str = "zh-CN-XiaoxiaoNeural"
) -> Optional[bytes]:
    """生成单篇论文的TTS语音（同步接口）"""
    return asyncio.run(generate_single_tts_async(paper_data, voice))


def get_papers_with_content(session: Session, paper_ids: List[UUID]) -> List[Tuple[UUID, str, str, str]]:
    """获取包含翻译和解读的论文数据"""
    query = text("""
        SELECT 
            p.id,
            p.title,
            COALESCE(pt.title_zh, p.title) as title_zh,
            pi.interpretation
        FROM papers p
        LEFT JOIN paper_translations pt ON p.id = pt.paper_id
        LEFT JOIN paper_interpretations pi ON p.id = pi.paper_id
        WHERE p.id = ANY(:paper_ids)
        AND pi.interpretation IS NOT NULL
    """)
    
    result = session.execute(query, {"paper_ids": paper_ids})
    return [(row[0], row[1], row[2], row[3]) for row in result.fetchall()]


async def batch_generate_tts_async(
    session: Session,
    paper_ids: List[UUID],
    voice: str = "zh-CN-XiaoxiaoNeural",
    max_workers: int = 5
) -> Dict[UUID, bytes]:
    """批量异步生成TTS语音"""
    if not TTS_AVAILABLE:
        logger.error("edge-tts未安装，无法生成TTS")
        return {}
    
    if not paper_ids:
        logger.info("没有需要生成TTS的论文")
        return {}
    
    logger.info("开始批量生成TTS {} 篇论文", len(paper_ids))
    
    # 获取论文数据
    papers_data = get_papers_with_content(session, paper_ids)
    
    if not papers_data:
        logger.warning("未找到包含解读的论文")
        return {}
    
    logger.info("找到 {} 篇可生成TTS的论文", len(papers_data))
    
    # 并发生成TTS
    tasks = []
    paper_id_map = {}
    
    for paper_id, title_en, title_zh, interpretation in papers_data:
        task = generate_single_tts_async((title_en, title_zh, interpretation), voice)
        tasks.append(task)
        paper_id_map[len(tasks) - 1] = paper_id
    
    # 限制并发数
    semaphore = asyncio.Semaphore(max_workers)
    
    async def limited_task(task, index):
        async with semaphore:
            result = await task
            return index, result
    
    limited_tasks = [limited_task(task, i) for i, task in enumerate(tasks)]
    
    # 使用 return_exceptions=True 允许部分成功
    results_raw = await asyncio.gather(*limited_tasks, return_exceptions=True)
    
    # 收集结果
    tts_results = {}
    success_count = 0
    
    for result_item in results_raw:
        if isinstance(result_item, Exception):
            logger.error(f"TTS根据任务失败: {result_item}")
            continue
            
        index, audio_bytes = result_item
        paper_id = paper_id_map[index]
        if audio_bytes:
            tts_results[paper_id] = audio_bytes
            success_count += 1
            logger.debug("TTS生成成功: paper_id={}", paper_id)
        else:
            logger.warning("TTS生成失败: paper_id={}", paper_id)
    
    logger.info("TTS生成完成: 成功 {} 篇，失败 {} 篇", 
                success_count, len(papers_data) - success_count)
    
    return tts_results


def batch_generate_tts(
    session: Session,
    paper_ids: List[UUID],
    voice: str = "zh-CN-XiaoxiaoNeural",
    max_workers: int = 5
) -> Dict[UUID, bytes]:
    """
    [DEPRECATED] 批量生成TTS语音（同步接口）
    
    请使用 TTSService.generate_batch() 代替:
        from app.services.content_generation.tts_service import tts_service
        tts_service.generate_batch(session, paper_ids)
    """
    import warnings
    warnings.warn(
        "batch_generate_tts 已废弃，请使用 tts_service.generate_batch()",
        DeprecationWarning,
        stacklevel=2
    )
    return asyncio.run(batch_generate_tts_async(session, paper_ids, voice, max_workers))


# ... (imports remain same)

async def _save_record_in_thread(paper_id: UUID, audio_bytes: bytes, voice: str, content: str) -> Optional[str]:
    """
    在独立线程中保存TTS文件，避免阻塞异步事件循环。
    必须在线程内创建新的数据库会话。
    """
    from app.db.session import SessionLocal
    from app.services.content_generation.tts_storage import tts_storage

    try:
        with SessionLocal() as thread_session:
            record = tts_storage.save_tts_file(
                thread_session, paper_id, audio_bytes, voice, content
            )
            # 返回文件路径字符串，而非ORM对象
            if record:
                return str(record.file_path)
    except Exception as e:
        logger.error(f"线程内保存TTS失败 {paper_id}: {e}")
    return None


async def _process_single_task(
    semaphore: asyncio.Semaphore,
    paper_id: UUID, 
    paper_data: Tuple[str, str, str], 
    voice: str,
    save_to_storage: bool,
    paper_content_map: Dict[UUID, str],
    saved_files_local: Dict[UUID, str]
) -> Tuple[UUID, Optional[bytes]]:
    """
    处理单个TTS任务：生成 -> (可选)保存
    包含并发控制和性能追踪日志。
    """
    title_en, title_zh, interpretation = paper_data
    
    async with semaphore:
        logger.debug(f"[TTS-Task] Starting: {paper_id}")
        start_time = time.time()
        
        try:
            # 1. 生成音频
            audio_bytes = await generate_single_tts_async((title_en, title_zh, interpretation), voice)
            duration = time.time() - start_time
            
            if not audio_bytes:
                logger.warning(f"[TTS-Task] Failed (No audio): {paper_id}")
                return paper_id, None

            logger.debug(f"[TTS-Task] Generated: {paper_id} in {duration:.2f}s")
            
            # 2. 保存 (如果需要)
            if save_to_storage:
                content = paper_content_map.get(paper_id, "")
                loop = asyncio.get_running_loop()
                
                # 使用 run_in_executor 执行阻塞的 I/O 操作
                saved_file_path = await loop.run_in_executor(
                    None, 
                    lambda: asyncio.run(asyncio.sleep(0)) or _save_record_in_thread_sync(paper_id, audio_bytes, voice, content)
                )
                # 注意：上面lambda写法是为了能在executor里调普通函数，下面定义同步wrapper
                
                saved_file_path = await loop.run_in_executor(
                    None,
                    _save_record_in_thread_wrapper,  # 需要定义这个wrapper
                    paper_id, audio_bytes, voice, content
                )

                if saved_file_path:
                    from app.services.content_generation.tts_storage import tts_storage
                    full_path = tts_storage.base_dir / saved_file_path
                    saved_files_local[paper_id] = str(full_path)
                    logger.info(f"TTS保存成功: {paper_id}")
                    
            return paper_id, audio_bytes

        except Exception as e:
            logger.error(f"[TTS-Task] Exception {paper_id}: {e}")
            return paper_id, None

# 辅助同步函数，用于 run_in_executor
def _save_record_in_thread_wrapper(paper_id: UUID, audio_bytes: bytes, voice: str, content: str) -> Optional[str]:
    from app.db.session import SessionLocal
    from app.services.content_generation.tts_storage import tts_storage
    try:
        with SessionLocal() as thread_session:
            record = tts_storage.save_tts_file(
                thread_session, paper_id, audio_bytes, voice, content
            )
            if record:
                return str(record.file_path)
    except Exception as e:
        logger.error(f"线程保存异常 {paper_id}: {e}")
    return None


def batch_generate_tts_with_storage(
    session: Session,
    paper_ids: List[UUID],
    voice: str = "zh-CN-XiaoxiaoNeural",
    max_workers: int = 5,
    save_to_storage: bool = True
) -> Dict[UUID, str]:
    """
    批量生成TTS并保存到存储系统 (优化版)
    - 并发控制
    - 非阻塞I/O
    - 实时保存
    """
    from app.services.content_generation.tts_storage import tts_storage
    
    # 1. 过滤已存在
    existing_files = {}
    papers_to_generate = []
    
    for paper_id in paper_ids:
        if save_to_storage:
            existing_path = tts_storage.get_tts_file_path(session, paper_id, voice)
            if existing_path:
                existing_files[paper_id] = str(existing_path)
                continue
        papers_to_generate.append(paper_id)
    
    if not papers_to_generate:
        logger.info("所有TTS文件都已存在")
        return existing_files
        
    logger.info(f"需要生成 {len(papers_to_generate)} 个新TTS文件 (并发数: {max_workers})")
    
    # 2. 准备数据
    papers_data_list = get_papers_with_content(session, papers_to_generate)
    # 将 list 转为 dict 以便 ID 查找，或者直接 zip
    # 但原逻辑是 iterate list，这里我们构建一个 map 方便
    paper_data_map = {row[0]: (row[1], row[2], row[3]) for row in papers_data_list}
    
    paper_content_map = {
        pid: f"论文标题：{zh}\n英文标题：{en}\nAI解读：{clean_markdown_for_tts(interpretation)}"
        for pid, (en, zh, interpretation) in paper_data_map.items()
    }

    # 3. 异步执行主体
    async def _run_batch():
        semaphore = asyncio.Semaphore(max_workers)
        saved_files_local = {}
        tasks = []
        
        for pid in papers_to_generate:
            if pid not in paper_data_map:
                continue
            
            task = _process_single_task(
                semaphore, 
                pid, 
                paper_data_map[pid], 
                voice, 
                save_to_storage, 
                paper_content_map, 
                saved_files_local
            )
            tasks.append(task)
            
        if not tasks:
            return {}
            
        await asyncio.gather(*tasks, return_exceptions=True)
        return saved_files_local

    # 4. 运行
    new_saved_files = asyncio.run(_run_batch())
    
    existing_files.update(new_saved_files)
    return existing_files

# ... (keep get_random_papers_for_tts)
