#!/usr/bin/env python3
"""
为所有用户生成推荐池
基于CS候选池为每个用户生成个性化推荐
"""
import sys
from pathlib import Path
backend_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_root))

import pendulum
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User
from app.services.data_ingestion.arxiv_candidate_pool import CandidatePoolServiceV2
from app.services.recommendation.user_ranking_service import UserRankingService
from app.services.recommendation.recommendation_facade import RecommendationFacade

def generate_recommendations_for_all_users():
    print('=== 为所有用户生成推荐池 ===')
    
    # 动态计算目标日期 (使用 T-3 延迟)
    from app.core.config import settings
    from datetime import timedelta
    target_date = (pendulum.now('America/New_York').date() 
                   - timedelta(days=settings.arxiv_submission_delay_days))
    print(f'📅 目标日期: {target_date} (T-{settings.arxiv_submission_delay_days})')
    
    db = SessionLocal()
    
    try:
        # 获取所有用户
        users = db.query(User).all()
        print(f'📋 找到 {len(users)} 个用户')
        
        # 获取CS候选池
        cs_paper_ids = CandidatePoolServiceV2.get_candidate_papers_by_date(
            session=db,
            target_date=target_date,
            filter_type='cs'
        )
        print(f'📋 CS候选池: {len(cs_paper_ids)} 篇论文')
        
        if not cs_paper_ids:
            print('❌ 未找到CS候选池')
            return
        
        # 初始化服务
        ranking_service = UserRankingService(db)
        facade = RecommendationFacade(db)
        success_count = 0
        
        for user in users:
            try:
                print(f'\n👤 处理用户: {user.id}')
                
                # 先生成排序表
                source_key = f'arxiv_cs_{target_date}'
                ranking_success = ranking_service.update_user_ranking(
                    user_id=user.id,
                    source_key=source_key,
                    paper_ids=cs_paper_ids,
                    force_update=True
                )
                
                if not ranking_success:
                    print(f'   ❌ 排序表生成失败')
                    continue
                
                print(f'   ✅ 排序表生成成功')
                
                # 生成推荐池 (使用10%比例)
                recommendations = facade.get_user_recommendations(
                    user_id=user.id,
                    source_key=source_key,
                    pool_ratio=0.1
                )
                
                if recommendations:
                    print(f'   ✅ 生成推荐: {len(recommendations)} 篇')
                    success_count += 1
                else:
                    print(f'   ⚠️  推荐为空')
                    
            except Exception as e:
                print(f'   ❌ 失败: {e}')
        
        print(f'\n📊 处理结果:')
        print(f'总用户数: {len(users)}')
        print(f'成功生成推荐: {success_count}')
        print(f'成功率: {success_count/len(users)*100:.1f}%')
        
    except Exception as e:
        print(f'❌ 执行失败: {e}')
    finally:
        db.close()

if __name__ == "__main__":
    generate_recommendations_for_all_users()
