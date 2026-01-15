#!/usr/bin/env python3
"""
查询候选论文池统计信息

查看指定日期的候选池统计和论文信息
"""
import argparse
import os
import sys
from pathlib import Path

# 禁用代理
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('all_proxy', None)
os.environ.pop('ALL_PROXY', None)

# 添加backend根目录到路径
backend_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_root))

import pendulum
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import SessionLocal
from app.services.data_ingestion.arxiv_candidate_pool import CandidatePoolServiceV2


def main():
    parser = argparse.ArgumentParser(description="查询候选论文池")
    parser.add_argument(
        "--date",
        type=str,
        help="查询日期 (YYYY-MM-DD格式)，默认为今天"
    )
    parser.add_argument(
        "--filter-type",
        choices=['cs', 'ai-ml-cv', 'math', 'physics', 'all'],
        help="查询特定筛选类型"
    )
    parser.add_argument(
        "--show-papers",
        action="store_true",
        help="显示论文详细信息"
    )
    args = parser.parse_args()
    
    # 确定查询日期
    if args.date:
        target_date = pendulum.parse(args.date).date()
    else:
        target_date = pendulum.today().date()
    
    print(f"=== 候选论文池查询 - {target_date} ===")
    
    # 获取数据库会话
    db = SessionLocal()
    
    try:
        # 获取统计信息
        print(f"\n📊 统计信息:")
        
        # 直接查询候选池数据
        from app.services.data_ingestion.arxiv_candidate_pool import date_to_uuid
        from app.models import CandidatePool
        from sqlalchemy import select, func
        
        date_uuid = date_to_uuid(target_date)
        
        # 按筛选类型统计
        stmt = (
            select(CandidatePool.filter_type, func.count(CandidatePool.paper_id))
            .where(CandidatePool.batch_id == date_uuid)
            .group_by(CandidatePool.filter_type)
        )
        
        results = db.execute(stmt).all()
        
        if not results:
            print(f"❌ 未找到 {target_date} 的候选池数据")
            return
        
        total = 0
        stats = {}
        for filter_type, count in results:
            print(f"  {filter_type.upper()}: {count} 篇")
            stats[filter_type] = count
            total += count
        print(f"  总计: {total} 篇")
        
        # 如果指定了筛选类型，显示详细信息
        if args.filter_type:
            paper_ids = CandidatePoolServiceV2.get_candidate_papers_by_date(
                db, target_date, args.filter_type
            )
            
            print(f"\n🔍 {args.filter_type.upper()}候选池详情:")
            print(f"论文数量: {len(paper_ids)}")
            
            if args.show_papers and paper_ids:
                print(f"\n📄 论文列表:")
                # 获取论文详细信息
                result = db.execute(text("""
                    SELECT p.arxiv_id, p.title, p.categories
                    FROM papers p
                    WHERE p.id = ANY(:paper_ids)
                    ORDER BY p.submitted_date DESC
                    LIMIT 10
                """), {"paper_ids": paper_ids[:10]})
                
                papers = result.fetchall()
                for i, paper in enumerate(papers, 1):
                    arxiv_id, title, categories = paper
                    print(f"  {i}. {arxiv_id}")
                    print(f"     标题: {title[:80]}...")
                    print(f"     分类: {', '.join(categories)}")
                    print()
                
                if len(paper_ids) > 10:
                    print(f"  ... 还有 {len(paper_ids) - 10} 篇论文")
        
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
