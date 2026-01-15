#!/usr/bin/env python3
"""
Arxiv Content Factory Script (每日刷新)

功能:
1. 确认/生成 T-3 的 CS 候选池 (Candidate Pool)
2. 触发该候选池的内容生成:
   - 翻译 (DeepSeek API)
   - AI解读 (DeepSeek API)
   - TTS语音 (Edge-TTS + FFmpeg -> Opus)
3. 上传 TTS 音频到 COS 对象存储

注意:
- 本脚本不包含任何"用户个性化推荐"逻辑。
- 仅负责生产内容静态资源。
- 用户推荐由云端服务 (Cloud Service) 负责。

运行时间: 每日凌晨 (T-3 论文获取后)
"""
import sys
import asyncio
import subprocess
from pathlib import Path
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(backend_root))

from datetime import date, timedelta
from loguru import logger

from app.db.session import SessionLocal
from app.core.config import settings
from app.services.data_ingestion.arxiv_candidate_pool import CandidatePoolServiceV2, cs_filter


def get_target_date() -> date:
    """计算目标日期 (T-3)"""
    return date.today() - timedelta(days=settings.arxiv_submission_delay_days)


def run_script(script_path: str, args: list, description: str) -> bool:
    """运行子脚本并捕获输出"""
    logger.info(f"🚀 执行: {description}")
    try:
        cmd = [sys.executable, script_path] + args
        result = subprocess.run(
            cmd,
            cwd=str(backend_root),
            capture_output=True,
            text=True,
            timeout=3600  # 1小时超时
        )
        if result.returncode == 0:
            logger.success(f"✅ {description} 完成")
            if result.stdout:
                # 只显示最后几行
                lines = result.stdout.strip().split('\n')
                for line in lines[-5:]:
                    logger.info(f"   {line}")
            return True
        else:
            logger.error(f"❌ {description} 失败 (exit code: {result.returncode})")
            if result.stderr:
                logger.error(result.stderr[-500:])
            return False
    except subprocess.TimeoutExpired:
        logger.error(f"❌ {description} 超时")
        return False
    except Exception as e:
        logger.exception(f"❌ {description} 异常: {e}")
        return False


def step_1_ensure_candidate_pool(target_date: date) -> bool:
    """步骤1: 确认/创建 CS 候选池"""
    logger.info("=== Step 1: 确认 CS 候选池 ===")
    
    db = SessionLocal()
    try:
        cs_paper_ids = CandidatePoolServiceV2.get_candidate_papers_by_date(
            session=db,
            target_date=target_date,
            filter_type='cs'
        )
        
        if not cs_paper_ids:
            logger.info("候选池不存在，正在创建...")
            cs_paper_ids = CandidatePoolServiceV2.create_filtered_pool_by_date(
                session=db,
                target_date=target_date,
                filter_type='cs',
                filter_func=cs_filter
            )
            db.commit()
            logger.success(f"✅ CS 候选池创建成功: {len(cs_paper_ids)} 篇论文")
        else:
            logger.info(f"✅ CS 候选池已存在: {len(cs_paper_ids)} 篇论文")
        
        if not cs_paper_ids:
            logger.warning("⚠️ 候选池为空")
            return False
        return True
        
    except Exception as e:
        logger.exception(f"❌ 候选池处理失败: {e}")
        return False
    finally:
        db.close()


def step_2_generate_translation_interpretation(target_date: date) -> bool:
    """步骤2: 生成翻译和AI解读"""
    logger.info("=== Step 2: 生成翻译和AI解读 ===")
    
    script_path = str(backend_root / "scripts" / "arxiv_base_content_generate" / "generate_daily_content_full.py")
    date_str = target_date.strftime("%Y-%m-%d")
    
    # 只运行翻译和解读步骤，跳过TTS (我们用独立的opus脚本)
    return run_script(
        script_path,
        ["--date", date_str, "--steps", "trans,ai"],
        f"Translation & Interpretation for {date_str}"
    )


def step_3_generate_tts_opus(target_date: date) -> bool:
    """步骤3: 生成 TTS 音频 (Opus格式)"""
    logger.info("=== Step 3: 生成 TTS 音频 (Opus) ===")
    
    script_path = str(backend_root / "scripts" / "tts" / "generate_cs_tts_parallel.py")
    date_str = target_date.strftime("%Y-%m-%d")
    
    return run_script(
        script_path,
        ["--date", date_str, "--concurrency", "6"],
        f"TTS Opus Generation for {date_str}"
    )


def step_4_upload_to_cos(target_date: date) -> bool:
    """步骤4: 上传音频到 COS 对象存储"""
    logger.info("=== Step 4: 上传 TTS 到 COS ===")
    
    script_path = str(backend_root / "scripts" / "cos" / "upload_paper_audio.py")
    date_str = target_date.strftime("%Y-%m-%d")
    
    return run_script(
        script_path,
        ["--date", date_str, "--workers", "20"],
        f"COS Upload for {date_str}"
    )


def main():
    logger.add("logs/daily_arxiv_factory.log", rotation="1 day", retention="7 days")
    
    logger.info("========================================")
    logger.info("🏭 Arxiv Content Factory 每日刷新")
    logger.info(f"📅 执行日期: {date.today()}")
    logger.info("========================================")
    
    target_date = get_target_date()
    logger.info(f"🎯 目标论文日期: {target_date}")
    
    # Step 1: 确认候选池
    if not step_1_ensure_candidate_pool(target_date):
        logger.error("流程终止: 候选池创建失败")
        return
    
    # Step 2: 翻译 + 解读
    if not step_2_generate_translation_interpretation(target_date):
        logger.warning("翻译/解读可能有部分失败，继续执行TTS...")
    
    # Step 3: TTS 生成 (Opus)
    if not step_3_generate_tts_opus(target_date):
        logger.warning("TTS可能有部分失败，继续执行COS上传...")
    
    # Step 4: COS 上传
    if not step_4_upload_to_cos(target_date):
        logger.warning("COS上传可能有部分失败")
    
    logger.info("========================================")
    logger.info("🏁 Factory 任务结束")
    logger.info("========================================")


if __name__ == "__main__":
    main()
