#!/usr/bin/env python3
"""
日常维护流水线
1. 数据质量检查
2. 过期数据清理
3. 推荐池更新
4. 系统健康检查
5. 性能统计报告
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from datetime import datetime, date, timedelta
from app.db.session import SessionLocal
from sqlalchemy import text

def step1_data_quality_check():
    """步骤1: 数据质量检查"""
    print("🔄 步骤1: 数据质量检查")
    
    issues = []
    
    with SessionLocal() as db:
        # 检查论文数据完整性
        paper_issues = db.execute(text("""
            SELECT 
                COUNT(*) FILTER (WHERE title IS NULL OR title = '') as missing_title,
                COUNT(*) FILTER (WHERE summary IS NULL OR summary = '') as missing_summary,
                COUNT(*) FILTER (WHERE authors IS NULL OR array_length(authors, 1) = 0) as missing_authors,
                COUNT(*) FILTER (WHERE categories IS NULL OR array_length(categories, 1) = 0) as missing_categories
            FROM papers
            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
        """)).fetchone()
        
        if paper_issues:
            if paper_issues[0] > 0:
                issues.append(f"缺少标题的论文: {paper_issues[0]}篇")
            if paper_issues[1] > 0:
                issues.append(f"缺少摘要的论文: {paper_issues[1]}篇")
            if paper_issues[2] > 0:
                issues.append(f"缺少作者的论文: {paper_issues[2]}篇")
            if paper_issues[3] > 0:
                issues.append(f"缺少类别的论文: {paper_issues[3]}篇")
        
        # 检查embedding覆盖率
        embedding_coverage = db.execute(text("""
            SELECT 
                COUNT(p.id) as total_papers,
                COUNT(pe.id) as papers_with_embedding,
                ROUND(COUNT(pe.id)::numeric / COUNT(p.id) * 100, 2) as coverage_rate
            FROM papers p
            LEFT JOIN paper_embeddings pe ON p.id = pe.paper_id
            WHERE p.created_at >= CURRENT_DATE - INTERVAL '7 days'
        """)).fetchone()
        
        if embedding_coverage:
            coverage_rate = embedding_coverage[2] or 0
            print(f"  📊 Embedding覆盖率: {coverage_rate}% ({embedding_coverage[1]}/{embedding_coverage[0]})")
            if coverage_rate < 95:
                issues.append(f"Embedding覆盖率过低: {coverage_rate}%")
        
        # 检查翻译覆盖率
        translation_coverage = db.execute(text("""
            SELECT 
                COUNT(p.id) as total_papers,
                COUNT(pt.id) as papers_with_translation,
                ROUND(COUNT(pt.id)::numeric / COUNT(p.id) * 100, 2) as coverage_rate
            FROM papers p
            LEFT JOIN paper_translations pt ON p.id = pt.paper_id
            WHERE p.created_at >= CURRENT_DATE - INTERVAL '7 days'
        """)).fetchone()
        
        if translation_coverage:
            coverage_rate = translation_coverage[2] or 0
            print(f"  📊 翻译覆盖率: {coverage_rate}% ({translation_coverage[1]}/{translation_coverage[0]})")
            if coverage_rate < 80:
                issues.append(f"翻译覆盖率过低: {coverage_rate}%")
    
    if issues:
        print(f"  ⚠️  发现{len(issues)}个数据质量问题:")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print("  ✅ 数据质量检查通过")
    
    return issues

def step2_cleanup_expired_data():
    """步骤2: 清理过期数据"""
    print("\n🔄 步骤2: 清理过期数据")
    
    with SessionLocal() as db:
        # 清理30天前的推荐池
        cutoff_date = date.today() - timedelta(days=30)
        
        deleted_pools = db.execute(text("""
            DELETE FROM daily_recommendation_pool 
            WHERE pool_date < :cutoff_date
        """), {'cutoff_date': cutoff_date}).rowcount
        
        deleted_user_pools = db.execute(text("""
            DELETE FROM user_recommendation_pools 
            WHERE pool_date < :cutoff_date
        """), {'cutoff_date': cutoff_date}).rowcount
        
        # 清理90天前的用户活动记录
        activity_cutoff = datetime.now() - timedelta(days=90)
        deleted_activities = db.execute(text("""
            DELETE FROM user_activity 
            WHERE created_at < :cutoff_date
        """), {'cutoff_date': activity_cutoff}).rowcount
        
        db.commit()
        
        print(f"  ✅ 清理完成:")
        print(f"    - 推荐池: {deleted_pools}条")
        print(f"    - 用户推荐池: {deleted_user_pools}条")
        print(f"    - 用户活动: {deleted_activities}条")
        
        return deleted_pools + deleted_user_pools + deleted_activities

def step3_update_recommendation_pools():
    """步骤3: 更新推荐池"""
    print("\n🔄 步骤3: 更新推荐池")
    
    from app.services.recommendation import generate_personalized_pool
    
    with SessionLocal() as db:
        # 获取活跃用户列表
        active_users = db.execute(text("""
            SELECT DISTINCT user_id 
            FROM user_feedback 
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
        """)).fetchall()
        
        print(f"  👥 活跃用户: {len(active_users)}个")
        
        updated_count = 0
        for user_row in active_users:
            user_id = user_row[0]
            try:
                # 为每个活跃用户生成推荐池
                entries = generate_personalized_pool(db, user_id=user_id)
                if entries:
                    updated_count += 1
                    print(f"    ✅ 用户 {user_id[:8]}... 推荐池已更新 ({len(entries)}篇)")
            except Exception as e:
                print(f"    ❌ 用户 {user_id[:8]}... 更新失败: {e}")
        
        print(f"  ✅ 推荐池更新: {updated_count}/{len(active_users)}个用户")
        return updated_count

def step4_system_health_check():
    """步骤4: 系统健康检查"""
    print("\n🔄 步骤4: 系统健康检查")
    
    health_issues = []
    
    with SessionLocal() as db:
        # 检查数据库连接
        try:
            db.execute(text("SELECT 1")).fetchone()
            print("  ✅ 数据库连接正常")
        except Exception as e:
            health_issues.append(f"数据库连接异常: {e}")
        
        # 检查关键表的记录数
        table_counts = db.execute(text("""
            SELECT 
                (SELECT COUNT(*) FROM papers) as papers,
                (SELECT COUNT(*) FROM paper_embeddings) as embeddings,
                (SELECT COUNT(*) FROM candidate_pools) as candidates,
                (SELECT COUNT(*) FROM user_feedback) as feedback,
                (SELECT COUNT(*) FROM user_profiles) as profiles
        """)).fetchone()
        
        if table_counts:
            print(f"  📊 数据表统计:")
            print(f"    - 论文: {table_counts[0]:,}篇")
            print(f"    - Embeddings: {table_counts[1]:,}个")
            print(f"    - 候选池: {table_counts[2]:,}篇")
            print(f"    - 用户反馈: {table_counts[3]:,}条")
            print(f"    - 用户画像: {table_counts[4]:,}个")
            
            # 检查异常情况
            if table_counts[0] == 0:
                health_issues.append("论文表为空")
            if table_counts[1] / table_counts[0] < 0.8:
                health_issues.append("Embedding覆盖率过低")
        
        # 检查最近的数据摄取
        recent_ingestion = db.execute(text("""
            SELECT MAX(created_at) as last_ingestion
            FROM ingestion_batches
        """)).fetchone()
        
        if recent_ingestion and recent_ingestion[0]:
            days_since = (datetime.now() - recent_ingestion[0]).days
            print(f"  📅 最近数据摄取: {days_since}天前")
            if days_since > 2:
                health_issues.append(f"数据摄取过期: {days_since}天前")
        else:
            health_issues.append("无数据摄取记录")
    
    if health_issues:
        print(f"  ⚠️  发现{len(health_issues)}个健康问题:")
        for issue in health_issues:
            print(f"    - {issue}")
    else:
        print("  ✅ 系统健康检查通过")
    
    return health_issues

def step5_performance_report():
    """步骤5: 性能统计报告"""
    print("\n🔄 步骤5: 性能统计报告")
    
    with SessionLocal() as db:
        # 用户活跃度统计
        user_activity = db.execute(text("""
            SELECT 
                COUNT(DISTINCT user_id) FILTER (WHERE created_at >= CURRENT_DATE) as daily_active,
                COUNT(DISTINCT user_id) FILTER (WHERE created_at >= CURRENT_DATE - INTERVAL '7 days') as weekly_active,
                COUNT(DISTINCT user_id) FILTER (WHERE created_at >= CURRENT_DATE - INTERVAL '30 days') as monthly_active
            FROM user_feedback
        """)).fetchone()
        
        # 推荐效果统计
        recommendation_stats = db.execute(text("""
            SELECT 
                COUNT(*) as total_recommendations,
                COUNT(*) FILTER (WHERE feedback_type = 'like') as liked_recommendations,
                ROUND(COUNT(*) FILTER (WHERE feedback_type = 'like')::numeric / COUNT(*) * 100, 2) as like_rate
            FROM user_feedback uf
            JOIN daily_recommendation_pool drp ON uf.paper_id = drp.paper_id
            WHERE uf.created_at >= CURRENT_DATE - INTERVAL '7 days'
        """)).fetchone()
        
        # 内容生成统计
        content_stats = db.execute(text("""
            SELECT 
                COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE - INTERVAL '7 days') as weekly_papers,
                COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE - INTERVAL '7 days' AND id IN (
                    SELECT paper_id FROM paper_translations
                )) as weekly_translated,
                COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE - INTERVAL '7 days' AND id IN (
                    SELECT paper_id FROM paper_interpretations
                )) as weekly_interpreted
            FROM papers
        """)).fetchone()
        
        print(f"  📈 性能报告:")
        
        if user_activity:
            print(f"    用户活跃度:")
            print(f"      - 日活跃: {user_activity[0]}人")
            print(f"      - 周活跃: {user_activity[1]}人")
            print(f"      - 月活跃: {user_activity[2]}人")
        
        if recommendation_stats and recommendation_stats[0]:
            print(f"    推荐效果 (近7天):")
            print(f"      - 总推荐: {recommendation_stats[0]}次")
            print(f"      - 点赞数: {recommendation_stats[1]}次")
            print(f"      - 点赞率: {recommendation_stats[2]}%")
        
        if content_stats:
            print(f"    内容生成 (近7天):")
            print(f"      - 新论文: {content_stats[0]}篇")
            print(f"      - 已翻译: {content_stats[1]}篇")
            print(f"      - 已解读: {content_stats[2]}篇")
        
        return {
            'user_activity': user_activity,
            'recommendation_stats': recommendation_stats,
            'content_stats': content_stats
        }

def main():
    """主流程"""
    print("🚀 开始日常维护流水线")
    start_time = datetime.now()
    
    try:
        # 步骤1: 数据质量检查
        data_issues = step1_data_quality_check()
        
        # 步骤2: 清理过期数据
        cleaned_records = step2_cleanup_expired_data()
        
        # 步骤3: 更新推荐池
        updated_users = step3_update_recommendation_pools()
        
        # 步骤4: 系统健康检查
        health_issues = step4_system_health_check()
        
        # 步骤5: 性能报告
        performance_stats = step5_performance_report()
        
        # 总结
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n🎉 日常维护流水线完成!")
        print(f"⏱️  总耗时: {duration}")
        print(f"📊 维护结果:")
        print(f"   - 数据质量问题: {len(data_issues)}个")
        print(f"   - 清理记录: {cleaned_records}条")
        print(f"   - 更新推荐池: {updated_users}个用户")
        print(f"   - 系统健康问题: {len(health_issues)}个")
        
        # 健康状态总结
        if not data_issues and not health_issues:
            print("✅ 系统运行正常")
        else:
            print("⚠️  系统存在问题，需要关注")
        
    except Exception as e:
        print(f"❌ 维护流水线异常: {e}")
        raise

if __name__ == "__main__":
    main()
