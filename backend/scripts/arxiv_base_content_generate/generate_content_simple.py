#!/usr/bin/env python3
"""
简化版内容生成脚本

直接使用现有的CS候选池，生成5篇论文的完整内容
"""
import os
import sys
from pathlib import Path

# 禁用代理
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


def main():
    print("=== 简化版内容生成测试 ===")
    
    # 使用现有的CS候选池
    target_date = (pendulum.today() - pendulum.duration(days=3)).date()
    print(f"使用日期: {target_date}")
    
    db = SessionLocal()
    
    try:
        # 1. 获取CS候选池论文
        print("\n📋 获取CS候选池论文...")
        paper_ids = CandidatePoolServiceV2.get_candidate_papers_by_date(
            session=db,
            target_date=target_date,
            filter_type='cs'
        )
        
        if not paper_ids:
            print("❌ 未找到CS候选池，请先运行候选池生成脚本")
            return
        
        # 选择5篇论文
        test_paper_ids = paper_ids[:5]
        print(f"✅ 找到 {len(paper_ids)} 篇CS论文，选择5篇测试")
        
        # 2. 批量生成翻译
        print("\n🌐 生成翻译...")
        translation_count = translate_and_save_papers(
            session=db,
            paper_ids=test_paper_ids,
            max_workers=2,
            force_retranslate=False
        )
        print(f"✅ 翻译: {translation_count}/5 篇")
        
        # 3. 批量生成AI解读
        print("\n🤖 生成AI解读...")
        interpretation_results = batch_generate_interpretations(
            session=db,
            paper_ids=test_paper_ids,
            max_workers=2,
            force_regenerate=False
        )
        print(f"✅ AI解读: {len(interpretation_results)}/5 篇")
        
        # 4. 批量生成TTS
        print("\n🔊 生成TTS语音...")
        tts_results = batch_generate_tts(
            session=db,
            paper_ids=test_paper_ids,
            voice="zh-CN-XiaoxiaoNeural",
            max_workers=2
        )
        print(f"✅ TTS: {len(tts_results)}/5 篇")
        
        # 5. 保存TTS文件
        print("\n💾 保存TTS文件...")
        output_dir = Path("data/tts")
        output_dir.mkdir(exist_ok=True, parents=True)
        
        saved_count = 0
        for paper_id, audio_bytes in tts_results.items():
            output_file = output_dir / f"{paper_id}.wav"
            output_file.write_bytes(audio_bytes)
            print(f"  ✓ {output_file.name} ({len(audio_bytes)} 字节)")
            saved_count += 1
        
        # 6. 测试总结
        print(f"\n📊 测试结果:")
        print(f"翻译成功: {translation_count}/5")
        print(f"AI解读成功: {len(interpretation_results)}/5")
        print(f"TTS生成成功: {len(tts_results)}/5")
        print(f"文件保存成功: {saved_count}/5")
        
        total_success = min(translation_count, len(interpretation_results), len(tts_results), saved_count)
        print(f"完整流程成功: {total_success}/5")
        
        if total_success == 5:
            print("\n🎉 完美！所有5篇论文的内容生成流程全部成功！")
        elif total_success > 0:
            print(f"\n✅ 部分成功！{total_success}篇论文完成了完整流程")
        else:
            print("\n❌ 流程失败，请检查服务配置")
        
    except Exception as e:
        print(f"❌ 执行异常: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
