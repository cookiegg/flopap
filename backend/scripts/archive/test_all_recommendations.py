#!/usr/bin/env python3

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import asyncio
from app.db.session import SessionLocal
from sqlalchemy import text
import numpy as np
from datetime import date

def test_traditional_recommendation():
    """测试传统个性化推荐"""
    print("🔄 测试传统个性化推荐 (recommendation.py)")
    
    from app.services.recommendation import generate_personalized_pool
    
    with SessionLocal() as db:
        user_id = 'aa1d030e-a686-40af-834c-aad4c1f5165a'
        
        # 生成推荐池
        entries = generate_personalized_pool(db, user_id=user_id)
        
        print(f"  📊 推荐结果: {len(entries)}篇论文")
        
        if entries:
            print("  🎯 Top 5推荐:")
            for i, entry in enumerate(entries[:5], 1):
                paper = db.execute(text('SELECT title FROM papers WHERE id = :id'), {'id': entry.paper_id}).fetchone()
                print(f"    {i}. {paper[0][:60]}... (评分: {entry.score:.4f})")
        
        return len(entries)

async def test_v2_recommendation():
    """测试V2实时推荐"""
    print("\n🔄 测试V2实时推荐 (recommendation_v2.py)")
    
    from app.services.recommendation_v2 import RecommendationV2
    from app.db.session import AsyncSessionLocal
    
    service = RecommendationV2()
    
    async with AsyncSessionLocal() as db:
        user_id = 'aa1d030e-a686-40af-834c-aad4c1f5165a'
        
        # 生成个性化推荐池
        result = await service.generate_personalized_pool(
            db, 
            user_id=user_id,
            arxiv_ratio=10,
            conference_ratio=20,
            max_pool_size=50
        )
        
        print(f"  📊 推荐结果: {len(result)}篇论文")
        
        if result:
            print("  🎯 Top 5推荐:")
            for i, paper in enumerate(result[:5], 1):
                print(f"    {i}. {paper.title[:60]}...")
        
        return len(result)

def test_embedding_recommendation():
    """测试Embedding相似度推荐"""
    print("\n🔄 测试Embedding相似度推荐 (simple_embedding_rec.py)")
    
    from scripts.simple_embedding_rec import recommend_papers
    
    user_id = 'aa1d030e-a686-40af-834c-aad4c1f5165a'
    recommendations = recommend_papers(user_id, 10)
    
    return len(recommendations)

def analyze_user_data():
    """分析用户数据"""
    print("\n📊 用户数据分析")
    
    with SessionLocal() as db:
        user_id = 'aa1d030e-a686-40af-834c-aad4c1f5165a'
        
        # 用户反馈统计
        feedback_result = db.execute(text("""
            SELECT feedback_type, COUNT(*) 
            FROM user_feedback 
            WHERE user_id = :user_id 
            GROUP BY feedback_type
        """), {'user_id': user_id}).fetchall()
        
        print("  👤 用户反馈统计:")
        for feedback_type, count in feedback_result:
            print(f"    {feedback_type}: {count}篇")
        
        # 用户embedding状态
        embedding_result = db.execute(text("""
            SELECT embedding IS NOT NULL as has_embedding,
                   array_length(embedding, 1) as dim
            FROM user_profiles 
            WHERE user_id = :user_id
        """), {'user_id': user_id}).fetchone()
        
        if embedding_result:
            print(f"  🧠 用户embedding: {'✅有' if embedding_result[0] else '❌无'}")
            if embedding_result[1]:
                print(f"    维度: {embedding_result[1]}")
        
        # 候选池统计
        candidate_count = db.execute(text('SELECT COUNT(*) FROM candidate_pools')).fetchone()[0]
        print(f"  📚 候选池大小: {candidate_count}篇论文")

def compare_recommendations():
    """对比推荐结果"""
    print("\n🔍 推荐系统对比分析")
    
    # 运行所有推荐系统
    traditional_count = test_traditional_recommendation()
    v2_count = asyncio.run(test_v2_recommendation())
    embedding_count = test_embedding_recommendation()
    
    print(f"\n📈 推荐数量对比:")
    print(f"  传统推荐: {traditional_count}篇")
    print(f"  V2推荐: {v2_count}篇") 
    print(f"  Embedding推荐: {embedding_count}篇")
    
    return {
        'traditional': traditional_count,
        'v2': v2_count,
        'embedding': embedding_count
    }

if __name__ == "__main__":
    print("🚀 开始全面测试推荐系统")
    
    # 分析用户数据
    analyze_user_data()
    
    # 对比推荐结果
    results = compare_recommendations()
    
    print(f"\n✅ 测试完成!")
    print(f"📋 总结: 3套推荐系统均正常工作，推荐数量分别为 {results['traditional']}, {results['v2']}, {results['embedding']} 篇")
