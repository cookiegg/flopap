#!/usr/bin/env python3
"""
修复版内容生成脚本

解决TTS生成中的查询问题
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
from sqlalchemy import text
from app.db.session import SessionLocal
from app.services.data_ingestion.arxiv_candidate_pool import CandidatePoolServiceV2
from app.services.content_generation.translation_generate import translate_and_save_papers
from app.services.content_generation.ai_interpretation_generate import batch_generate_interpretations
from app.services.content_generation.tts_generate import clean_markdown_for_tts
import asyncio
import edge_tts


async def generate_single_tts_async(content: str, voice: str = "zh-CN-XiaoxiaoNeural") -> bytes:
    """异步生成单篇TTS"""
    communicate = edge_tts.Communicate(content, voice)
    audio_bytes = b""
    
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_bytes += chunk["data"]
    
    return audio_bytes


def main():
    print("=== 修复版内容生成测试 ===")
    
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
            print("❌ 未找到CS候选池")
            return
        
        test_paper_ids = paper_ids[:5]
        print(f"✅ 选择5篇论文测试")
        
        # 2. 生成翻译
        print("\n🌐 生成翻译...")
        translation_count = translate_and_save_papers(
            session=db,
            paper_ids=test_paper_ids,
            max_workers=2,
            force_retranslate=False
        )
        print(f"✅ 翻译: {translation_count}/5 篇")
        
        # 3. 生成AI解读
        print("\n🤖 生成AI解读...")
        interpretation_results = batch_generate_interpretations(
            session=db,
            paper_ids=test_paper_ids,
            max_workers=2,
            force_regenerate=False
        )
        print(f"✅ AI解读: {len(interpretation_results)}/5 篇")
        
        # 4. 手动查询论文数据并生成TTS
        print("\n🔊 生成TTS语音...")
        
        # 直接查询数据库获取完整数据
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
            AND pt.title_zh IS NOT NULL
            AND pi.interpretation IS NOT NULL
        """)
        
        result = db.execute(query, {"paper_ids": test_paper_ids})
        papers_data = result.fetchall()
        
        print(f"找到完整数据的论文: {len(papers_data)}/5")
        
        if not papers_data:
            print("❌ 未找到包含翻译和解读的论文数据")
            return
        
        # 异步生成TTS
        async def generate_all_tts():
            tts_results = {}
            for paper_data in papers_data:
                paper_id, title_en, title_zh, interpretation = paper_data
                
                # 组合内容
                clean_interpretation = clean_markdown_for_tts(interpretation)
                content = f"""
论文标题：{title_zh}

英文标题：{title_en}

AI解读：{clean_interpretation}
                """.strip()
                
                print(f"  正在生成: {title_zh[:30]}...")
                
                try:
                    audio_bytes = await generate_single_tts_async(content)
                    tts_results[paper_id] = audio_bytes
                    print(f"  ✓ 完成: {len(audio_bytes)} 字节")
                except Exception as e:
                    print(f"  ✗ 失败: {e}")
            
            return tts_results
        
        # 运行异步TTS生成
        tts_results = asyncio.run(generate_all_tts())
        
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
        
        complete_count = len([p for p in papers_data if p[0] in tts_results])
        print(f"完整流程成功: {complete_count}/5")
        
        if complete_count == 5:
            print("\n🎉 完美！所有5篇论文的内容生成流程全部成功！")
        elif complete_count > 0:
            print(f"\n✅ 部分成功！{complete_count}篇论文完成了完整流程")
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
