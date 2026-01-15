#!/usr/bin/env python3
"""
用户入驻流水线
1. 新用户检测和画像初始化
2. 冷启动推荐生成
3. 用户兴趣探索
4. 个性化内容推送
5. 用户行为分析和优化
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

import asyncio
from datetime import datetime, date, timedelta
from app.db.session import SessionLocal, async_session_factory
from sqlalchemy import text
import random

def step1_detect_new_users():
    """步骤1: 检测新用户并初始化画像"""
    print("🔄 步骤1: 检测新用户并初始化画像")
    
    with SessionLocal() as db:
        # 检测新注册用户 (最近7天)
        new_users = db.execute(text("""
            SELECT u.id, u.created_at
            FROM users u
            LEFT JOIN user_profiles up ON u.id = up.user_id
            WHERE u.created_at >= CURRENT_DATE - INTERVAL '7 days'
            AND up.user_id IS NULL
            ORDER BY u.created_at DESC
        """)).fetchall()
        
        print(f"  👥 检测到新用户: {len(new_users)}个")
        
        # 为新用户创建基础画像
        initialized_count = 0
        for user_id, created_at in new_users:
            try:
                # 创建用户画像
                db.execute(text("""
                    INSERT INTO user_profiles 
                    (user_id, interested_categories, research_keywords, onboarding_completed, created_at, updated_at)
                    VALUES (:user_id, '{}', '{}', false, NOW(), NOW())
                """), {'user_id': user_id})
                
                initialized_count += 1
                print(f"    ✅ 用户 {user_id[:8]}... 画像已初始化")
                
            except Exception as e:
                print(f"    ❌ 用户 {user_id[:8]}... 初始化失败: {e}")
        
        db.commit()
        print(f"  ✅ 画像初始化: {initialized_count}/{len(new_users)}个用户")
        
        return [user_id for user_id, _ in new_users]

def step2_cold_start_recommendations(new_user_ids):
    """步骤2: 冷启动推荐生成"""
    print(f"\n🔄 步骤2: 为{len(new_user_ids)}个新用户生成冷启动推荐")
    
    with SessionLocal() as db:
        # 获取热门论文 (基于用户反馈)
        popular_papers = db.execute(text("""
            SELECT p.id, COUNT(uf.id) as like_count
            FROM papers p
            JOIN user_feedback uf ON p.id = uf.paper_id
            WHERE uf.feedback_type = 'like'
            AND p.created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY p.id
            ORDER BY like_count DESC, p.created_at DESC
            LIMIT 50
        """)).fetchall()
        
        # 获取最新论文
        recent_papers = db.execute(text("""
            SELECT id FROM papers
            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
            ORDER BY created_at DESC
            LIMIT 30
        """)).fetchall()
        
        # 获取多样化类别论文
        diverse_papers = db.execute(text("""
            SELECT DISTINCT ON (primary_category) id, primary_category
            FROM papers
            WHERE created_at >= CURRENT_DATE - INTERVAL '14 days'
            AND primary_category IS NOT NULL
            ORDER BY primary_category, created_at DESC
        """)).fetchall()
        
        print(f"  📊 推荐源:")
        print(f"    - 热门论文: {len(popular_papers)}篇")
        print(f"    - 最新论文: {len(recent_papers)}篇")
        print(f"    - 多样化论文: {len(diverse_papers)}篇")
        
        # 为每个新用户生成冷启动推荐
        cold_start_count = 0
        today = date.today()
        
        for user_id in new_user_ids:
            try:
                # 组合推荐: 热门(40%) + 最新(40%) + 多样化(20%)
                recommendations = []
                
                # 热门论文 (8篇)
                popular_sample = random.sample(popular_papers, min(8, len(popular_papers)))
                recommendations.extend([p[0] for p in popular_sample])
                
                # 最新论文 (8篇)
                recent_sample = random.sample(recent_papers, min(8, len(recent_papers)))
                recommendations.extend([p[0] for p in recent_sample])
                
                # 多样化论文 (4篇)
                diverse_sample = random.sample(diverse_papers, min(4, len(diverse_papers)))
                recommendations.extend([p[0] for p in diverse_sample])
                
                # 去重并限制数量
                unique_recs = list(dict.fromkeys(recommendations))[:20]
                scores = [1.0 - (i * 0.02) for i in range(len(unique_recs))]  # 递减评分
                
                # 保存冷启动推荐
                db.execute(text("""
                    INSERT INTO user_recommendation_pools 
                    (user_id, pool_date, paper_ids, scores, created_at, updated_at)
                    VALUES (:user_id, :date, :paper_ids, :scores, NOW(), NOW())
                    ON CONFLICT (user_id, pool_date) DO UPDATE SET
                    paper_ids = EXCLUDED.paper_ids,
                    scores = EXCLUDED.scores,
                    updated_at = NOW()
                """), {
                    'user_id': user_id,
                    'date': today,
                    'paper_ids': [str(pid) for pid in unique_recs],
                    'scores': scores
                })
                
                cold_start_count += 1
                print(f"    ✅ 用户 {user_id[:8]}... 冷启动推荐已生成 ({len(unique_recs)}篇)")
                
            except Exception as e:
                print(f"    ❌ 用户 {user_id[:8]}... 冷启动推荐失败: {e}")
        
        db.commit()
        print(f"  ✅ 冷启动推荐: {cold_start_count}/{len(new_user_ids)}个用户")
        
        return cold_start_count

def step3_interest_exploration(new_user_ids):
    """步骤3: 用户兴趣探索"""
    print(f"\n🔄 步骤3: 用户兴趣探索 ({len(new_user_ids)}个用户)")
    
    with SessionLocal() as db:
        # 分析用户的初始反馈行为
        exploration_results = {}
        
        for user_id in new_user_ids:
            # 获取用户的反馈记录
            feedback_data = db.execute(text("""
                SELECT p.categories, p.primary_category, uf.feedback_type
                FROM user_feedback uf
                JOIN papers p ON uf.paper_id = p.id
                WHERE uf.user_id = :user_id
                ORDER BY uf.created_at DESC
            """), {'user_id': user_id}).fetchall()
            
            if not feedback_data:
                print(f"    ⚠️  用户 {user_id[:8]}... 暂无反馈数据")
                continue
            
            # 分析兴趣类别
            liked_categories = []
            disliked_categories = []
            
            for categories, primary_cat, feedback_type in feedback_data:
                if feedback_type == 'like':
                    if primary_cat:
                        liked_categories.append(primary_cat)
                    if categories:
                        liked_categories.extend(categories)
                elif feedback_type == 'dislike':
                    if primary_cat:
                        disliked_categories.append(primary_cat)
                    if categories:
                        disliked_categories.extend(categories)
            
            # 统计兴趣偏好
            from collections import Counter
            liked_counter = Counter(liked_categories)
            disliked_counter = Counter(disliked_categories)
            
            # 更新用户画像
            if liked_counter:
                top_interests = [cat for cat, _ in liked_counter.most_common(5)]
                
                db.execute(text("""
                    UPDATE user_profiles 
                    SET interested_categories = :categories,
                        updated_at = NOW()
                    WHERE user_id = :user_id
                """), {
                    'user_id': user_id,
                    'categories': top_interests
                })
                
                exploration_results[user_id] = {
                    'interests': top_interests,
                    'feedback_count': len(feedback_data)
                }
                
                print(f"    ✅ 用户 {user_id[:8]}... 兴趣探索完成: {', '.join(top_interests[:3])}")
            else:
                print(f"    ⚠️  用户 {user_id[:8]}... 无明确兴趣偏好")
        
        db.commit()
        print(f"  ✅ 兴趣探索: {len(exploration_results)}/{len(new_user_ids)}个用户")
        
        return exploration_results

async def step4_personalized_content_push(exploration_results):
    """步骤4: 个性化内容推送"""
    print(f"\n🔄 步骤4: 个性化内容推送 ({len(exploration_results)}个用户)")
    
    async with async_session_factory() as db:
        push_count = 0
        
        for user_id, user_data in exploration_results.items():
            interests = user_data['interests']
            
            # 基于兴趣类别推荐论文
            personalized_papers = await db.execute(text("""
                SELECT p.id, p.title
                FROM papers p
                WHERE p.primary_category = ANY(:categories)
                OR p.categories && :categories
                AND p.created_at >= CURRENT_DATE - INTERVAL '14 days'
                ORDER BY p.created_at DESC
                LIMIT 15
            """), {'categories': interests})
            
            papers = personalized_papers.fetchall()
            
            if papers:
                # 模拟推送通知
                print(f"    📱 用户 {user_id[:8]}... 推送{len(papers)}篇个性化论文")
                push_count += 1
                
                # 这里可以集成实际的推送服务
                # 例如: 邮件、短信、App推送等
            else:
                print(f"    ⚠️  用户 {user_id[:8]}... 无匹配的个性化内容")
        
        print(f"  ✅ 个性化推送: {push_count}/{len(exploration_results)}个用户")
        
        return push_count

def step5_user_behavior_analysis():
    """步骤5: 用户行为分析和优化建议"""
    print("\n🔄 步骤5: 用户行为分析和优化建议")
    
    with SessionLocal() as db:
        # 分析新用户的行为模式
        behavior_analysis = db.execute(text("""
            SELECT 
                COUNT(DISTINCT u.id) as total_new_users,
                COUNT(DISTINCT uf.user_id) as active_new_users,
                ROUND(COUNT(DISTINCT uf.user_id)::numeric / COUNT(DISTINCT u.id) * 100, 2) as activation_rate,
                AVG(feedback_counts.feedback_count) as avg_feedback_per_user
            FROM users u
            LEFT JOIN user_feedback uf ON u.id = uf.user_id
            LEFT JOIN (
                SELECT user_id, COUNT(*) as feedback_count
                FROM user_feedback
                WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY user_id
            ) feedback_counts ON u.id = feedback_counts.user_id
            WHERE u.created_at >= CURRENT_DATE - INTERVAL '7 days'
        """)).fetchone()
        
        # 分析用户留存情况
        retention_analysis = db.execute(text("""
            SELECT 
                COUNT(*) FILTER (WHERE last_activity >= CURRENT_DATE - INTERVAL '1 day') as day1_retention,
                COUNT(*) FILTER (WHERE last_activity >= CURRENT_DATE - INTERVAL '3 days') as day3_retention,
                COUNT(*) FILTER (WHERE last_activity >= CURRENT_DATE - INTERVAL '7 days') as day7_retention,
                COUNT(*) as total_users
            FROM (
                SELECT u.id, MAX(uf.created_at) as last_activity
                FROM users u
                LEFT JOIN user_feedback uf ON u.id = uf.user_id
                WHERE u.created_at >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY u.id
            ) user_activity
        """)).fetchone()
        
        # 分析推荐效果
        recommendation_effectiveness = db.execute(text("""
            SELECT 
                COUNT(*) as total_recommendations,
                COUNT(*) FILTER (WHERE uf.feedback_type = 'like') as liked_recommendations,
                ROUND(COUNT(*) FILTER (WHERE uf.feedback_type = 'like')::numeric / COUNT(*) * 100, 2) as like_rate
            FROM user_recommendation_pools urp
            JOIN unnest(urp.paper_ids) WITH ORDINALITY AS t(paper_id, ord) ON true
            LEFT JOIN user_feedback uf ON uf.user_id = urp.user_id AND uf.paper_id::text = t.paper_id
            WHERE urp.pool_date >= CURRENT_DATE - INTERVAL '7 days'
        """)).fetchone()
        
        print(f"  📊 用户行为分析:")
        
        if behavior_analysis:
            print(f"    新用户概况:")
            print(f"      - 总新用户: {behavior_analysis[0]}个")
            print(f"      - 活跃新用户: {behavior_analysis[1]}个")
            print(f"      - 激活率: {behavior_analysis[2]}%")
            print(f"      - 平均反馈数: {behavior_analysis[3]:.1f}次/用户")
        
        if retention_analysis:
            total = retention_analysis[3]
            if total > 0:
                print(f"    用户留存:")
                print(f"      - 1天留存: {retention_analysis[0]}/{total} ({retention_analysis[0]/total*100:.1f}%)")
                print(f"      - 3天留存: {retention_analysis[1]}/{total} ({retention_analysis[1]/total*100:.1f}%)")
                print(f"      - 7天留存: {retention_analysis[2]}/{total} ({retention_analysis[2]/total*100:.1f}%)")
        
        if recommendation_effectiveness and recommendation_effectiveness[0]:
            print(f"    推荐效果:")
            print(f"      - 总推荐数: {recommendation_effectiveness[0]}")
            print(f"      - 点赞数: {recommendation_effectiveness[1]}")
            print(f"      - 点赞率: {recommendation_effectiveness[2]}%")
        
        # 优化建议
        print(f"\n  💡 优化建议:")
        
        if behavior_analysis and behavior_analysis[2] < 50:
            print(f"    - 激活率偏低({behavior_analysis[2]}%)，建议优化冷启动推荐")
        
        if retention_analysis and retention_analysis[3] > 0:
            day7_rate = retention_analysis[2] / retention_analysis[3] * 100
            if day7_rate < 30:
                print(f"    - 7天留存率偏低({day7_rate:.1f}%)，建议加强用户引导")
        
        if recommendation_effectiveness and recommendation_effectiveness[2] < 20:
            print(f"    - 推荐点赞率偏低({recommendation_effectiveness[2]}%)，建议优化推荐算法")
        
        return {
            'behavior': behavior_analysis,
            'retention': retention_analysis,
            'recommendation': recommendation_effectiveness
        }

def main():
    """主流程"""
    print("🚀 开始用户入驻流水线")
    start_time = datetime.now()
    
    try:
        # 步骤1: 检测新用户
        new_user_ids = step1_detect_new_users()
        
        if not new_user_ids:
            print("⚠️  无新用户需要处理")
            # 仍然执行行为分析
            step5_user_behavior_analysis()
            return
        
        # 步骤2: 冷启动推荐
        cold_start_count = step2_cold_start_recommendations(new_user_ids)
        
        # 步骤3: 兴趣探索
        exploration_results = step3_interest_exploration(new_user_ids)
        
        # 步骤4: 个性化推送
        push_count = asyncio.run(step4_personalized_content_push(exploration_results))
        
        # 步骤5: 行为分析
        analytics = step5_user_behavior_analysis()
        
        # 总结
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n🎉 用户入驻流水线完成!")
        print(f"⏱️  总耗时: {duration}")
        print(f"📊 处理结果:")
        print(f"   - 新用户: {len(new_user_ids)}个")
        print(f"   - 冷启动推荐: {cold_start_count}个用户")
        print(f"   - 兴趣探索: {len(exploration_results)}个用户")
        print(f"   - 个性化推送: {push_count}个用户")
        
        if analytics['behavior']:
            print(f"   - 激活率: {analytics['behavior'][2]}%")
        
    except Exception as e:
        print(f"❌ 用户入驻流水线异常: {e}")
        raise

if __name__ == "__main__":
    main()
