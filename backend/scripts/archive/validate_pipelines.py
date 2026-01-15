#!/usr/bin/env python3
"""
流水线验证脚本
检查所有流水线的导入和基本功能
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

def test_imports():
    """测试所有关键导入"""
    print("🔍 检查流水线导入...")
    
    issues = []
    
    # 测试核心服务导入
    try:
        from app.services.data_ingestion.ingestion import ingest_for_date
        print("  ✅ ingestion.ingest_for_date")
    except ImportError as e:
        issues.append(f"ingestion.ingest_for_date: {e}")
    
    try:
        from app.services.data_ingestion.embedding import encode_documents
        print("  ✅ embedding.encode_documents")
    except ImportError as e:
        issues.append(f"embedding.encode_documents: {e}")
    
    try:
        from app.services.candidate_pool import CandidatePoolService, cs_filter
        print("  ✅ candidate_pool.CandidatePoolService, cs_filter")
    except ImportError as e:
        issues.append(f"candidate_pool: {e}")
    
    try:
        from app.services.translation_pure import batch_translate_papers
        print("  ✅ translation_pure.batch_translate_papers")
    except ImportError as e:
        issues.append(f"translation_pure.batch_translate_papers: {e}")
    
    try:
        from app.services.ai_interpretation_pure import interpret_and_save_papers
        print("  ✅ ai_interpretation_pure.interpret_and_save_papers")
    except ImportError as e:
        issues.append(f"ai_interpretation_pure.interpret_and_save_papers: {e}")
    
    try:
        from app.services.user_recommendation import UserRecommendationService
        print("  ✅ user_recommendation.UserRecommendationService")
    except ImportError as e:
        issues.append(f"user_recommendation.UserRecommendationService: {e}")
    
    try:
        from app.services.recommendation import generate_personalized_pool
        print("  ✅ recommendation.generate_personalized_pool")
    except ImportError as e:
        issues.append(f"recommendation.generate_personalized_pool: {e}")
    
    try:
        from scripts.init_user_embeddings import init_user_embeddings
        print("  ✅ scripts.init_user_embeddings.init_user_embeddings")
    except ImportError as e:
        issues.append(f"scripts.init_user_embeddings: {e}")
    
    # 测试数据库会话
    try:
        from app.db.session import SessionLocal, async_session_factory
        print("  ✅ database sessions")
    except ImportError as e:
        issues.append(f"database sessions: {e}")
    
    # 测试配置
    try:
        from app.core.config import settings
        print("  ✅ settings")
    except ImportError as e:
        issues.append(f"settings: {e}")
    
    return issues

def test_pipeline_syntax():
    """测试流水线脚本语法"""
    print("\n🔍 检查流水线语法...")
    
    import subprocess
    
    pipeline_files = [
        "scripts/pipeline/pipeline_master.py",
        "scripts/pipeline/pipeline_arxiv_cs_complete.py", 
        "scripts/pipeline/pipeline_embedding_recommendation.py",
        "scripts/pipeline/pipeline_daily_maintenance.py",
        "scripts/pipeline/pipeline_conference_papers.py",
        "scripts/pipeline/pipeline_user_onboarding.py"
    ]
    
    issues = []
    
    for pipeline_file in pipeline_files:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", pipeline_file],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent
            )
            
            if result.returncode == 0:
                print(f"  ✅ {pipeline_file}")
            else:
                print(f"  ❌ {pipeline_file}")
                issues.append(f"{pipeline_file}: {result.stderr}")
                
        except Exception as e:
            issues.append(f"{pipeline_file}: {e}")
    
    return issues

def test_database_connection():
    """测试数据库连接"""
    print("\n🔍 检查数据库连接...")
    
    try:
        from app.db.session import SessionLocal
        from sqlalchemy import text
        
        with SessionLocal() as db:
            result = db.execute(text("SELECT 1")).fetchone()
            if result:
                print("  ✅ 数据库连接正常")
                return []
            else:
                return ["数据库查询返回空结果"]
                
    except Exception as e:
        return [f"数据库连接失败: {e}"]

def test_key_tables():
    """测试关键数据表"""
    print("\n🔍 检查关键数据表...")
    
    try:
        from app.db.session import SessionLocal
        from sqlalchemy import text
        
        required_tables = [
            'papers', 'paper_embeddings', 'candidate_pools',
            'user_feedback', 'user_profiles', 
            'daily_recommendation_pool', 'user_recommendation_pools'
        ]
        
        issues = []
        
        with SessionLocal() as db:
            for table in required_tables:
                try:
                    result = db.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()
                    count = result[0] if result else 0
                    print(f"  ✅ {table}: {count}条记录")
                except Exception as e:
                    print(f"  ❌ {table}: {e}")
                    issues.append(f"表 {table} 不可访问: {e}")
        
        return issues
        
    except Exception as e:
        return [f"数据表检查失败: {e}"]

def main():
    """主检查流程"""
    print("🚀 开始流水线验证")
    
    all_issues = []
    
    # 检查导入
    import_issues = test_imports()
    all_issues.extend(import_issues)
    
    # 检查语法
    syntax_issues = test_pipeline_syntax()
    all_issues.extend(syntax_issues)
    
    # 检查数据库
    db_issues = test_database_connection()
    all_issues.extend(db_issues)
    
    # 检查数据表
    table_issues = test_key_tables()
    all_issues.extend(table_issues)
    
    # 总结
    print(f"\n📊 验证结果:")
    
    if not all_issues:
        print("✅ 所有检查通过，流水线准备就绪！")
        return True
    else:
        print(f"❌ 发现 {len(all_issues)} 个问题:")
        for i, issue in enumerate(all_issues, 1):
            print(f"  {i}. {issue}")
        
        print(f"\n💡 建议:")
        print("  - 检查缺失的服务函数")
        print("  - 确认数据库连接配置")
        print("  - 验证必要的数据表结构")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
