#!/usr/bin/env python3

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import asyncio
from app.db.session import SessionLocal, async_session_factory
from sqlalchemy import text

def test_embedding_recommendation():
    """测试Embedding相似度推荐"""
    print("🔄 测试Embedding相似度推荐")
    
    from scripts.simple_embedding_rec import recommend_papers
    
    user_id = 'aa1d030e-a686-40af-834c-aad4c1f5165a'
    recommendations = recommend_papers(user_id, 10)
    
    return len(recommendations)

async def test_v2_recommendation():
    """测试V2实时推荐"""
    print("\n🔄 测试V2实时推荐")
    
    from app.services.recommendation_v2 import RecommendationV2
    
    service = RecommendationV2()
    
    async with async_session_factory() as db:
        user_id = 'aa1d030e-a686-40af-834c-aad4c1f5165a'
        
        try:
            # 生成个性化推荐池
            result = await service.generate_personalized_pool(db, user_id=user_id)
            
            print(f"  📊 推荐结果: {len(result)}篇论文")
            
            if result:
                print("  🎯 Top 3推荐:")
                for i, paper in enumerate(result[:3], 1):
                    print(f"    {i}. {paper.title[:60]}...")
            
            return len(result)
        except Exception as e:
            print(f"  ❌ V2推荐测试失败: {e}")
            return 0

def analyze_candidate_pool():
    """分析候选池数据"""
    print("\n📊 候选池数据分析")
    
    with SessionLocal() as db:
        # 候选池统计
        total_candidates = db.execute(text('SELECT COUNT(*) FROM candidate_pools')).fetchone()[0]
        print(f"  📚 候选池总数: {total_candidates}篇论文")
        
        # 有embedding的论文数量
        with_embedding = db.execute(text("""
            SELECT COUNT(*) FROM candidate_pools cp
            JOIN papers p ON cp.paper_id = p.id
            JOIN paper_embeddings pe ON p.id = pe.paper_id
        """)).fetchone()[0]
        print(f"  🧠 有embedding的论文: {with_embedding}篇")
        
        # 用户反馈统计
        user_id = 'aa1d030e-a686-40af-834c-aad4c1f5165a'
        feedback_result = db.execute(text("""
            SELECT feedback_type, COUNT(*) 
            FROM user_feedback 
            WHERE user_id = :user_id 
            GROUP BY feedback_type
        """), {'user_id': user_id}).fetchall()
        
        print(f"  👤 用户 {user_id[:8]}... 反馈:")
        for feedback_type, count in feedback_result:
            print(f"    {feedback_type}: {count}篇")

def main():
    print("🚀 简化推荐系统测试")
    
    # 分析候选池
    analyze_candidate_pool()
    
    # 测试embedding推荐
    embedding_count = test_embedding_recommendation()
    
    # 测试V2推荐
    v2_count = asyncio.run(test_v2_recommendation())
    
    print(f"\n📈 推荐结果对比:")
    print(f"  Embedding推荐: {embedding_count}篇")
    print(f"  V2实时推荐: {v2_count}篇")
    
    print(f"\n✅ 测试完成!")

if __name__ == "__main__":
    main()
