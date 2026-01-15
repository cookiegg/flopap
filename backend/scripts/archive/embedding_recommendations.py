#!/usr/bin/env python3

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from sqlalchemy import text
import numpy as np

def get_embedding_recommendations(user_id: str, limit: int = 10):
    """基于embedding相似度的推荐算法"""
    
    with SessionLocal() as db:
        # 获取用户embedding
        user_result = db.execute(text("""
            SELECT embedding FROM user_profiles 
            WHERE user_id = :user_id AND embedding IS NOT NULL
        """), {'user_id': user_id}).fetchone()
        
        if not user_result:
            print(f"❌ 用户 {user_id} 没有embedding")
            return []
        
        user_embedding = np.array(user_result[0])
        
        # 获取候选池论文的embeddings
        papers_result = db.execute(text("""
            SELECT p.id, p.title, pe.vector
            FROM papers p
            JOIN paper_embeddings pe ON p.id = pe.paper_id
            JOIN candidate_pools cp ON p.id = cp.paper_id
            WHERE pe.vector IS NOT NULL
            AND p.id NOT IN (
                SELECT paper_id FROM user_feedback 
                WHERE user_id = :user_id
            )
        """), {'user_id': user_id}).fetchall()
        
        print(f"📊 候选论文: {len(papers_result)}篇")
        
        # 计算相似度
        similarities = []
        for paper_id, title, paper_embedding in papers_result:
            paper_vec = np.array(paper_embedding)
            
            # 计算余弦相似度
            similarity = np.dot(user_embedding, paper_vec) / (
                np.linalg.norm(user_embedding) * np.linalg.norm(paper_vec)
            )
            
            similarities.append((paper_id, title, similarity))
        
        # 按相似度排序
        similarities.sort(key=lambda x: x[2], reverse=True)
        
        # 返回top N
        recommendations = similarities[:limit]
        
        print(f"🎯 推荐结果 (top {len(recommendations)}):")
        for i, (paper_id, title, sim) in enumerate(recommendations, 1):
            print(f"  {i}. {title[:60]}... (相似度: {sim:.4f})")
        
        return [paper_id for paper_id, _, _ in recommendations]

if __name__ == "__main__":
    user_id = 'aa1d030e-a686-40af-834c-aad4c1f5165a'
    recommendations = get_embedding_recommendations(user_id, 10)
    print(f"\n✅ 为用户 {user_id} 生成了 {len(recommendations)} 个推荐")
