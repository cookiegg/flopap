#!/usr/bin/env python3
"""
每日全量内容生成脚本

对指定日期的所有CS候选论文进行：
1. 翻译
2. AI解读
3. TTS生成
"""
import argparse
import os
import sys
from pathlib import Path

# 禁用代理 (复用之前的成功经验)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('all_proxy', None)
os.environ.pop('ALL_PROXY', None)

# 添加backend根目录到路径
backend_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_root))

import pendulum
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.data_ingestion.arxiv_candidate_pool import CandidatePoolServiceV2
from app.services.content_generation.translation_generate import translate_and_save_papers
from app.services.content_generation.ai_interpretation_generate import batch_generate_interpretations
from app.services.content_generation.tts_generate import batch_generate_tts
from app.services.content_generation.tts_storage import tts_storage

def generate_content_for_date(target_date, limit=None, do_trans=True, do_ai=True, do_tts=True):
    """
    为指定日期生成内容 (可被外部调用)
    """
    print(f"执行计划: 翻译[{'✅' if do_trans else '❌'}] AI解读[{'✅' if do_ai else '❌'}] TTS[{'✅' if do_tts else '❌'}]")
    print(f"目标日期: {target_date}")
    
    db = SessionLocal()
    
    try:
        # 1. 获取CS候选池论文
        print("\n📋 步骤1: 获取CS候选池...")
        paper_ids = CandidatePoolServiceV2.get_candidate_papers_by_date(
            session=db,
            target_date=target_date,
            filter_type='cs'
        )
        
        if not paper_ids:
            print("❌ 未找到CS候选池，请先运行候选池生成脚本")
            return
            
        print(f"✅ 找到 {len(paper_ids)} 篇候选论文")
        
        if limit:
            paper_ids = paper_ids[:limit]
            print(f"⚠️ 限制处理前 {limit} 篇")

        # 2. 批量生成翻译
        if do_trans:
            print(f"\n🌐 步骤2: 生成翻译 (共 {len(paper_ids)} 篇)...")
            translation_count = translate_and_save_papers(
                session=db,
                paper_ids=paper_ids,
                max_workers=50,
                force_retranslate=False
            )
            print(f"✅ 翻译完成: {translation_count}/{len(paper_ids)}")
        else:
            print("\n⏭️ 跳过翻译步骤")
        
        # 3. 批量生成AI解读
        if do_ai:
            print(f"\n🤖 步骤3: 生成AI解读 (共 {len(paper_ids)} 篇)...")
            interpretation_results = batch_generate_interpretations(
                session=db,
                paper_ids=paper_ids,
                max_workers=50,
                force_regenerate=False
            )
            print(f"✅ AI解读完成: {len(interpretation_results)}/{len(paper_ids)}")
        else:
            print("\n⏭️ 跳过AI解读步骤")
        
        # 4. 批量生成TTS
        if do_tts:
            print(f"\n🔊 步骤4: 生成TTS语音 (共 {len(paper_ids)} 篇)...")
            from app.services.content_generation.tts_service import tts_service
            tts_results = tts_service.generate_batch(
                session=db,
                paper_ids=paper_ids,
                save_to_storage=True
            )
            print(f"✅ TTS生成并保存完成: {len(tts_results)}/{len(paper_ids)}")
        else:
            print("\n⏭️ 跳过TTS步骤")
        
        print("\n🎉 === 全量生成完成 ===")
        
    except Exception as e:
        print(f"❌ 执行异常: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def main():
    parser = argparse.ArgumentParser(description="每日全量内容生成")
    parser.add_argument("--days-ago", type=int, default=3, help="处理N天前的数据")
    parser.add_argument("--date", type=str, help="指定日期 YYYY-MM-DD")
    parser.add_argument("--limit", type=int, help="限制处理数量(用于测试)")
    parser.add_argument("--steps", type=str, default="all", help="执行步骤: all, trans, ai, tts")
    args = parser.parse_args()

    print("=== 每日全量内容生成 ===")
    
    steps = args.steps.split(',')
    do_trans = "all" in steps or "trans" in steps
    do_ai = "all" in steps or "ai" in steps
    do_tts = "all" in steps or "tts" in steps
    
    # 确定目标日期
    if args.date:
        target_date = pendulum.parse(args.date).date()
    else:
        target_date = (pendulum.today() - pendulum.duration(days=args.days_ago)).date()
    
    generate_content_for_date(target_date, args.limit, do_trans, do_ai, do_tts)

if __name__ == "__main__":
    main()
