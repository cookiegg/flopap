#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import numpy as np
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update
from backend.models import UserProfile, Paper, UserFeedback
from backend.config import DATABASE_URL

async def generate_user_embeddings():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 获取所有有反馈的用户
        result = await session.execute(
            select(UserFeedback.user_id).distinct()
        )
        user_ids = [row[0] for row in result.fetchall()]
        
        for user_id in user_ids:
            # 获取用户的正面反馈论文
            result = await session.execute(
                select(Paper.embedding).join(UserFeedback).where(
                    UserFeedback.user_id == user_id,
                    UserFeedback.feedback_type == 'like',
                    Paper.embedding.isnot(None)
                )
            )
            embeddings = [row[0] for row in result.fetchall()]
            
            if embeddings:
                # 计算平均embedding
                avg_embedding = np.mean(embeddings, axis=0).tolist()
                
                # 更新用户embedding
                await session.execute(
                    update(UserProfile).where(UserProfile.user_id == user_id)
                    .values(embedding=avg_embedding)
                )
                print(f"✅ 用户 {user_id} embedding已生成 (基于{len(embeddings)}篇论文)")
        
        await session.commit()

if __name__ == "__main__":
    asyncio.run(generate_user_embeddings())
