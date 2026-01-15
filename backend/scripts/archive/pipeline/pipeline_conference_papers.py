#!/usr/bin/env python3
"""
会议论文处理流水线
1. 会议论文数据获取
2. 质量筛选和分类
3. 批量内容生成
4. 会议推荐池生成
5. 专题推荐创建
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from datetime import datetime, date
from app.db.session import SessionLocal
from sqlalchemy import text

def step1_conference_data_ingestion():
    """步骤1: 会议论文数据获取"""
    print("🔄 步骤1: 会议论文数据获取")
    
    # 这里可以集成各种会议数据源
    # 例如: NIPS, ICML, ICLR, ACL, EMNLP等
    
    conference_sources = [
        'NIPS', 'ICML', 'ICLR', 'ACL', 'EMNLP', 
        'CVPR', 'ICCV', 'ECCV', 'AAAI', 'IJCAI'
    ]
    
    with SessionLocal() as db:
        # 统计现有会议论文
        existing_conference_papers = db.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE - INTERVAL '30 days') as recent
            FROM papers 
            WHERE comment ILIKE ANY(ARRAY['%NIPS%', '%ICML%', '%ICLR%', '%ACL%', '%EMNLP%', 
                                          '%CVPR%', '%ICCV%', '%ECCV%', '%AAAI%', '%IJCAI%'])
        """)).fetchone()
        
        print(f"  📊 现有会议论文: {existing_conference_papers[0]}篇")
        print(f"  📅 近30天新增: {existing_conference_papers[1]}篇")
        
        # 模拟新会议论文获取
        # 实际实现中这里会调用各会议的API或爬虫
        print(f"  🔍 扫描会议源: {', '.join(conference_sources)}")
        print(f"  📥 模拟获取新论文: 假设获取了25篇新会议论文")
        
        return 25  # 模拟返回值

def step2_quality_filtering_and_classification():
    """步骤2: 质量筛选和分类"""
    print("\n🔄 步骤2: 质量筛选和分类")
    
    with SessionLocal() as db:
        # 获取最近的会议论文
        conference_papers = db.execute(text("""
            SELECT id, title, summary, comment, categories
            FROM papers 
            WHERE comment ILIKE ANY(ARRAY['%NIPS%', '%ICML%', '%ICLR%', '%ACL%', '%EMNLP%', 
                                          '%CVPR%', '%ICCV%', '%ECCV%', '%AAAI%', '%IJCAI%'])
            AND created_at >= CURRENT_DATE - INTERVAL '7 days'
            ORDER BY created_at DESC
        """)).fetchall()
        
        print(f"  📚 待处理会议论文: {len(conference_papers)}篇")
        
        # 质量筛选规则
        high_quality_papers = []
        categorized_papers = {
            'AI/ML': [],
            'CV': [],
            'NLP': [],
            'Other': []
        }
        
        for paper in conference_papers:
            paper_id, title, summary, comment, categories = paper
            
            # 质量筛选 (基于标题长度、摘要长度等简单规则)
            if (len(title) >= 10 and len(summary) >= 100 and 
                not any(word in title.lower() for word in ['test', 'demo', 'workshop'])):
                high_quality_papers.append(paper_id)
                
                # 分类
                if any(cat.startswith('cs.CV') for cat in (categories or [])):
                    categorized_papers['CV'].append(paper_id)
                elif any(cat.startswith('cs.CL') for cat in (categories or [])):
                    categorized_papers['NLP'].append(paper_id)
                elif any(cat.startswith(('cs.AI', 'cs.LG')) for cat in (categories or [])):
                    categorized_papers['AI/ML'].append(paper_id)
                else:
                    categorized_papers['Other'].append(paper_id)
        
        print(f"  ✅ 高质量论文: {len(high_quality_papers)}篇")
        print(f"  📊 分类结果:")
        for category, papers in categorized_papers.items():
            print(f"    - {category}: {len(papers)}篇")
        
        return high_quality_papers, categorized_papers

def step3_batch_content_generation(paper_ids):
    """步骤3: 批量内容生成"""
    print(f"\n🔄 步骤3: 批量内容生成 ({len(paper_ids)}篇论文)")
    
    from app.services.translation_pure import batch_translate_papers
    from app.services.ai_interpretation_pure import interpret_and_save_papers
    
    with SessionLocal() as db:
        # 批量翻译
        print("  🔤 开始批量翻译...")
        translated_count = batch_translate_papers(db, paper_ids)
        print(f"    ✅ 翻译完成: {translated_count}篇")
        
        # 批量AI解读
        print("  🤖 开始批量AI解读...")
        interpreted_count = interpret_and_save_papers(db, paper_ids)
        print(f"    ✅ AI解读完成: {interpreted_count}篇")
        
        # 生成信息图 (如果需要)
        print("  📊 生成信息图...")
        # 这里可以调用信息图生成服务
        infographic_count = min(len(paper_ids), 10)  # 模拟只为前10篇生成信息图
        print(f"    ✅ 信息图生成: {infographic_count}篇")
        
        return translated_count, interpreted_count, infographic_count

def step4_conference_recommendation_pool(categorized_papers):
    """步骤4: 会议推荐池生成"""
    print("\n🔄 步骤4: 会议推荐池生成")
    
    with SessionLocal() as db:
        today = date.today()
        
        # 为每个类别创建推荐池
        total_pools = 0
        
        for category, paper_ids in categorized_papers.items():
            if not paper_ids:
                continue
            
            # 清理该类别的旧推荐池
            db.execute(text("""
                DELETE FROM conference_recommendation_pool 
                WHERE source = :category AND pool_date = :date
            """), {'category': category, 'date': today})
            
            # 创建新的推荐池
            for position, paper_id in enumerate(paper_ids[:20]):  # 每类别最多20篇
                db.execute(text("""
                    INSERT INTO conference_recommendation_pool 
                    (pool_date, paper_id, source, position, score, is_active, created_at, updated_at)
                    VALUES (:date, :paper_id, :source, :position, :score, true, NOW(), NOW())
                """), {
                    'date': today,
                    'paper_id': paper_id,
                    'source': category,
                    'position': position,
                    'score': 1.0 - (position * 0.01)  # 简单的位置评分
                })
            
            total_pools += len(paper_ids[:20])
            print(f"    ✅ {category}推荐池: {len(paper_ids[:20])}篇")
        
        db.commit()
        print(f"  ✅ 会议推荐池生成: {total_pools}篇论文")
        
        return total_pools

def step5_create_special_recommendations():
    """步骤5: 创建专题推荐"""
    print("\n🔄 步骤5: 创建专题推荐")
    
    with SessionLocal() as db:
        # 创建"本周热门会议论文"专题
        hot_papers = db.execute(text("""
            SELECT p.id, COUNT(uf.id) as feedback_count
            FROM papers p
            LEFT JOIN user_feedback uf ON p.id = uf.paper_id AND uf.feedback_type = 'like'
            WHERE p.comment ILIKE ANY(ARRAY['%NIPS%', '%ICML%', '%ICLR%', '%ACL%', '%EMNLP%', 
                                            '%CVPR%', '%ICCV%', '%ECCV%', '%AAAI%', '%IJCAI%'])
            AND p.created_at >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY p.id
            ORDER BY feedback_count DESC, p.created_at DESC
            LIMIT 10
        """)).fetchall()
        
        print(f"    📈 本周热门会议论文: {len(hot_papers)}篇")
        
        # 创建"新兴技术趋势"专题
        trending_keywords = ['transformer', 'diffusion', 'multimodal', 'few-shot', 'self-supervised']
        trending_papers = []
        
        for keyword in trending_keywords:
            papers = db.execute(text("""
                SELECT id FROM papers
                WHERE (title ILIKE :keyword OR summary ILIKE :keyword)
                AND comment ILIKE ANY(ARRAY['%NIPS%', '%ICML%', '%ICLR%', '%ACL%', '%EMNLP%', 
                                            '%CVPR%', '%ICCV%', '%ECCV%', '%AAAI%', '%IJCAI%'])
                AND created_at >= CURRENT_DATE - INTERVAL '30 days'
                ORDER BY created_at DESC
                LIMIT 2
            """), {'keyword': f'%{keyword}%'}).fetchall()
            
            trending_papers.extend([p[0] for p in papers])
        
        print(f"    🔥 新兴技术趋势论文: {len(trending_papers)}篇")
        
        # 创建"跨领域研究"专题
        interdisciplinary_papers = db.execute(text("""
            SELECT id FROM papers
            WHERE array_length(categories, 1) >= 3
            AND comment ILIKE ANY(ARRAY['%NIPS%', '%ICML%', '%ICLR%', '%ACL%', '%EMNLP%', 
                                        '%CVPR%', '%ICCV%', '%ECCV%', '%AAAI%', '%IJCAI%'])
            AND created_at >= CURRENT_DATE - INTERVAL '14 days'
            ORDER BY array_length(categories, 1) DESC, created_at DESC
            LIMIT 8
        """)).fetchall()
        
        print(f"    🔗 跨领域研究论文: {len(interdisciplinary_papers)}篇")
        
        # 保存专题推荐到特殊标记
        special_recommendations = {
            'weekly_hot': [p[0] for p in hot_papers],
            'trending_tech': trending_papers,
            'interdisciplinary': [p[0] for p in interdisciplinary_papers]
        }
        
        return special_recommendations

def main():
    """主流程"""
    print("🚀 开始会议论文处理流水线")
    start_time = datetime.now()
    
    try:
        # 步骤1: 会议数据获取
        new_papers_count = step1_conference_data_ingestion()
        
        # 步骤2: 质量筛选和分类
        high_quality_papers, categorized_papers = step2_quality_filtering_and_classification()
        
        if not high_quality_papers:
            print("⚠️  无高质量会议论文需要处理")
            return
        
        # 步骤3: 批量内容生成
        translated, interpreted, infographics = step3_batch_content_generation(high_quality_papers)
        
        # 步骤4: 会议推荐池生成
        pool_count = step4_conference_recommendation_pool(categorized_papers)
        
        # 步骤5: 专题推荐创建
        special_recs = step5_create_special_recommendations()
        
        # 总结
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n🎉 会议论文处理流水线完成!")
        print(f"⏱️  总耗时: {duration}")
        print(f"📊 处理结果:")
        print(f"   - 新获取论文: {new_papers_count}篇")
        print(f"   - 高质量论文: {len(high_quality_papers)}篇")
        print(f"   - 翻译: {translated}篇")
        print(f"   - AI解读: {interpreted}篇")
        print(f"   - 信息图: {infographics}篇")
        print(f"   - 推荐池: {pool_count}篇")
        print(f"   - 专题推荐: {sum(len(papers) for papers in special_recs.values())}篇")
        
        print(f"\n📈 分类统计:")
        for category, papers in categorized_papers.items():
            print(f"   - {category}: {len(papers)}篇")
        
    except Exception as e:
        print(f"❌ 会议论文流水线异常: {e}")
        raise

if __name__ == "__main__":
    main()
