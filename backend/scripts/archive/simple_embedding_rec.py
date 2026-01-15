#!/usr/bin/env python3

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from sqlalchemy import text
import numpy as np

def get_user_embedding_from_feedback(user_id: str):
    """从用户反馈直接计算embedding"""
    with SessionLocal() as db:
        # 获取用户点赞论文的embeddings
        result = db.execute(text("""
            SELECT pe.vector 
            FROM user_feedback uf
            JOIN papers p ON uf.paper_id = p.id
            JOIN paper_embeddings pe ON p.id = pe.paper_id
            WHERE uf.user_id = :user_id 
            AND uf.feedback_type = 'like'
            AND pe.vector IS NOT NULL
        """), {'user_id': user_id}).fetchall()
        
        if not result:
            return None
            
        vectors = [np.array(row[0]) for row in result]
        return np.mean(vectors, axis=0)

def recommend_papers(user_id: str, limit: int = 10):
    """基于embedding相似度推荐论文"""
    
    # 计算用户embedding
    user_embedding = get_user_embedding_from_feedback(user_id)
    if user_embedding is None:
        print(f"❌ 用户 {user_id} 没有点赞论文")
        return []
    
    print(f"✅ 用户embedding维度: {len(user_embedding)}")
    
    with SessionLocal() as db:
        # 获取候选池中未反馈的论文
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
        
        if not papers_result:
            print("❌ 没有可推荐的论文")
            return []
        
        # 计算相似度
        similarities = []
        for paper_id, title, paper_embedding in papers_result:
            paper_vec = np.array(paper_embedding)
            
            # 余弦相似度
            similarity = np.dot(user_embedding, paper_vec) / (
                np.linalg.norm(user_embedding) * np.linalg.norm(paper_vec)
            )
            
            similarities.append((paper_id, title, similarity))
        
        # 排序并返回top N
        similarities.sort(key=lambda x: x[2], reverse=True)
        recommendations = similarities[:limit]
        
        print(f"\n🎯 推荐结果:")
        for i, (paper_id, title, sim) in enumerate(recommendations, 1):
            print(f"  {i}. {title[:60]}... (相似度: {sim:.4f})")
        
        return [paper_id for paper_id, _, _ in recommendations]

if __name__ == "__main__":
    user_id = 'aa1d030e-a686-40af-834c-aad4c1f5165a'
    recommendations = recommend_papers(user_id, 10)
    print(f"\n✅ 生成了 {len(recommendations)} 个推荐")
