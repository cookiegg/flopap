#!/usr/bin/env python3
"""
验证用户推荐池生成情况
检查所有用户的排序表和推荐池状态
"""
import sys
from pathlib import Path
backend_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_root))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User
from app.models.user_paper_ranking import UserPaperRanking

def verify_user_recommendations():
    print('=== 验证用户推荐池生成情况 ===')
    
    db = SessionLocal()
    
    try:
        # 获取所有用户
        users = db.query(User).all()
        print(f'📋 总用户数: {len(users)}')
        
        # 检查每个用户的排序表
        for user in users:
            rankings = db.query(UserPaperRanking).filter(
                UserPaperRanking.user_id == user.id
            ).all()
            
            print(f'\n👤 用户: {user.id}')
            print(f'   排序表数量: {len(rankings)}')
            
            for ranking in rankings:
                print(f'   📊 数据源: {ranking.source_key}')
                print(f'      论文数量: {len(ranking.paper_ids)}')
                print(f'      生成日期: {ranking.pool_date}')
                
                # 计算推荐池大小 (10%)
                pool_size = int(len(ranking.paper_ids) * 0.1)
                print(f'      推荐池大小: {pool_size} 篇')
        
        print(f'\n✅ 验证完成')
        
    except Exception as e:
        print(f'❌ 验证失败: {e}')
    finally:
        db.close()

if __name__ == "__main__":
    verify_user_recommendations()
