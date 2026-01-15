#!/usr/bin/env python3
"""
为指定的16篇NeurIPS论文生成缺失的翻译和AI解读
"""
import sys
import os
import json
from pathlib import Path
from datetime import datetime
import uuid

# 添加backend路径到sys.path
backend_path = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(backend_path))

from sqlalchemy import text
from sqlalchemy.orm import Session
from loguru import logger

from app.db.session import SessionLocal
from app.models import Paper, PaperTranslation, PaperInterpretation
from app.services.content_generation.translation_generate_v2 import generate_translations_for_papers
from app.services.content_generation.ai_interpretation_generate_v2 import generate_interpretations_for_papers

# 需要处理的16篇论文ID
MISSING_PAPERS = [
    'b8b00dbc-cfb6-4e30-9ea4-451b9db7627c',  # 需要翻译
    'd7d30888-50e4-4601-891f-7e83b5402b11',  # 需要翻译
    'd810d631-8432-4ed4-9004-209efdaf42a1',  # 需要AI解读
    'd0d3a0f3-57e0-4092-8a7c-23c549eb854d',  # 需要翻译
    '080bd375-f12c-4281-b8f9-4a25de68ef0c',  # 需要翻译
    '7792523a-deb3-4679-8ec9-bc134f117bb3',  # 需要翻译
    '9ab9992e-bf61-4356-8841-3f666ae868ff',  # 需要翻译
    'cf6ebd5e-3f7e-43ae-8fc8-00ab01899c15',  # 需要AI解读
    '5acda317-f2b2-4e4c-8bc8-f3202ac98f0f',  # 需要翻译
    'da3d1f6a-7777-4b9b-acf1-ac4c801c4f79',  # 需要翻译
    'acdf9d39-aca1-4e74-b927-fd41f314acc5',  # 需要翻译
    '273030d5-a4c7-4066-b4a5-15792544a6a5',  # 需要翻译
    '10a11f07-1840-4a2c-ad66-29991a260f02',  # 需要翻译
    '03406616-29e6-4d93-9eba-f8b5f94f8097',  # 需要翻译
    'c2002268-92a9-4290-a491-635509c743e0',  # 需要翻译
    '2de16e0b-a99a-4b30-bce7-cb297b8aca69',  # 需要翻译
]

def get_papers_needing_translation(session: Session) -> list[Paper]:
    """获取需要翻译的论文"""
    papers_needing_translation = []
    
    for paper_id in MISSING_PAPERS:
        # 检查是否缺少翻译
        translation_query = text("""
            SELECT COUNT(*) FROM paper_translations 
            WHERE paper_id = :paper_id AND title_zh IS NOT NULL
        """)
        has_translation = session.execute(translation_query, {"paper_id": paper_id}).scalar() > 0
        
        if not has_translation:
            paper = session.get(Paper, uuid.UUID(paper_id))
            if paper:
                papers_needing_translation.append(paper)
    
    return papers_needing_translation

def get_papers_needing_interpretation(session: Session) -> list[Paper]:
    """获取需要AI解读的论文"""
    papers_needing_interpretation = []
    
    for paper_id in MISSING_PAPERS:
        # 检查是否缺少AI解读
        interpretation_query = text("""
            SELECT COUNT(*) FROM paper_interpretations 
            WHERE paper_id = :paper_id AND interpretation IS NOT NULL
        """)
        has_interpretation = session.execute(interpretation_query, {"paper_id": paper_id}).scalar() > 0
        
        if not has_interpretation:
            paper = session.get(Paper, uuid.UUID(paper_id))
            if paper:
                papers_needing_interpretation.append(paper)
    
    return papers_needing_interpretation

def main():
    logger.info("🚀 开始为16篇缺失TTS的NeurIPS论文生成内容")
    
    session = SessionLocal()
    
    try:
        # 1. 生成缺失的翻译
        papers_needing_translation = get_papers_needing_translation(session)
        logger.info(f"📝 需要生成翻译的论文: {len(papers_needing_translation)} 篇")
        
        if papers_needing_translation:
            logger.info("开始生成翻译...")
            translation_results = generate_translations_for_papers(
                papers=papers_needing_translation,
                max_workers=10  # 使用10个并发
            )
            
            # 保存翻译结果到数据库
            saved_count = 0
            for paper_id, (title_zh, summary_zh) in translation_results.items():
                try:
                    # 检查是否已存在翻译记录
                    existing = session.query(PaperTranslation).filter_by(paper_id=paper_id).first()
                    if existing:
                        existing.title_zh = title_zh
                        existing.summary_zh = summary_zh
                        existing.model_name = "deepseek-reasoner"
                    else:
                        translation = PaperTranslation(
                            paper_id=paper_id,
                            title_zh=title_zh,
                            summary_zh=summary_zh,
                            model_name="deepseek-reasoner"
                        )
                        session.add(translation)
                    saved_count += 1
                except Exception as e:
                    logger.error(f"保存翻译失败: {paper_id}, {e}")
            
            session.commit()
            logger.info(f"翻译生成完成: 生成 {len(translation_results)} 篇，保存 {saved_count} 篇")
        
        # 2. 生成缺失的AI解读
        papers_needing_interpretation = get_papers_needing_interpretation(session)
        logger.info(f"🤖 需要生成AI解读的论文: {len(papers_needing_interpretation)} 篇")
        
        if papers_needing_interpretation:
            logger.info("开始生成AI解读...")
            interpretation_results = generate_interpretations_for_papers(
                papers=papers_needing_interpretation,
                max_workers=10  # 使用10个并发
            )
            
            # 保存AI解读结果到数据库
            saved_count = 0
            for paper_id, interpretation in interpretation_results.items():
                try:
                    # 检查是否已存在解读记录
                    existing = session.query(PaperInterpretation).filter_by(paper_id=paper_id).first()
                    if existing:
                        existing.interpretation = interpretation
                        existing.model_name = "deepseek-reasoner"
                    else:
                        interp = PaperInterpretation(
                            paper_id=paper_id,
                            interpretation=interpretation,
                            model_name="deepseek-reasoner"
                        )
                        session.add(interp)
                    saved_count += 1
                except Exception as e:
                    logger.error(f"保存AI解读失败: {paper_id}, {e}")
            
            session.commit()
            logger.info(f"AI解读生成完成: 生成 {len(interpretation_results)} 篇，保存 {saved_count} 篇")
        
        # 3. 验证结果
        logger.info("🔍 验证生成结果...")
        complete_papers = 0
        
        for paper_id in MISSING_PAPERS:
            # 检查是否同时有翻译和解读
            check_query = text("""
                SELECT 
                    (SELECT COUNT(*) FROM paper_translations pt WHERE pt.paper_id = :paper_id AND pt.title_zh IS NOT NULL) as has_translation,
                    (SELECT COUNT(*) FROM paper_interpretations pi WHERE pi.paper_id = :paper_id AND pi.interpretation IS NOT NULL) as has_interpretation
            """)
            result = session.execute(check_query, {"paper_id": paper_id}).fetchone()
            
            if result.has_translation > 0 and result.has_interpretation > 0:
                complete_papers += 1
        
        logger.info(f"✅ 完成内容生成的论文: {complete_papers}/{len(MISSING_PAPERS)} 篇")
        
        if complete_papers == len(MISSING_PAPERS):
            logger.info("🎉 所有16篇论文的内容都已完成，现在可以生成TTS了！")
        else:
            logger.warning(f"⚠️  还有 {len(MISSING_PAPERS) - complete_papers} 篇论文需要补充内容")
        
    except Exception as e:
        logger.error(f"❌ 生成过程出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    main()
