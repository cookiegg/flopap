from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import date, timedelta
import logging

from app.api import deps
from app.db.session import SessionLocal
from app.core.config import settings

# Services
from app.services.data_ingestion.ingestion import ingest_for_date
from app.services.data_ingestion.arxiv_candidate_pool import CandidatePoolServiceV2, cs_filter, FILTERS_V2
from app.services.recommendation.multi_layer_recommendation import MultiLayerRecommendationService
from app.services.content_generation.translation_generate import translate_and_save_papers
from app.services.content_generation.ai_interpretation_generate import batch_generate_interpretations
from app.services.content_generation.tts_generate import get_papers_with_content, clean_markdown_for_tts
from app.services.content_generation.tts_storage import tts_storage

router = APIRouter()
logger = logging.getLogger(__name__)

# Request Models
class FactoryRequest(BaseModel):
    target_date: Optional[date] = None
    category: str = "cs"

class ContentGenRequest(BaseModel):
    target_date: Optional[date] = None
    scope: str = "candidate"  # "candidate" or "user"
    steps: List[str] = ["trans", "ai", "tts"] # "trans", "ai", "tts"
    category: str = "cs"

# Enhanced Status with timestamps, counts, and per-task errors
factory_status = {
    "fetch_arxiv": {
        "status": "idle",
        "count": 0,
        "last_date": None,
        "last_run_at": None,
        "error": None
    },
    "gen_candidate_pool": {
        "status": "idle",
        "count": 0,
        "last_date": None,
        "last_run_at": None,
        "error": None
    },
    "gen_recommendation": {
        "status": "idle",
        "count": 0,
        "last_run_at": None,
        "error": None
    },
    "gen_content": {
        "status": "idle",
        "count": 0,
        "scope": None,
        "last_run_at": None,
        "error": None
    }
}

def _run_fetch_arxiv(target_date: date):
    global factory_status
    import pendulum
    from sqlalchemy import func
    from app.models import Paper
    
    factory_status["fetch_arxiv"]["status"] = "running"
    factory_status["fetch_arxiv"]["error"] = None
    db = SessionLocal()
    try:
        logger.info(f"Factory: Starting Arxiv Fetch for {target_date}")
        ingest_for_date(session=db, target_date=target_date)
        
        # Count papers for this date
        count = db.query(func.count(Paper.id)).filter(Paper.submitted_date >= target_date).scalar() or 0
        
        factory_status["fetch_arxiv"]["status"] = "success"
        factory_status["fetch_arxiv"]["count"] = count
        factory_status["fetch_arxiv"]["last_date"] = str(target_date)
        factory_status["fetch_arxiv"]["last_run_at"] = pendulum.now().to_iso8601_string()
    except Exception as e:
        logger.error(f"Factory: Arxiv Fetch failed: {e}")
        factory_status["fetch_arxiv"]["status"] = "error"
        factory_status["fetch_arxiv"]["error"] = str(e)
    finally:
        db.close()

def _run_gen_candidate_pool(target_date: date, category: str = "cs"):
    global factory_status
    import pendulum
    
    factory_status["gen_candidate_pool"]["status"] = "running"
    factory_status["gen_candidate_pool"]["error"] = None
    db = SessionLocal()
    try:
        logger.info(f"Factory: Generating {category} Candidate Pool for {target_date}")
        
        filter_func = FILTERS_V2.get(category, cs_filter)
        
        CandidatePoolServiceV2.create_filtered_pool_by_date(
            session=db,
            target_date=target_date,
            filter_type=category,
            filter_func=filter_func
        )
        db.commit()
        
        # Get count from pool
        count = len(CandidatePoolServiceV2.get_candidate_papers_by_date(db, target_date, category))
        
        factory_status["gen_candidate_pool"]["status"] = "success"
        factory_status["gen_candidate_pool"]["count"] = count
        factory_status["gen_candidate_pool"]["last_date"] = str(target_date)
        factory_status["gen_candidate_pool"]["last_run_at"] = pendulum.now().to_iso8601_string()
    except Exception as e:
        logger.error(f"Factory: Candidate Pool Generation failed: {e}")
        factory_status["gen_candidate_pool"]["status"] = "error"
        factory_status["gen_candidate_pool"]["error"] = str(e)
    finally:
        db.close()

def _run_gen_recommendation(user_id: str, category: str = "cs"):
    global factory_status
    import pendulum
    from app.services.recommendation.user_ranking_service import UserRankingService
    
    factory_status["gen_recommendation"]["status"] = "running"
    factory_status["gen_recommendation"]["error"] = None
    db = SessionLocal()
    try:
        logger.info(f"Factory: Generating Recommendations for User {user_id} (Category: {category})")
        
        # Get candidate pool
        target_date = pendulum.now("America/New_York").subtract(days=3).date()
        candidate_paper_ids = CandidatePoolServiceV2.get_candidate_papers_by_date(
            session=db, target_date=target_date, filter_type=category
        )
        
        if not candidate_paper_ids:
            logger.warning(f"Factory: No candidate papers found for {target_date}")
            factory_status["gen_recommendation"]["status"] = "success_empty"
            factory_status["gen_recommendation"]["count"] = 0
            factory_status["gen_recommendation"]["last_run_at"] = pendulum.now().to_iso8601_string()
            return
        
        # Create user ranking - use arxiv_day_ prefix to match ArxivPoolService
        ranking_service = UserRankingService(db)
        source_key = f"arxiv_day_{target_date.strftime('%Y%m%d')}"
        
        success = ranking_service.update_user_ranking(
            user_id=user_id,
            source_key=source_key,
            paper_ids=candidate_paper_ids,
            force_update=True
        )
        
        if success:
            factory_status["gen_recommendation"]["status"] = "success"
            factory_status["gen_recommendation"]["count"] = len(candidate_paper_ids)
        else:
            factory_status["gen_recommendation"]["status"] = "success_empty"
            factory_status["gen_recommendation"]["count"] = 0
            
        factory_status["gen_recommendation"]["last_run_at"] = pendulum.now().to_iso8601_string()
            
    except Exception as e:
        logger.error(f"Factory: Rec Generation failed: {e}")
        factory_status["gen_recommendation"]["status"] = "error"
        factory_status["gen_recommendation"]["error"] = str(e)
    finally:
        db.close()

def _run_gen_content(target_date: date, scope: str, steps: List[str], user_id: str, category: str = "cs"):
    global factory_status
    import pendulum
    
    factory_status["gen_content"]["status"] = "running"
    factory_status["gen_content"]["error"] = None
    factory_status["gen_content"]["scope"] = scope
    db = SessionLocal()
    try:
        paper_ids = []
        if scope == "candidate":
            logger.info(f"Factory: Fetching {category} Candidate Pool for {target_date}")
            paper_ids = CandidatePoolServiceV2.get_candidate_papers_by_date(
                session=db, target_date=target_date, filter_type=category
            )
        elif scope == "user":
            logger.info(f"Factory: Fetching User Recommendations for {user_id}")
            service = MultiLayerRecommendationService(db)
            paper_ids = service.get_user_recommendations(user_id, "arxiv", pool_ratio=0.1, max_size=1000)
        
        if not paper_ids:
            logger.warning("Factory: No papers found to process")
            factory_status["gen_content"]["status"] = "success_empty"
            factory_status["gen_content"]["count"] = 0
            factory_status["gen_content"]["last_run_at"] = pendulum.now().to_iso8601_string()
            return

        logger.info(f"Factory: Processing {len(paper_ids)} papers. Steps: {steps}")
        
        if "trans" in steps:
            translate_and_save_papers(session=db, paper_ids=paper_ids, max_workers=20, force_retranslate=False)
        
        if "ai" in steps:
            batch_generate_interpretations(session=db, paper_ids=paper_ids, max_workers=20, force_regenerate=False)
        
        if "tts" in steps:
            from app.services.content_generation.tts_service import tts_service
            tts_service.generate_batch(session=db, paper_ids=paper_ids, save_to_storage=True)

        factory_status["gen_content"]["status"] = "success"
        factory_status["gen_content"]["count"] = len(paper_ids)
        factory_status["gen_content"]["last_run_at"] = pendulum.now().to_iso8601_string()
    except Exception as e:
        logger.error(f"Factory: Content Generation failed: {e}")
        factory_status["gen_content"]["status"] = "error"
        factory_status["gen_content"]["error"] = str(e)
    finally:
        db.close()

# Endpoints

@router.get("/status")
def get_status(current_user: str = Depends(deps.get_current_user)):
    return factory_status

@router.post("/fetch-arxiv")
def trigger_fetch_arxiv(
    req: FactoryRequest, 
    background_tasks: BackgroundTasks,
    current_user: str = Depends(deps.get_current_user)
):
    if factory_status["fetch_arxiv"]["status"] == "running":
        raise HTTPException(status_code=400, detail="Task already running")
    
    target_dt = req.target_date
    if not target_dt:
        import pendulum
        target_dt = pendulum.now("America/New_York").subtract(days=3).date()
        
    background_tasks.add_task(_run_fetch_arxiv, target_dt)
    return {"status": "started", "target_date": target_dt}

@router.post("/candidate-pool")
def trigger_candidate_pool(
    req: FactoryRequest, 
    background_tasks: BackgroundTasks,
    current_user: str = Depends(deps.get_current_user)
):
    if factory_status["gen_candidate_pool"]["status"] == "running":
        raise HTTPException(status_code=400, detail="Task already running")
        
    target_dt = req.target_date
    if not target_dt:
        import pendulum
        target_dt = pendulum.now("America/New_York").subtract(days=3).date()
        
    background_tasks.add_task(_run_gen_candidate_pool, target_dt, req.category)
    return {"status": "started", "target_date": target_dt, "category": req.category}

@router.post("/recommendation")
def trigger_recommendation(
    req: FactoryRequest, 
    background_tasks: BackgroundTasks,
    current_user: str = Depends(deps.get_current_user)
):
    if factory_status["gen_recommendation"]["status"] == "running":
        raise HTTPException(status_code=400, detail="Task already running")
    
    user_id = current_user
        
    background_tasks.add_task(_run_gen_recommendation, user_id, req.category)
    return {"status": "started", "user_id": user_id, "category": req.category}

@router.post("/content-gen")
def trigger_content_gen(
    req: ContentGenRequest, 
    background_tasks: BackgroundTasks,
    current_user: str = Depends(deps.get_current_user)
):
    if factory_status["gen_content"]["status"] == "running":
        raise HTTPException(status_code=400, detail="Task already running")
        
    target_dt = req.target_date
    if not target_dt:
        import pendulum
        target_dt = pendulum.now("America/New_York").subtract(days=3).date()
        
    user_id = current_user
    if req.scope == "user" and not user_id:
        raise HTTPException(status_code=400, detail="User ID required for user scope")

    background_tasks.add_task(_run_gen_content, target_dt, req.scope, req.steps, user_id, req.category)
    return {"status": "started", "scope": req.scope, "steps": req.steps, "category": req.category}


# ==================== Conference Endpoints ====================

# Conference status tracking
conference_status = {}

class ConferenceRequest(BaseModel):
    force_update: bool = False
    max_users: Optional[int] = None
    steps: List[str] = ["trans", "ai"]
    pool_ratio: float = 0.2  # 推荐池大小比例 (0.1 - 1.0)
    content_scope: str = "all"  # "all" 或 "pool" - 内容生成范围


def _run_conference_import(conf_id: str):
    """后台任务: 导入会议论文"""
    global conference_status
    import pendulum
    
    if conf_id not in conference_status:
        conference_status[conf_id] = {"import": {}, "pool": {}, "content": {}}
    
    conference_status[conf_id]["import"]["status"] = "running"
    conference_status[conf_id]["import"]["error"] = None
    
    try:
        from app.services.data_ingestion.conference_import import import_conference_papers
        
        db = SessionLocal()
        try:
            batch = import_conference_papers(db, conf_id)
            conference_status[conf_id]["import"]["status"] = "success"
            conference_status[conf_id]["import"]["count"] = batch.item_count
            conference_status[conf_id]["import"]["last_run_at"] = pendulum.now().to_iso8601_string()
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Conference import failed for {conf_id}: {e}")
        conference_status[conf_id]["import"]["status"] = "error"
        conference_status[conf_id]["import"]["error"] = str(e)


def _run_conference_pool(conf_id: str, force_update: bool = False, max_users: Optional[int] = None, pool_ratio: float = None):
    """后台任务: 生成会议推荐池"""
    global conference_status
    import pendulum
    from sqlalchemy import select, distinct, func
    from app.models import Paper, UserPaperRanking, UserFeedback
    from app.models.data_source_pool_settings import DataSourcePoolSettings
    from app.services.recommendation.user_ranking_service import UserRankingService
    
    if conf_id not in conference_status:
        conference_status[conf_id] = {"import": {}, "pool": {}, "content": {}}
    
    conference_status[conf_id]["pool"]["status"] = "running"
    conference_status[conf_id]["pool"]["error"] = None
    
    try:
        db = SessionLocal()
        try:
            source_key = f"conf/{conf_id}"
            
            # 0. 从 DataSourcePoolSettings 读取设置 (如果未提供 pool_ratio)
            if pool_ratio is None:
                settings = db.query(DataSourcePoolSettings).filter(
                    DataSourcePoolSettings.user_id == 'default',
                    DataSourcePoolSettings.source_key == conf_id
                ).first()
                if settings:
                    pool_ratio = settings.pool_ratio
                    max_pool_size = settings.max_pool_size
                else:
                    pool_ratio = 0.2  # 默认 20%
                    max_pool_size = 2000
            else:
                max_pool_size = 2000
            
            # 1. 计算总论文数
            total_count = db.scalar(
                select(func.count(Paper.id)).where(Paper.source == source_key)
            ) or 0
            
            # 2. 根据比例和上限计算采样限制
            limit = min(max(10, int(total_count * pool_ratio)), max_pool_size)
            
            # 3. 获取论文ID (全量获取以计算推荐分数)
            # 为了防止OOM，设置最大上限为3000
            paper_ids = list(db.execute(
                select(Paper.id)
                .where(Paper.source == source_key)
                .limit(3000)
            ).scalars().all())
            
            logger.info(f"Pool generation for {conf_id}: ratio={pool_ratio}, total={total_count}, candidates={len(paper_ids)}, target_limit={limit}")
            
            if not paper_ids:
                conference_status[conf_id]["pool"]["status"] = "error"
                conference_status[conf_id]["pool"]["error"] = "No papers found. Run import first."
                return
            
            # Get active users
            feedback_users = set(db.execute(
                select(distinct(UserFeedback.user_id))
            ).scalars().all())
            ranking_users = set(db.execute(
                select(distinct(UserPaperRanking.user_id))
            ).scalars().all())
            users = list(feedback_users.union(ranking_users))
            
            if max_users:
                users = users[:max_users]
            
            # Generate rankings
            ranking_service = UserRankingService(db)
            success_count = 0
            
            for user_id in users:
                try:
                    success = ranking_service.update_user_ranking(
                        user_id=user_id,
                        source_key=conf_id,
                        paper_ids=paper_ids,
                        force_update=force_update
                    )
                    if success:
                        success_count += 1
                except Exception as e:
                    logger.error(f"Pool generation failed for user {user_id}: {e}")
            
            conference_status[conf_id]["pool"]["status"] = "success"
            conference_status[conf_id]["pool"]["count"] = success_count
            conference_status[conf_id]["pool"]["total_users"] = len(users)
            conference_status[conf_id]["pool"]["last_run_at"] = pendulum.now().to_iso8601_string()
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Conference pool generation failed for {conf_id}: {e}")
        conference_status[conf_id]["pool"]["status"] = "error"
        conference_status[conf_id]["pool"]["error"] = str(e)


def _run_conference_content(conf_id: str, steps: List[str], content_scope: str = "all", pool_ratio: float = 0.2):
    """后台任务: 生成会议内容 (翻译/解读)"""
    global conference_status
    import pendulum
    from sqlalchemy import text
    from app.models import PaperTranslation, PaperInterpretation, UserPaperRanking
    
    if conf_id not in conference_status:
        conference_status[conf_id] = {"import": {}, "pool": {}, "content": {}}
    
    conference_status[conf_id]["content"]["status"] = "running"
    conference_status[conf_id]["content"]["error"] = None
    conference_status[conf_id]["content"]["scope"] = content_scope
    
    try:
        db = SessionLocal()
        try:
            source_key = f"conf/{conf_id}"
            
            if content_scope == "pool":
                # 只对用户推荐池中的论文生成内容
                query = text("""
                    SELECT DISTINCT p.id FROM papers p
                    INNER JOIN user_paper_rankings upr ON p.id = ANY(upr.paper_ids[1 : GREATEST(10, CAST(cardinality(upr.paper_ids) * :ratio AS INT))]) 
                                                        AND upr.source_key = :conf_id
                    WHERE p.source = :source
                """)
                params = {"source": source_key, "ratio": pool_ratio, "conf_id": conf_id}
            else:
                # 对全部论文生成内容
                query = text("""
                    SELECT p.id FROM papers p
                    WHERE p.source = :source
                """)
                params = {"source": source_key}
            
            # Fetch ALL candidates (usually < 3000)
            all_paper_ids = list(db.execute(query, params).scalars().all())
            
            # Filter in Python based on requested steps
            from app.models import PaperTTS
            
            # Batch check existence
            missing_ids = []
            
            # Helper to check existence
            def check_existence(ids, model):
                stmt = select(model.paper_id).where(model.paper_id.in_(ids))
                return set(db.execute(stmt).scalars().all())

            existing_trans = check_existence(all_paper_ids, PaperTranslation) if "trans" in steps else set()
            existing_ai = check_existence(all_paper_ids, PaperInterpretation) if "ai" in steps else set()
            existing_tts = check_existence(all_paper_ids, PaperTTS) if "tts" in steps else set()
            
            for pid in all_paper_ids:
                needs_work = False
                if "trans" in steps and pid not in existing_trans:
                    needs_work = True
                elif "ai" in steps and pid not in existing_ai:
                    needs_work = True
                elif "tts" in steps and pid not in existing_tts:
                    needs_work = True
                
                if needs_work:
                    missing_ids.append(pid)
                    if len(missing_ids) >= 200:  # Batch Limit
                        break
            
            paper_ids = missing_ids
            
            if not paper_ids:
                conference_status[conf_id]["content"]["status"] = "success"
                conference_status[conf_id]["content"]["message"] = "All papers already have requested content"
                conference_status[conf_id]["content"]["last_run_at"] = pendulum.now().to_iso8601_string()
                return
            
            results = {"trans": 0, "ai": 0, "tts": 0}
            
            if "trans" in steps:
                translate_and_save_papers(session=db, paper_ids=paper_ids, max_workers=20, force_retranslate=False)
                results["trans"] = len(paper_ids)
            
            if "ai" in steps:
                batch_generate_interpretations(session=db, paper_ids=paper_ids, max_workers=20, force_regenerate=False)
                results["ai"] = len(paper_ids)

            if "tts" in steps:
                from app.services.content_generation.tts_service import tts_service
                tts_service.generate_batch(session=db, paper_ids=paper_ids, save_to_storage=True)
                results["tts"] = len(paper_ids)
            
            conference_status[conf_id]["content"]["status"] = "success"
            conference_status[conf_id]["content"]["count"] = len(paper_ids)
            conference_status[conf_id]["content"]["results"] = results
            conference_status[conf_id]["content"]["last_run_at"] = pendulum.now().to_iso8601_string()
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Conference content generation failed for {conf_id}: {e}")
        conference_status[conf_id]["content"]["status"] = "error"
        conference_status[conf_id]["content"]["error"] = str(e)


@router.get("/conferences")
def get_available_conferences(current_user: str = Depends(deps.get_current_user)):
    """获取可用的会议列表 - 优先从数据库查询已导入的会议"""
    from app.services.data_ingestion.conference_import import get_available_2025_conferences, SUPPORTED_2025_CONFERENCES
    from sqlalchemy import select, func, distinct
    from app.models import Paper
    
    db = SessionLocal()
    try:
        result = []
        
        # 1. 从数据库获取已导入的会议 (source like 'conf/%')
        imported_sources = db.query(
            Paper.source,
            func.count(Paper.id).label('count')
        ).filter(
            Paper.source.like('conf/%')
        ).group_by(Paper.source).all()
        
        imported_confs = {}
        for source, count in imported_sources:
            if source.startswith('conf/'):
                conf_id = source[5:]  # 去掉 'conf/' 前缀
                imported_confs[conf_id] = count
        
        # 2. 添加已导入的会议
        for conf_id, paper_count in imported_confs.items():
            conf_info = SUPPORTED_2025_CONFERENCES.get(conf_id, {})
            conf_name = conf_info.get('name', conf_id.upper())
            
            result.append({
                "id": conf_id,
                "name": conf_name,
                "file_size_mb": 0,  # 已导入的会议不需要显示文件大小
                "imported": True,
                "paper_count": paper_count,
                "status": conference_status.get(conf_id, {})
            })
        
        # 3. 尝试获取未导入但有数据文件的会议 (用于本地导入)
        try:
            file_available = get_available_2025_conferences()
            for conf in file_available:
                conf_id = conf['id']
                if conf_id not in imported_confs:
                    result.append({
                        "id": conf_id,
                        "name": conf['name'],
                        "file_size_mb": round(conf['file_size'] / (1024 * 1024), 1),
                        "imported": False,
                        "paper_count": 0,
                        "status": conference_status.get(conf_id, {})
                    })
        except Exception:
            pass  # 文件不存在时忽略
        
        # 按名称排序
        result.sort(key=lambda x: x['name'])
        
        return {"conferences": result}
    finally:
        db.close()


@router.post("/conference/{conf_id}/import")
def trigger_conference_import(
    conf_id: str,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(deps.get_current_user)
):
    """导入会议论文"""
    from app.services.data_ingestion.conference_import import SUPPORTED_2025_CONFERENCES
    
    if conf_id not in SUPPORTED_2025_CONFERENCES:
        raise HTTPException(status_code=404, detail=f"Conference {conf_id} not supported")
    
    if conf_id in conference_status and conference_status[conf_id].get("import", {}).get("status") == "running":
        raise HTTPException(status_code=400, detail="Import already running")
    
    background_tasks.add_task(_run_conference_import, conf_id)
    return {"status": "started", "conference": conf_id}


@router.post("/conference/{conf_id}/pool")
def trigger_conference_pool(
    conf_id: str,
    req: ConferenceRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(deps.get_current_user)
):
    """生成会议推荐池"""
    from app.services.data_ingestion.conference_import import SUPPORTED_2025_CONFERENCES
    
    if conf_id not in SUPPORTED_2025_CONFERENCES:
        raise HTTPException(status_code=404, detail=f"Conference {conf_id} not supported")
    
    if conf_id in conference_status and conference_status[conf_id].get("pool", {}).get("status") == "running":
        raise HTTPException(status_code=400, detail="Pool generation already running")
    
    # Pass pool_ratio to pool generation task
    background_tasks.add_task(_run_conference_pool, conf_id, req.force_update, req.max_users, req.pool_ratio)
    return {"status": "started", "conference": conf_id, "force_update": req.force_update, "pool_ratio": req.pool_ratio}


@router.post("/conference/{conf_id}/content")
def trigger_conference_content(
    conf_id: str,
    req: ConferenceRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(deps.get_current_user)
):
    """生成会议内容 (翻译/AI解读)"""
    from app.services.data_ingestion.conference_import import SUPPORTED_2025_CONFERENCES
    
    if conf_id not in SUPPORTED_2025_CONFERENCES:
        raise HTTPException(status_code=404, detail=f"Conference {conf_id} not supported")
    
    if conf_id in conference_status and conference_status[conf_id].get("content", {}).get("status") == "running":
        raise HTTPException(status_code=400, detail="Content generation already running")
    
    # Remove pool_ratio from content generation task (it uses existing user_rankings for pool scope)
    background_tasks.add_task(_run_conference_content, conf_id, req.steps, req.content_scope, req.pool_ratio)
    return {"status": "started", "conference": conf_id, "steps": req.steps, "scope": req.content_scope, "pool_ratio": req.pool_ratio}

