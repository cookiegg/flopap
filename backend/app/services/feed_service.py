"""
Feed服务 V2 - 基于推荐池的简化实现
结合 feed_simplified.py 的简洁性和推荐系统的个性化能力
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Paper, PaperTranslation, PaperInterpretation, UserFeedback
from app.schemas.feed import FeedResponse, FeedItem, PaperMeta, PaperTranslationMeta, PaperInterpretationMeta
from app.services.recommendation import RecommendationFacade


def _get_user_pool_ratio(session: Session, user_id: str, source_key: str) -> float:
    """
    从用户设置中获取推荐池比例
    注意: 这个函数现在主要用于 arxiv 动态数据源
    会议数据源使用 DataSourcePoolSettings 表
    返回 0.0 - 1.0 的浮点数
    """
    from app.models.framework_v2 import UserRecommendationSettings
    
    # 查询用户设置
    setting = session.query(UserRecommendationSettings).filter(
        UserRecommendationSettings.user_id == user_id
    ).first()
    
    if not setting:
        # 默认返回 50%
        return 0.5
    
    # 根据数据源类型选择对应的比例
    if source_key == 'arxiv' or source_key.startswith('arxiv_'):
        ratio_percent = setting.arxiv_ratio  # 1-100
    else:
        ratio_percent = setting.conference_ratio  # 1-100
    
    # 转换为 0.0 - 1.0
    return ratio_percent / 100.0


def _get_source_pool_settings(session: Session, user_id: str, source_key: str) -> dict:
    """
    获取数据源池设置 (DataSourcePoolSettings 表)
    用于会议数据源的显示配置
    """
    from app.models.data_source_pool_settings import DataSourcePoolSettings
    
    setting = session.query(DataSourcePoolSettings).filter(
        DataSourcePoolSettings.user_id == user_id,
        DataSourcePoolSettings.source_key == source_key
    ).first()
    
    if not setting:
        return {
            "pool_ratio": 0.2,
            "max_pool_size": 2000,
            "show_mode": "pool",
            "filter_no_content": True
        }
    
    return {
        "pool_ratio": setting.pool_ratio,
        "max_pool_size": setting.max_pool_size,
        "show_mode": setting.show_mode,
        "filter_no_content": setting.filter_no_content
    }


def get_personalized_feed(
    session: Session,
    *,
    cursor: int = 0,
    limit: int = 10,
    user_id: str | None = None,
    source: str | None = None,
    sub: str | None = None  # 新增: arxiv 子池参数 (today/week)
) -> FeedResponse:
    """
    获取个性化推荐Feed - 使用多层推荐池架构
    
    Args:
        sub: arxiv 子池选择 ('today' 或 'week')
    """
    user_id = user_id or settings.default_user_id
    
    # 如果是 arxiv 数据源且指定了 sub 参数
    if (source == 'arxiv' or source is None) and sub in ('today', 'week'):
        from app.services.recommendation.arxiv_pool_service import ArxivPoolService
        arxiv_service = ArxivPoolService(session)
        
        if sub == 'today':
            paper_ids = arxiv_service.get_today_pool(user_id)
        else:  # sub == 'week'
            paper_ids = arxiv_service.get_week_pool(user_id)
        
        if not paper_ids:
            # [NEW] Cloud Cold Start: 尝试使用冷启动服务 (Hot/Latest)
            from app.core.edition import Edition
            if settings.edition == Edition.CLOUD:
                from app.services.recommendation.cold_start_service import ColdStartService
                cold_start = ColdStartService(session)
                paper_ids = cold_start.get_cold_start_pool(limit=50)  # 获取 50 篇
    
            # 如果冷启动也没拿到数据，或者是 Local 版，回退到简单查询
            if not paper_ids:
                return _get_fallback_feed(session, cursor, limit, source)
        
        # 分页处理
        total = len(paper_ids)
        paginated_ids = paper_ids[cursor:cursor + limit] if limit > 0 else paper_ids[cursor:]
        
        return _build_feed_response(session, paginated_ids, user_id, cursor, limit, total)
    
    # 原有逻辑: 使用多层推荐系统
    from app.services.recommendation import MultiLayerRecommendationService
    from app.core.edition import Edition
    
    ml_service = MultiLayerRecommendationService(session)
    source_key = source or 'arxiv'
    
    # 判断是否为会议数据源
    is_conference = source_key != 'arxiv' and not source_key.startswith('arxiv_')
    
    # 统一会议数据源格式：如果是会议 ID (如 neurips2025), 自动加上 conf/ 前缀
    if is_conference and not source_key.startswith('conf/'):
        source_key = f'conf/{source_key}'
    
    try:
        if is_conference:
            # 会议数据源: 显示所有有内容的论文
            pool_settings = _get_source_pool_settings(session, user_id, source.replace('conf/', ''))
            
            # 获取所有排序后的论文 (不截取)
            paper_ids = ml_service.get_user_recommendations(
                user_id, 
                source_key, 
                pool_ratio=1.0,  # 不截取，返回全部排序后的论文
                max_size=pool_settings['max_pool_size']
            )
            
            # 只显示有翻译/AI内容的论文 (默认开启)
            if pool_settings['filter_no_content'] and paper_ids:
                paper_ids = _filter_papers_with_content(session, paper_ids)
        else:
            # ArXiv 数据源: 保持原有逻辑
            pool_ratio = _get_user_pool_ratio(session, user_id, source_key)
            paper_ids = ml_service.get_user_recommendations(user_id, source_key, pool_ratio=pool_ratio)
        
        if not paper_ids:
            # 如果没有推荐池，回退到简单查询
            return _get_fallback_feed(session, cursor, limit, source)
        
        # 分页处理
        total = len(paper_ids)
        paginated_ids = paper_ids[cursor:cursor + limit] if limit > 0 else paper_ids[cursor:]
        
        return _build_feed_response(session, paginated_ids, user_id, cursor, limit, total)
        
    except Exception as e:
        # 推荐系统异常时回退到简单查询
        return _get_fallback_feed(session, cursor, limit, source)


def _filter_papers_with_content(session: Session, paper_ids: List[UUID]) -> List[UUID]:
    """过滤有翻译或AI解读内容的论文"""
    from sqlalchemy import select, or_
    
    # 查询有翻译或解读的论文ID
    trans_stmt = select(PaperTranslation.paper_id).where(PaperTranslation.paper_id.in_(paper_ids))
    interp_stmt = select(PaperInterpretation.paper_id).where(PaperInterpretation.paper_id.in_(paper_ids))
    
    papers_with_translation = set(session.execute(trans_stmt).scalars().all())
    papers_with_interpretation = set(session.execute(interp_stmt).scalars().all())
    papers_with_content = papers_with_translation.union(papers_with_interpretation)
    
    # 保持原顺序过滤
    return [pid for pid in paper_ids if pid in papers_with_content]


def _get_fallback_feed(
    session: Session,
    cursor: int,
    limit: int,
    source: str | None
) -> FeedResponse:
    """回退到简单的按时间排序查询"""
    query = select(Paper).order_by(Paper.submitted_date.desc())
    
    if source:
        # 统一会议数据源格式
        source_key = source
        if source != 'arxiv' and not source.startswith('conf/'):
            source_key = f'conf/{source}'
        query = query.where(Paper.source == source_key)
    
    query = query.offset(cursor).limit(limit)
    papers = session.execute(query).scalars().all()
    
    return _build_feed_response(session, [p.id for p in papers], None, cursor, limit, None)


def _build_feed_response(
    session: Session,
    paper_ids: List[UUID],
    user_id: str | None,
    cursor: int,
    limit: int,
    total: int | None
) -> FeedResponse:
    """构建Feed响应"""
    if not paper_ids:
        return FeedResponse(items=[], next_cursor=0, total=0)
    
    # 批量查询论文数据
    papers = {p.id: p for p in session.execute(
        select(Paper).where(Paper.id.in_(paper_ids))
    ).scalars().all()}
    
    # 批量查询翻译数据
    translations = {t.paper_id: t for t in session.execute(
        select(PaperTranslation).where(PaperTranslation.paper_id.in_(paper_ids))
    ).scalars().all()}
    
    # 批量查询解读数据
    interpretations = {i.paper_id: i for i in session.execute(
        select(PaperInterpretation).where(PaperInterpretation.paper_id.in_(paper_ids))
    ).scalars().all()}
    
    # 批量查询infographic数据
    from app.models.paper_infographic import PaperInfographic
    infographics_list = session.execute(
        select(PaperInfographic).where(PaperInfographic.paper_id.in_([str(pid) for pid in paper_ids]))
    ).scalars().all()
    
    # 确保键类型一致性 - 将字符串键转换为UUID以匹配paper_ids
    infographics = {}
    for infographic in infographics_list:
        # 将字符串paper_id转换为UUID以匹配paper_ids中的类型
        from uuid import UUID
        paper_uuid = UUID(infographic.paper_id)
        infographics[paper_uuid] = infographic
    
    # 批量查询visual数据
    from app.models.paper import PaperVisual
    visuals = {v.paper_id: v for v in session.execute(
        select(PaperVisual).where(PaperVisual.paper_id.in_(paper_ids))
    ).scalars().all()}
    
    # Debug: Check DisCO infographic
    disco_id = "24971a08-467f-4cea-ad54-e8200196cf98"
    if any(str(pid) == disco_id for pid in paper_ids):
        print(f"[DEBUG] DisCO paper {disco_id} in paper_ids")
        disco_uuid = next((pid for pid in paper_ids if str(pid) == disco_id), None)
        print(f"[DEBUG] disco_uuid: {disco_uuid} (type: {type(disco_uuid)})")
        print(f"[DEBUG] infographics keys: {[(k, type(k)) for k in list(infographics.keys())[:3]]}")
        if disco_uuid and disco_uuid in infographics:
            print(f"[DEBUG] DisCO infographic found: {len(infographics[disco_uuid].html_content)} chars")
        else:
            print(f"[DEBUG] DisCO infographic NOT found")
    else:
        print(f"[DEBUG] DisCO paper {disco_id} NOT in paper_ids")
    
    # 批量查询用户反馈（如果有用户ID）
    feedback_map = {}
    if user_id:
        feedback_map = _get_user_feedback_map(session, paper_ids, user_id)
    
    # 构建Feed项目
    items = []
    for position, paper_id in enumerate(paper_ids):
        paper = papers.get(paper_id)
        if not paper:
            continue
            
        translation = translations.get(paper_id)
        interpretation = interpretations.get(paper_id)
        infographic = infographics.get(paper_id)
        visual = visuals.get(paper_id)
        feedback = feedback_map.get(paper_id, {})
        
        items.append(FeedItem(
            position=position + cursor,
            score=1.0,
            paper=_paper_to_meta(paper, translation, interpretation, infographic, visual),
            liked=feedback.get("like", False),
            bookmarked=feedback.get("bookmark", False),
            disliked=feedback.get("dislike", False),
        ))
    
    # 计算下一页游标
    next_cursor = cursor + len(items) if limit > 0 and len(items) == limit else 0
    
    return FeedResponse(
        items=items,
        next_cursor=next_cursor,
        total=total or len(items)
    )


def _get_user_feedback_map(session: Session, paper_ids: List[UUID], user_id: str) -> dict:
    """获取用户反馈映射"""
    feedback_map = {pid: {"like": False, "bookmark": False, "dislike": False} for pid in paper_ids}
    
    feedbacks = session.execute(
        select(UserFeedback).where(
            UserFeedback.user_id == user_id,
            UserFeedback.paper_id.in_(paper_ids)
        )
    ).scalars().all()
    
    for feedback in feedbacks:
        feedback_map[feedback.paper_id][feedback.feedback_type.value] = True
    
    return feedback_map


def _paper_to_meta(
    paper: Paper,
    translation: Optional[PaperTranslation] = None,
    interpretation: Optional[PaperInterpretation] = None,
    infographic: Optional = None,
    visual: Optional = None
) -> PaperMeta:
    """转换Paper对象为PaperMeta"""
    translation_meta = None
    if translation and (translation.title_zh or translation.summary_zh):
        translation_meta = PaperTranslationMeta(
            title_zh=translation.title_zh,
            summary_zh=translation.summary_zh,
            model_name=translation.model_name,
        )
    
    interpretation_meta = None
    if interpretation and interpretation.interpretation:
        interpretation_meta = PaperInterpretationMeta(
            interpretation=interpretation.interpretation,
            language=interpretation.language,
            model_name=interpretation.model_name,
        )
    
    return PaperMeta(
        id=paper.id,
        arxiv_id=paper.arxiv_id,
        title=paper.title,
        summary=paper.summary,
        authors=[{"name": author} if isinstance(author, str) else author for author in (paper.authors or [])],
        categories=paper.categories,
        submitted_date=paper.submitted_date,
        updated_date=paper.updated_date,
        pdf_url=paper.pdf_url,
        html_url=paper.html_url,
        comment=paper.comment,
        doi=paper.doi,
        primary_category=paper.primary_category,
        source=getattr(paper, 'source', ''),  # 添加source字段
        translation=translation_meta,
        interpretation=interpretation_meta,
        infographic_html=infographic.html_content if infographic else None,
        visual_html=visual.image_data if visual else None,
    )
