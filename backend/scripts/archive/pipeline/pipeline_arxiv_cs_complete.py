#!/usr/bin/env python3
"""
完整arXiv CS流水线
1. arXiv获取 + embedding生成
2. CS候选池筛选
3. 翻译 + AI解读生成
4. 用户推荐池生成
5. 推送通知
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

import asyncio
from datetime import date, datetime, timedelta
from app.db.session import SessionLocal, async_session_factory
from app.core.config import settings
from sqlalchemy import text
import pendulum

def step1_arxiv_ingestion_and_embedding():
    """步骤1: arXiv数据获取和embedding生成"""
    print("🔄 步骤1: arXiv数据获取和embedding生成")
    
    from app.services.data_ingestion.ingestion import ingest_for_date
    from app.services.data_ingestion.embedding import encode_documents
    
    with SessionLocal() as db:
        # 使用系统配置的延迟天数 (默认3天，考虑arXiv发布延迟)
        target_date = pendulum.now("UTC").subtract(days=settings.arxiv_submission_delay_days).date()
        print(f"  📅 目标日期: {target_date} (延迟{settings.arxiv_submission_delay_days}天)")
        print(f"  💡 说明: 考虑arXiv提交到发布的审核延迟")
        
        # 数据摄取
        batch = ingest_for_date(db, target_date)
        if not batch:
            print("  ❌ 数据摄取失败")
            return None
        
        print(f"  ✅ 摄取完成: {batch.total_papers}篇论文")
        
        # 生成embeddings - 需要获取论文文本并调用encode_documents
        # 注意: encode_documents需要文本列表，这里需要实现批量embedding逻辑
        print(f"  ⚠️  Embedding生成需要单独实现批量逻辑")
        embedding_count = 0  # 暂时设为0，需要实现具体逻辑
        print(f"  ✅ Embedding生成: {embedding_count}篇")
        
        return batch

def step2_cs_candidate_pool():
    """步骤2: CS候选池筛选"""
    print("\n🔄 步骤2: CS候选池筛选")
    
    from app.services.candidate_pool import CandidatePoolService, cs_filter
    
    with SessionLocal() as db:
        service = CandidatePoolService()
        
        # 使用CS筛选器创建候选池
        cs_count = service.create_filtered_pool(db, cs_filter, pool_name="cs_daily")
        print(f"  ✅ CS候选池: {cs_count}篇论文")
        
        return cs_count

def step3_translation_and_interpretation():
    """步骤3: 翻译和AI解读生成"""
    print("\n🔄 步骤3: 翻译和AI解读生成")
    
    from app.services.translation_pure import batch_translate_papers
    from app.services.ai_interpretation_pure import interpret_and_save_papers
    
    with SessionLocal() as db:
        # 获取候选池论文ID
        result = db.execute(text("""
            SELECT cp.paper_id FROM candidate_pools cp
            JOIN papers p ON cp.paper_id = p.id
            WHERE p.created_at >= CURRENT_DATE
        """)).fetchall()
        
        paper_ids = [row[0] for row in result]
        print(f"  📚 待处理论文: {len(paper_ids)}篇")
        
        if not paper_ids:
            print("  ⚠️  无新论文需要处理")
            return 0, 0
        
        # 批量翻译
        translated_count = batch_translate_papers(db, paper_ids)
        print(f"  ✅ 翻译完成: {translated_count}篇")
        
        # 批量AI解读
        interpreted_count = interpret_and_save_papers(db, paper_ids)
        print(f"  ✅ AI解读完成: {interpreted_count}篇")
        
        return translated_count, interpreted_count

async def step4_user_recommendation_pools():
    """步骤4: 用户推荐池生成"""
    print("\n🔄 步骤4: 用户推荐池生成")
    
    from app.services.user_recommendation import UserRecommendationService
    
    async with async_session_factory() as db:
        service = UserRecommendationService()
        
        # 获取所有活跃用户
        result = await db.execute(text("SELECT DISTINCT user_id FROM user_feedback"))
        user_ids = [row[0] for row in result.fetchall()]
        
        print(f"  👥 活跃用户: {len(user_ids)}个")
        
        # 获取今日候选池
        candidate_result = await db.execute(text("SELECT paper_id FROM candidate_pools"))
        candidate_ids = [str(row[0]) for row in candidate_result.fetchall()]
        
        generated_count = 0
        today = date.today()
        
        for user_id in user_ids:
            try:
                pool = await service.generate_user_pool(
                    db, user_id, today, candidate_ids
                )
                if pool:
                    generated_count += 1
                    print(f"    ✅ 用户 {user_id[:8]}... 推荐池已生成")
            except Exception as e:
                print(f"    ❌ 用户 {user_id[:8]}... 生成失败: {e}")
        
        print(f"  ✅ 推荐池生成: {generated_count}/{len(user_ids)}个用户")
        return generated_count

def step5_push_notifications():
    """步骤5: 推送通知"""
    print("\n🔄 步骤5: 推送通知")
    
    # 这里可以集成推送服务
    # 例如: 邮件通知、短信通知、App推送等
    
    with SessionLocal() as db:
        # 统计今日推荐
        today = date.today()
        result = db.execute(text("""
            SELECT COUNT(DISTINCT user_id) as user_count,
                   SUM(array_length(paper_ids, 1)) as total_recommendations
            FROM user_recommendation_pools 
            WHERE pool_date = :date
        """), {'date': today}).fetchone()
        
        if result and result[0]:
            user_count, total_recs = result
            print(f"  📊 推送统计: {user_count}个用户, {total_recs}条推荐")
            print(f"  📱 推送通知已发送 (模拟)")
            return user_count
        else:
            print("  ⚠️  无推荐数据可推送")
            return 0

def main():
    """主流程"""
    print("🚀 开始完整arXiv CS流水线")
    start_time = datetime.now()
    
    try:
        # 步骤1: 数据获取和embedding
        batch = step1_arxiv_ingestion_and_embedding()
        if not batch:
            print("❌ 流水线中断: 数据获取失败")
            return
        
        # 步骤2: 候选池筛选
        cs_count = step2_cs_candidate_pool()
        if cs_count == 0:
            print("❌ 流水线中断: 无CS论文")
            return
        
        # 步骤3: 翻译和解读
        translated, interpreted = step3_translation_and_interpretation()
        
        # 步骤4: 用户推荐池
        user_pools = asyncio.run(step4_user_recommendation_pools())
        
        # 步骤5: 推送通知
        pushed_users = step5_push_notifications()
        
        # 总结
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n🎉 流水线完成!")
        print(f"⏱️  总耗时: {duration}")
        print(f"📊 处理结果:")
        print(f"   - 摄取论文: {batch.total_papers}篇")
        print(f"   - CS候选池: {cs_count}篇")
        print(f"   - 翻译: {translated}篇")
        print(f"   - AI解读: {interpreted}篇")
        print(f"   - 用户推荐池: {user_pools}个")
        print(f"   - 推送用户: {pushed_users}个")
        
    except Exception as e:
        print(f"❌ 流水线异常: {e}")
        raise

if __name__ == "__main__":
    main()
