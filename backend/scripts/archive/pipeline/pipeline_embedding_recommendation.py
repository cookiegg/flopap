#!/usr/bin/env python3
"""
基于Embedding的个性化推荐流水线
1. 用户embedding更新
2. 候选池embedding相似度计算
3. 个性化推荐生成
4. 推荐结果存储和推送
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from datetime import datetime
from app.db.session import SessionLocal
from sqlalchemy import text
import numpy as np

def step1_update_user_embeddings():
    """步骤1: 更新用户embedding"""
    print("🔄 步骤1: 更新用户embedding")
    
    from scripts.init_user_embeddings import init_user_embeddings
    
    # 重新生成所有用户embedding
    init_user_embeddings()
    
    # 统计结果
    with SessionLocal() as db:
        result = db.execute(text("""
            SELECT COUNT(*) as total_users,
                   COUNT(embedding) as users_with_embedding
            FROM user_profiles
        """)).fetchone()
        
        print(f"  ✅ 用户embedding更新: {result[1]}/{result[0]}个用户")
        return result[1]

def step2_calculate_similarities():
    """步骤2: 计算embedding相似度"""
    print("\n🔄 步骤2: 计算embedding相似度")
    
    with SessionLocal() as db:
        # 获取有embedding的用户
        users_result = db.execute(text("""
            SELECT user_id, embedding 
            FROM user_profiles 
            WHERE embedding IS NOT NULL
        """)).fetchall()
        
        # 获取候选池论文embedding
        papers_result = db.execute(text("""
            SELECT p.id, pe.vector
            FROM papers p
            JOIN paper_embeddings pe ON p.id = pe.paper_id
            JOIN candidate_pools cp ON p.id = cp.paper_id
            WHERE pe.vector IS NOT NULL
        """)).fetchall()
        
        print(f"  👥 用户数: {len(users_result)}")
        print(f"  📚 候选论文数: {len(papers_result)}")
        
        similarities = {}
        
        for user_id, user_embedding in users_result:
            user_vec = np.array(user_embedding)
            user_similarities = []
            
            for paper_id, paper_embedding in papers_result:
                paper_vec = np.array(paper_embedding)
                
                # 计算余弦相似度
                similarity = np.dot(user_vec, paper_vec) / (
                    np.linalg.norm(user_vec) * np.linalg.norm(paper_vec)
                )
                
                user_similarities.append((paper_id, similarity))
            
            # 按相似度排序
            user_similarities.sort(key=lambda x: x[1], reverse=True)
            similarities[user_id] = user_similarities
            
            print(f"    ✅ 用户 {user_id[:8]}... 相似度计算完成")
        
        return similarities

def step3_generate_recommendations(similarities, top_k=20):
    """步骤3: 生成个性化推荐"""
    print(f"\n🔄 步骤3: 生成Top-{top_k}个性化推荐")
    
    recommendations = {}
    
    for user_id, user_similarities in similarities.items():
        # 获取用户已反馈的论文
        with SessionLocal() as db:
            feedback_result = db.execute(text("""
                SELECT paper_id FROM user_feedback 
                WHERE user_id = :user_id
            """), {'user_id': user_id}).fetchall()
            
            feedback_ids = {row[0] for row in feedback_result}
        
        # 过滤已反馈论文，取top-k
        filtered_recs = [
            (paper_id, sim) for paper_id, sim in user_similarities
            if paper_id not in feedback_ids
        ][:top_k]
        
        recommendations[user_id] = filtered_recs
        print(f"    ✅ 用户 {user_id[:8]}... 推荐{len(filtered_recs)}篇论文")
    
    return recommendations

def step4_save_recommendations(recommendations):
    """步骤4: 保存推荐结果"""
    print("\n🔄 步骤4: 保存推荐结果到数据库")
    
    from datetime import date
    
    with SessionLocal() as db:
        today = date.today()
        saved_count = 0
        
        for user_id, user_recs in recommendations.items():
            if not user_recs:
                continue
            
            paper_ids = [str(paper_id) for paper_id, _ in user_recs]
            scores = [float(sim) for _, sim in user_recs]
            
            # 检查是否已存在
            existing = db.execute(text("""
                SELECT id FROM user_recommendation_pools
                WHERE user_id = :user_id AND pool_date = :date
            """), {'user_id': user_id, 'date': today}).fetchone()
            
            if existing:
                # 更新现有记录
                db.execute(text("""
                    UPDATE user_recommendation_pools
                    SET paper_ids = :paper_ids, scores = :scores, updated_at = NOW()
                    WHERE user_id = :user_id AND pool_date = :date
                """), {
                    'user_id': user_id,
                    'date': today,
                    'paper_ids': paper_ids,
                    'scores': scores
                })
            else:
                # 插入新记录
                db.execute(text("""
                    INSERT INTO user_recommendation_pools 
                    (user_id, pool_date, paper_ids, scores, created_at, updated_at)
                    VALUES (:user_id, :date, :paper_ids, :scores, NOW(), NOW())
                """), {
                    'user_id': user_id,
                    'date': today,
                    'paper_ids': paper_ids,
                    'scores': scores
                })
            
            saved_count += 1
            print(f"    ✅ 用户 {user_id[:8]}... 推荐已保存")
        
        db.commit()
        print(f"  ✅ 推荐结果保存: {saved_count}个用户")
        return saved_count

def step5_recommendation_analytics():
    """步骤5: 推荐分析和统计"""
    print("\n🔄 步骤5: 推荐分析和统计")
    
    from datetime import date
    
    with SessionLocal() as db:
        today = date.today()
        
        # 推荐统计
        stats = db.execute(text("""
            SELECT 
                COUNT(*) as total_users,
                AVG(array_length(paper_ids, 1)) as avg_recommendations,
                MIN(array_length(paper_ids, 1)) as min_recommendations,
                MAX(array_length(paper_ids, 1)) as max_recommendations,
                AVG((SELECT AVG(unnest) FROM unnest(scores))) as avg_similarity
            FROM user_recommendation_pools
            WHERE pool_date = :date
        """), {'date': today}).fetchone()
        
        if stats and stats[0]:
            print(f"  📊 推荐统计:")
            print(f"    用户数: {stats[0]}")
            print(f"    平均推荐数: {stats[1]:.1f}")
            print(f"    推荐数范围: {stats[2]} - {stats[3]}")
            print(f"    平均相似度: {stats[4]:.4f}")
            
            # 相似度分布
            similarity_dist = db.execute(text("""
                SELECT 
                    COUNT(*) FILTER (WHERE avg_score >= 0.5) as high_similarity,
                    COUNT(*) FILTER (WHERE avg_score >= 0.3 AND avg_score < 0.5) as medium_similarity,
                    COUNT(*) FILTER (WHERE avg_score < 0.3) as low_similarity
                FROM (
                    SELECT (SELECT AVG(unnest) FROM unnest(scores)) as avg_score
                    FROM user_recommendation_pools
                    WHERE pool_date = :date
                ) t
            """), {'date': today}).fetchone()
            
            if similarity_dist:
                print(f"  📈 相似度分布:")
                print(f"    高相似度(≥0.5): {similarity_dist[0]}个用户")
                print(f"    中相似度(0.3-0.5): {similarity_dist[1]}个用户")
                print(f"    低相似度(<0.3): {similarity_dist[2]}个用户")
        
        return stats

def main():
    """主流程"""
    print("🚀 开始基于Embedding的个性化推荐流水线")
    start_time = datetime.now()
    
    try:
        # 步骤1: 更新用户embedding
        users_with_embedding = step1_update_user_embeddings()
        if users_with_embedding == 0:
            print("❌ 流水线中断: 无用户embedding")
            return
        
        # 步骤2: 计算相似度
        similarities = step2_calculate_similarities()
        if not similarities:
            print("❌ 流水线中断: 相似度计算失败")
            return
        
        # 步骤3: 生成推荐
        recommendations = step3_generate_recommendations(similarities, top_k=20)
        
        # 步骤4: 保存推荐
        saved_count = step4_save_recommendations(recommendations)
        
        # 步骤5: 分析统计
        stats = step5_recommendation_analytics()
        
        # 总结
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n🎉 Embedding推荐流水线完成!")
        print(f"⏱️  总耗时: {duration}")
        print(f"📊 处理结果:")
        print(f"   - 用户embedding: {users_with_embedding}个")
        print(f"   - 推荐用户: {len(similarities)}个")
        print(f"   - 保存推荐: {saved_count}个")
        if stats and stats[0]:
            print(f"   - 平均推荐数: {stats[1]:.1f}篇")
            print(f"   - 平均相似度: {stats[4]:.4f}")
        
    except Exception as e:
        print(f"❌ 流水线异常: {e}")
        raise

if __name__ == "__main__":
    main()
