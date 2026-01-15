#!/usr/bin/env python3

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from sqlalchemy import text
import numpy as np

def generate_user_embedding(user_id: str):
    with SessionLocal() as db:
        try:
            # 获取用户点赞论文的embeddings
            result = db.execute(text("""
                SELECT pe.vector 
                FROM user_feedback uf
                JOIN papers p ON uf.paper_id = p.id
                JOIN paper_embeddings pe ON p.id = pe.paper_id
                WHERE uf.user_id = :user_id 
                AND uf.feedback_type = 'like'
                AND pe.vector IS NOT NULL
            """), {'user_id': user_id})
            
            vectors = []
            for row in result:
                vectors.append(np.array(row[0]))
            
            if not vectors:
                print(f"❌ 用户 {user_id} 没有点赞论文")
                return False
            
            # 计算平均embedding
            user_embedding = np.mean(vectors, axis=0).tolist()
            
            # 更新user_profiles
            db.execute(text("""
                UPDATE user_profiles 
                SET embedding = :embedding
                WHERE user_id = :user_id
            """), {
                'user_id': user_id,
                'embedding': user_embedding
            })
            
            db.commit()
            print(f"✅ 用户 {user_id} embedding已生成 (基于{len(vectors)}篇论文)")
            return True
            
        except Exception as e:
            db.rollback()
            print(f"❌ 生成失败: {e}")
            return False

if __name__ == "__main__":
    user_id = 'aa1d030e-a686-40af-834c-aad4c1f5165a'
    generate_user_embedding(user_id)
