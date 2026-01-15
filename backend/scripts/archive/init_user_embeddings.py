#!/usr/bin/env python3

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from sqlalchemy import text
import numpy as np
import uuid

def init_user_embeddings():
    with SessionLocal() as db:
        # 获取所有有反馈的用户
        users = db.execute(text('SELECT DISTINCT user_id FROM user_feedback')).fetchall()
        
        for user_row in users:
            user_id = user_row[0]
            print(f"🎯 处理用户: {user_id}")
            
            # 检查用户是否已存在于user_profiles
            existing = db.execute(text('SELECT user_id FROM user_profiles WHERE user_id = :user_id'), 
                                {'user_id': user_id}).fetchone()
            
            if not existing:
                # 创建用户profile
                db.execute(text("""
                    INSERT INTO user_profiles (user_id, interested_categories, research_keywords, onboarding_completed, created_at, updated_at)
                    VALUES (:user_id, '{}', '{}', false, NOW(), NOW())
                """), {
                    'user_id': user_id
                })
                print(f"  ✅ 创建用户profile")
            
            # 生成用户embedding
            vectors_result = db.execute(text("""
                SELECT pe.vector 
                FROM user_feedback uf
                JOIN papers p ON uf.paper_id = p.id
                JOIN paper_embeddings pe ON p.id = pe.paper_id
                WHERE uf.user_id = :user_id 
                AND uf.feedback_type = 'like'
                AND pe.vector IS NOT NULL
            """), {'user_id': user_id})
            
            vectors = [np.array(row[0]) for row in vectors_result]
            
            if vectors:
                user_embedding = np.mean(vectors, axis=0).tolist()
                
                db.execute(text("""
                    UPDATE user_profiles 
                    SET embedding = :embedding, updated_at = NOW()
                    WHERE user_id = :user_id
                """), {
                    'user_id': user_id,
                    'embedding': user_embedding
                })
                
                print(f"  ✅ 生成embedding (基于{len(vectors)}篇论文)")
            else:
                print(f"  ⚠️  无点赞论文，跳过embedding生成")
        
        db.commit()
        print(f"\n🎉 完成! 处理了{len(users)}个用户")

if __name__ == "__main__":
    init_user_embeddings()
