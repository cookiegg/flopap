#!/usr/bin/env python3
"""
为NeurIPS 2025论文批量生成翻译和AI解读
- 处理1000篇论文
- 使用50个deepseek并发
"""
import sys
import os
import json
import random
from pathlib import Path
from datetime import datetime

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

# 临时文件目录
TEMP_DIR = Path(__file__).parent / "temp_results"
TEMP_DIR.mkdir(exist_ok=True)

def get_papers_without_content(session: Session, limit: int = 1000) -> list[Paper]:
    """获取没有翻译和AI解读的neurips2025论文"""
    query = text("""
        SELECT p.* FROM papers p
        WHERE p.source = 'conf/neurips2025'
        AND (
            NOT EXISTS (
                SELECT 1 FROM paper_translations pt WHERE pt.paper_id = p.id
            )
            OR NOT EXISTS (
                SELECT 1 FROM paper_interpretations pi WHERE pi.paper_id = p.id
            )
        )
        ORDER BY RANDOM()
        LIMIT :limit
    """)
    
    result = session.execute(query, {"limit": limit})
    paper_rows = result.fetchall()
    
    # 转换为Paper对象并从session中分离
    papers = []
    for row in paper_rows:
        paper = session.get(Paper, row.id)
        if paper:
            # 强制加载所有属性
            _ = paper.id, paper.title, paper.summary, paper.authors, paper.categories, paper.arxiv_id
            # 从session中分离对象，避免多线程访问session
            session.expunge(paper)
            papers.append(paper)
    
    return papers

def filter_papers_for_generation(session: Session, papers: list[Paper]) -> tuple[list[Paper], list[Paper]]:
    """过滤需要生成翻译和AI解读的论文"""
    papers_need_translation = []
    papers_need_interpretation = []
    
    for paper in papers:
        # 检查是否需要翻译
        existing_translation = session.query(PaperTranslation).filter(
            PaperTranslation.paper_id == paper.id
        ).first()
        if not existing_translation:
            papers_need_translation.append(paper)
        
        # 检查是否需要AI解读
        existing_interpretation = session.query(PaperInterpretation).filter(
            PaperInterpretation.paper_id == paper.id
        ).first()
        if not existing_interpretation:
            papers_need_interpretation.append(paper)
    
    return papers_need_translation, papers_need_interpretation

def save_single_result_to_temp(paper: Paper, content_type: str, content: any, batch_id: str):
    """增量保存单个结果到临时文件"""
    temp_file = TEMP_DIR / f"batch_{batch_id}_{content_type}_{paper.id}.json"
    
    result = {
        "batch_id": batch_id,
        "timestamp": datetime.now().isoformat(),
        "paper": {
            "id": str(paper.id),
            "arxiv_id": paper.arxiv_id,
            "title": paper.title
        },
        "content_type": content_type,
        "content": content
    }
    
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    logger.debug(f"增量保存: {content_type} - {paper.arxiv_id}")
    return temp_file

def collect_temp_results(batch_id: str) -> dict:
    """收集所有临时文件的结果"""
    pattern = f"batch_{batch_id}_*.json"
    temp_files = list(TEMP_DIR.glob(pattern))
    
    results = {
        "batch_id": batch_id,
        "timestamp": datetime.now().isoformat(),
        "papers": [],
        "translations": {},
        "interpretations": {}
    }
    
    papers_seen = set()
    
    for temp_file in temp_files:
        try:
            with open(temp_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            paper_id = data["paper"]["id"]
            content_type = data["content_type"]
            
            # 添加论文信息（去重）
            if paper_id not in papers_seen:
                results["papers"].append(data["paper"])
                papers_seen.add(paper_id)
            
            # 添加内容
            if content_type == "translation":
                results["translations"][paper_id] = data["content"]
            elif content_type == "interpretation":
                results["interpretations"][paper_id] = data["content"]
                
        except Exception as e:
            logger.warning(f"读取临时文件失败: {temp_file} - {e}")
    
    logger.info(f"收集到 {len(temp_files)} 个临时文件的结果")
    return results

def cleanup_temp_files(batch_id: str):
    """清理批次的临时文件"""
    pattern = f"batch_{batch_id}_*.json"
    temp_files = list(TEMP_DIR.glob(pattern))
    
    for temp_file in temp_files:
        try:
            temp_file.unlink()
        except Exception as e:
            logger.warning(f"删除临时文件失败: {temp_file} - {e}")
    
    logger.info(f"清理了 {len(temp_files)} 个临时文件")

def load_and_save_to_db(results: dict):
    """从收集的结果保存到数据库"""
    logger.info("开始保存到数据库")
    
    with SessionLocal() as session:
        translation_count = 0
        interpretation_count = 0
        
        # 保存翻译
        for paper_id_str, translation_data in results["translations"].items():
            paper_id = paper_id_str
            
            # 检查是否已存在
            existing = session.query(PaperTranslation).filter(
                PaperTranslation.paper_id == paper_id
            ).first()
            
            if not existing:
                translation = PaperTranslation(
                    paper_id=paper_id,
                    title_zh=translation_data["title_zh"],
                    summary_zh=translation_data["summary_zh"],
                    model_name="deepseek-reasoner"
                )
                session.add(translation)
                translation_count += 1
        
        # 保存AI解读
        for paper_id_str, interpretation_text in results["interpretations"].items():
            paper_id = paper_id_str
            
            # 检查是否已存在
            existing = session.query(PaperInterpretation).filter(
                PaperInterpretation.paper_id == paper_id
            ).first()
            
            if not existing:
                interpretation = PaperInterpretation(
                    paper_id=paper_id,
                    interpretation=interpretation_text,
                    language="zh",
                    model_name="deepseek-reasoner"
                )
                session.add(interpretation)
                interpretation_count += 1
        
        # 提交事务
        session.commit()
        logger.info(f"数据库保存完成: 翻译 {translation_count} 篇，AI解读 {interpretation_count} 篇")
        
        return translation_count, interpretation_count

def main():
    batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.info(f"开始批次 {batch_id} - 为NeurIPS 2025论文生成翻译和AI解读")
    logger.info("配置: 1000篇论文，50个deepseek并发")
    
    with SessionLocal() as session:
        # 获取候选论文 - 增加到1500篇候选，确保有足够的论文
        candidate_papers = get_papers_without_content(session, limit=1500)
        
        if not candidate_papers:
            logger.info("没有找到需要处理的论文")
            return
        
        # 过滤出真正需要生成内容的论文
        papers_need_translation, papers_need_interpretation = filter_papers_for_generation(session, candidate_papers)
        
        # 限制为1000篇进行大批量处理
        papers_need_translation = papers_need_translation[:1000]
        papers_need_interpretation = papers_need_interpretation[:1000]
        
        logger.info(f"需要翻译的论文: {len(papers_need_translation)} 篇")
        logger.info(f"需要AI解读的论文: {len(papers_need_interpretation)} 篇")
        
        if not papers_need_translation and not papers_need_interpretation:
            logger.info("所有论文都已有翻译和AI解读")
            return
        
        # 显示将要处理的论文统计
        all_papers = list(set(papers_need_translation + papers_need_interpretation))
        logger.info(f"本批次将处理 {len(all_papers)} 篇论文")
    
    # 阶段1：生成内容（与数据库分离）
    logger.info("=== 阶段1：批量生成和缓存内容 (50个deepseek并发) ===")
    
    # 生成翻译
    if papers_need_translation:
        logger.info(f"开始生成翻译... ({len(papers_need_translation)} 篇)")
        try:
            translations = generate_translations_for_papers(papers_need_translation, max_workers=50)
            # 增量缓存翻译结果
            for paper in papers_need_translation:
                if paper.id in translations:
                    title_zh, summary_zh = translations[paper.id]
                    content = {"title_zh": title_zh, "summary_zh": summary_zh}
                    save_single_result_to_temp(paper, "translation", content, batch_id)
            logger.info(f"翻译生成和缓存完成: {len(translations)} 篇")
        except Exception as e:
            logger.error(f"翻译生成失败: {e}")
    else:
        logger.info("跳过翻译生成 - 无需处理的论文")
    
    # 生成AI解读
    if papers_need_interpretation:
        logger.info(f"开始生成AI解读... ({len(papers_need_interpretation)} 篇)")
        try:
            interpretations = generate_interpretations_for_papers(papers_need_interpretation, max_workers=50)
            # 增量缓存AI解读结果
            for paper in papers_need_interpretation:
                if paper.id in interpretations:
                    save_single_result_to_temp(paper, "interpretation", interpretations[paper.id], batch_id)
            logger.info(f"AI解读生成和缓存完成: {len(interpretations)} 篇")
        except Exception as e:
            logger.error(f"AI解读生成失败: {e}")
    else:
        logger.info("跳过AI解读生成 - 无需处理的论文")
    
    # 阶段2：收集所有缓存结果
    logger.info("=== 阶段2：收集缓存结果 ===")
    results = collect_temp_results(batch_id)
    
    if not results["translations"] and not results["interpretations"]:
        logger.info("没有生成任何新内容")
        return
    
    # 阶段3：批量保存到数据库
    logger.info("=== 阶段3：批量保存到数据库 ===")
    try:
        translation_count, interpretation_count = load_and_save_to_db(results)
        logger.info(f"批次 {batch_id} 处理完成")
        logger.info(f"成功保存: 翻译 {translation_count} 篇，AI解读 {interpretation_count} 篇")
        
        # 清理临时文件
        cleanup_temp_files(batch_id)
        
    except Exception as e:
        logger.error(f"数据库保存失败: {e}")
        logger.info(f"临时文件已保留，批次ID: {batch_id}")

if __name__ == "__main__":
    main()
