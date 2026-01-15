#!/usr/bin/env python3
"""
arXiv基础内容生成测试脚本

完整流程：CS候选池 → 翻译 → AI解读 → TTS语音
"""
import os
import sys
import subprocess
from pathlib import Path
from uuid import UUID

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
from app.services.tts_storage import tts_storage


def main():
    print("=== arXiv基础内容生成测试 ===")
    
    # 1. 生成CS候选池
    print("\n🔄 步骤1: 生成CS候选池...")
    target_date = (pendulum.today() - pendulum.duration(days=3)).date()
    print(f"目标日期: {target_date}")
    
    try:
        result = subprocess.run([
            sys.executable, 
            "scripts/arxiv_candidate_pool/generate_cs_pool.py",
            "--days-ago", "3"
        ], cwd=backend_root, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ CS候选池生成失败: {result.stderr}")
            return
        
        print("✅ CS候选池生成完成")
    except Exception as e:
        print(f"❌ CS候选池生成异常: {e}")
        return
    
    # 2. 获取候选池中的论文
    print("\n🔄 步骤2: 获取候选池论文...")
    db = SessionLocal()
    
    try:
        paper_ids = CandidatePoolServiceV2.get_candidate_papers_by_date(
            session=db,
            target_date=target_date,
            filter_type='cs'
        )
        
        if not paper_ids:
            print("❌ 未找到CS候选池论文")
            return
        
        # 取前5篇进行测试
        test_paper_ids = paper_ids[:5]
        print(f"✅ 获取到 {len(paper_ids)} 篇CS论文，选择前5篇测试")
        print(f"测试论文ID: {[str(pid)[:8] + '...' for pid in test_paper_ids]}")
        
        # 3. 生成翻译
        print("\n🔄 步骤3: 生成翻译...")
        translation_count = translate_and_save_papers(
            session=db,
            paper_ids=test_paper_ids,
            max_workers=3,
            force_retranslate=False
        )
        print(f"✅ 翻译完成: {translation_count} 篇")
        
        # 4. 生成AI解读
        print("\n🔄 步骤4: 生成AI解读...")
        interpretation_results = batch_generate_interpretations(
            session=db,
            paper_ids=test_paper_ids,
            max_workers=3,
            force_regenerate=False
        )
        print(f"✅ AI解读完成: {len(interpretation_results)} 篇")
        
        # 5. 生成TTS语音
        print("\n🔄 步骤5: 生成TTS语音...")
        tts_results = batch_generate_tts(
            session=db,
            paper_ids=test_paper_ids,
            voice="zh-CN-XiaoxiaoNeural",
            max_workers=3
        )
        print(f"✅ TTS生成完成: {len(tts_results)} 篇")
        
        # 6. 保存TTS到存储系统
        print("\n🔄 步骤6: 保存TTS文件...")
        saved_count = 0
        for paper_id, audio_bytes in tts_results.items():
            # 获取论文内容用于存储
            from app.services.content_generation.tts_generate import get_papers_with_content, clean_markdown_for_tts
            papers_data = get_papers_with_content(db, [paper_id])
            
            if papers_data:
                paper_data = papers_data[0]
                _, title_en, title_zh, interpretation = paper_data
                content = f"论文标题：{title_zh}\n英文标题：{title_en}\nAI解读：{clean_markdown_for_tts(interpretation)}"
                
                tts_record = tts_storage.save_tts_file(
                    session=db,
                    paper_id=paper_id,
                    audio_bytes=audio_bytes,
                    voice_model="zh-CN-XiaoxiaoNeural",
                    content=content
                )
                
                if tts_record:
                    saved_count += 1
                    file_path = tts_storage.base_dir / tts_record.file_path
                    print(f"  ✓ {paper_id}: {file_path}")
        
        print(f"✅ TTS文件保存完成: {saved_count} 个文件")
        
        # 7. 生成测试报告
        print("\n📊 测试报告:")
        print(f"目标日期: {target_date}")
        print(f"CS候选池论文数: {len(paper_ids)}")
        print(f"测试论文数: {len(test_paper_ids)}")
        print(f"翻译成功: {translation_count} 篇")
        print(f"AI解读成功: {len(interpretation_results)} 篇")
        print(f"TTS生成成功: {len(tts_results)} 篇")
        print(f"TTS文件保存: {saved_count} 个")
        
        success_rate = (saved_count / len(test_paper_ids)) * 100
        print(f"整体成功率: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("\n🎉 所有步骤完成！内容生成流水线测试成功！")
        else:
            print(f"\n⚠️  部分步骤失败，成功率: {success_rate:.1f}%")
        
    except Exception as e:
        print(f"❌ 测试过程异常: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
