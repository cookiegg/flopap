import httpx
import pendulum
import argparse
from loguru import logger
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.db.session import SessionLocal
from app.models.paper import Paper, UserProfile, UserFeedback
from app.models.user_paper_ranking import UserPaperRanking
from app.models.paper_tts import PaperTTS
from app.models.paper import PaperEmbedding
from app.models.candidate_pool import CandidatePool
from app.core.config import settings

def date_to_uuid(target_date: pendulum.Date) -> uuid.UUID:
    """将日期转换为确定性的UUID"""
    date_str = target_date.isoformat()
    return uuid.uuid5(uuid.NAMESPACE_DNS, f"candidate_pool_date_{date_str}")

def pull_cloud_user_data(local_db: Session, cloud_url: str, headers: dict):
    """从云端拉取最新的用户画像和反馈，同步到本地数据库"""
    logger.info("正在从云端拉取用户数据...")
    try:
        response = httpx.get(f"{cloud_url}/export/users", headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # 1. 同步用户画像
        for p_data in data["profiles"]:
            profile = local_db.scalar(select(UserProfile).where(UserProfile.user_id == p_data["user_id"]))
            if not profile:
                profile = UserProfile(user_id=p_data["user_id"])
                local_db.add(profile)
            
            profile.interested_categories = p_data["interested_categories"]
            profile.research_keywords = p_data["research_keywords"]
            profile.preference_description = p_data["preference_description"]
            profile.onboarding_completed = p_data["onboarding_completed"]
        
        # 2. 同步用户反馈
        for f_data in data["feedback"]:
            paper = local_db.scalar(select(Paper).where(Paper.arxiv_id == f_data["arxiv_id"]))
            if not paper:
                continue
                
            feedback = local_db.scalar(
                select(UserFeedback).where(
                    and_(
                        UserFeedback.user_id == f_data["user_id"],
                        UserFeedback.paper_id == paper.id
                    )
                )
            )
            if not feedback:
                feedback = UserFeedback(
                    user_id=f_data["user_id"],
                    paper_id=paper.id,
                    feedback_type=f_data["feedback_type"]
                )
                local_db.add(feedback)
        
        local_db.commit()
        logger.success(f"已同步 {len(data['profiles'])} 个用户画像和 {len(data['feedback'])} 条反馈")
    except Exception as e:
        logger.error(f"拉取云端数据失败: {e}")

def push_local_processing_results(
    local_db: Session, 
    cloud_url: str, 
    headers: dict, 
    target_date: Optional[pendulum.Date] = None, 
    source_key: Optional[str] = None,
    batch_size: int = 50,
    limit: Optional[int] = None
):
    """将本地生成的论文、翻译、解读、推荐排序, TTS, Embedding 推送到云端"""
    if target_date:
        logger.info(f"正在准备推送日期 {target_date} 的处理结果 (Batch Size: {batch_size})...")
        batch_id = date_to_uuid(target_date)
        stmt = select(CandidatePool.paper_id).where(
            CandidatePool.batch_id == batch_id,
            CandidatePool.filter_type == 'cs'
        )
        paper_ids = list(local_db.execute(stmt).scalars().all())
    elif source_key:
        logger.info(f"正在准备推送 Source: {source_key} 的处理结果 (Batch Size: {batch_size})...")
        stmt = select(Paper.id).where(Paper.source.like(f"%{source_key}%"))
        if limit:
            stmt = stmt.limit(limit)
        paper_ids = list(local_db.execute(stmt).scalars().all())
    else:
        logger.error("必须提供 target_date 或 source_key")
        return

    if not paper_ids:
        logger.warning("未找到匹配的论文，请先确认本地数据")
        return

    logger.info(f"匹配到 {len(paper_ids)} 篇论文，开始分批推送...")
    
    from sqlalchemy.orm import selectinload
    
    # 分批处理
    for i in range(0, len(paper_ids), batch_size):
        chunk_ids = paper_ids[i:i + batch_size]
        # 使用 selectinload 预加载所有关系，避免 lazy load 失败
        stmt = select(Paper).where(Paper.id.in_(chunk_ids)).options(
            selectinload(Paper.translation),
            selectinload(Paper.interpretation),
            selectinload(Paper.embeddings),
            selectinload(Paper.tts_files)
        )
        papers = local_db.scalars(stmt).all()
        
        payload = {
            "papers": [],
            "translations": [],
            "interpretations": [],
            "tts_records": [],
            "rankings": [],
            "embeddings": []
        }
        
        for p in papers:
            # 基础数据
            payload["papers"].append({
                "arxiv_id": p.arxiv_id,
                "title": p.title,
                "summary": p.summary,
                "authors": p.authors,
                "categories": p.categories,
                "submitted_date": str(p.submitted_date.date()),
                "primary_category": p.primary_category,
                "source": p.source
            })
            
            # 翻译
            if p.translation:
                payload["translations"].append({
                    "arxiv_id": p.arxiv_id,
                    "title_zh": p.translation.title_zh,
                    "summary_zh": p.translation.summary_zh,
                    "model_name": p.translation.model_name
                })
                
            # 解读
            if p.interpretation:
                payload["interpretations"].append({
                    "arxiv_id": p.arxiv_id,
                    "interpretation": p.interpretation.interpretation,
                    "model_name": p.interpretation.model_name
                })
            
            # TTS
            if p.tts_files:
                for tts in p.tts_files:
                    payload["tts_records"].append({
                        "arxiv_id": p.arxiv_id,
                        "file_path": tts.file_path,
                        "file_size": tts.file_size,
                        "voice_model": tts.voice_model,
                        "content_hash": tts.content_hash
                    })

            # Embeddings
            if p.embeddings:
                for emb in p.embeddings:
                    vector = list(emb.vector) if hasattr(emb.vector, '__iter__') else emb.vector
                    payload["embeddings"].append({
                        "arxiv_id": p.arxiv_id,
                        "model_name": emb.model_name,
                        "vector": vector
                    })
        
        # Rankings 同步
        if i == 0:
            if target_date:
                # 尝试通过日期 OR source_key 匹配 (因为T-3逻辑, pool_date可能是今天, 但source包含target_date)
                date_str = target_date.strftime('%Y%m%d')
                today_str = pendulum.now().strftime('%Y%m%d')
                rank_stmt = select(UserPaperRanking).where(
                    or_(
                        UserPaperRanking.pool_date == target_date,
                        UserPaperRanking.source_key.like(f"%{date_str}%"),
                        UserPaperRanking.source_key.like(f"%{today_str}%")
                    )
                )
            else:
                # 模糊匹配 source_key
                rank_stmt = select(UserPaperRanking).where(UserPaperRanking.source_key.like(f"%{source_key}%"))
            
            rankings = local_db.scalars(rank_stmt).all()
            for r in rankings:
                paper_ids_str = []
                # 优化：批量获取 paper 以减少查询
                if r.paper_ids:
                    papers_mapping = {p.id: p.arxiv_id for p in local_db.scalars(select(Paper).where(Paper.id.in_(r.paper_ids))).all()}
                    for pid in r.paper_ids:
                        if pid in papers_mapping:
                            paper_ids_str.append(papers_mapping[pid])
                
                payload["rankings"].append({
                    "user_id": str(r.user_id),
                    "pool_date": str(r.pool_date) if r.pool_date else None,
                    "source_key": r.source_key,
                    "paper_ids": paper_ids_str,
                    "scores": r.scores
                })

        try:
            logger.info(f"正在推送批次 {i//batch_size + 1}...")
            response = httpx.post(f"{cloud_url}/ingest/batch", json=payload, headers=headers, timeout=120.0)
            response.raise_for_status()
            res_json = response.json()
            logger.success(f"推送批次 {i//batch_size + 1} 成功: papers={res_json.get('papers')}, translations={res_json.get('translations')}, interpretations={res_json.get('interpretations')}, tts={res_json.get('tts')}, rankings={res_json.get('rankings')}")
        except Exception as e:
            logger.error(f"推送批次 {i//batch_size + 1} 失败: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"错误详情: {e.response.text}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Master-Worker 同步守护程序")
    parser.add_argument("--date", type=str, help="指定同步日期 (YYYY-MM-DD)")
    parser.add_argument("--source", type=str, help="指定数据源同步 (例如 neurips2025)")
    parser.add_argument("--url", type=str, default="http://localhost:8000/api/v1/internal", help="云端 API 地址")
    parser.add_argument("--batch-size", type=int, default=50, help="每批推送的论文数量")
    parser.add_argument("--limit", type=int, help="限制总论文数量（用于测试）")
    args = parser.parse_args()

    cloud_url = args.url
    headers = {"X-Internal-Token": settings.internal_ingest_token}

    with SessionLocal() as db:
        # 1. 先拉取云端用户画像
        pull_cloud_user_data(db, cloud_url, headers)
        
        # 2. 推送本地处理结果
        target_date = pendulum.parse(args.date).date() if args.date else None
        push_local_processing_results(
            db, 
            cloud_url=cloud_url, 
            headers=headers, 
            target_date=target_date, 
            source_key=args.source,
            batch_size=args.batch_size,
            limit=args.limit
        )
