#!/usr/bin/env python3
"""
生成多领域候选论文池

支持生成CS、AI/ML/CV、数学、物理等领域的候选池
"""
import argparse
import os
import sys
from pathlib import Path
from datetime import date, timedelta

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
from app.db.session import SessionLocal
from app.services.data_ingestion.arxiv_candidate_pool import CandidatePoolServiceV2, FILTERS_V2


def main():
    parser = argparse.ArgumentParser(description="生成候选论文池")
    parser.add_argument(
        "--filter-type",
        choices=['cs', 'ai-ml-cv', 'math', 'physics', 'all'],
        default='cs',
        help="筛选类型 (默认: cs)"
    )
    parser.add_argument(
        "--date",
        type=str,
        help="目标日期 (YYYY-MM-DD格式)，默认为今天"
    )
    parser.add_argument(
        "--days-ago",
        type=int,
        help="生成N天前的候选池"
    )
    parser.add_argument(
        "--recent-days",
        type=int,
        help="生成最近N天的候选池"
    )
    args = parser.parse_args()
    
    print(f"=== {args.filter_type.upper()}候选论文池生成 ===")
    
    # 确定目标日期
    if args.date:
        target_dates = [pendulum.parse(args.date).date()]
        print(f"生成指定日期: {target_dates[0]}")
    elif args.days_ago is not None:
        target_date = (pendulum.today() - timedelta(days=args.days_ago)).date()
        target_dates = [target_date]
        print(f"生成 {args.days_ago} 天前的候选池: {target_date}")
    elif args.recent_days:
        target_dates = [
            (pendulum.today() - timedelta(days=i)).date()
            for i in range(args.recent_days)
        ]
        print(f"生成最近 {args.recent_days} 天的候选池")
    else:
        target_dates = [pendulum.today().date()]
        print(f"生成今天的候选池: {target_dates[0]}")
    
    # 获取筛选函数
    filter_func = FILTERS_V2.get(args.filter_type)
    if not filter_func:
        print(f"❌ 不支持的筛选类型: {args.filter_type}")
        return
    
    # 获取数据库会话
    db = SessionLocal()
    
    try:
        total_papers = 0
        
        for target_date in target_dates:
            print(f"\n处理日期: {target_date}")
            
            # 生成候选池
            paper_ids = CandidatePoolServiceV2.create_filtered_pool_by_date(
                session=db,
                target_date=target_date,
                filter_type=args.filter_type,
                filter_func=filter_func
            )
            
            print(f"  ✓ 筛选出 {len(paper_ids)} 篇{args.filter_type.upper()}论文")
            total_papers += len(paper_ids)
            
            # 提交到数据库
            db.commit()
        
        print(f"\n✅ 完成！")
        print(f"总共生成 {total_papers} 篇{args.filter_type.upper()}候选论文")
        print(f"处理日期数: {len(target_dates)}")
        
        # 显示统计信息
        if len(target_dates) == 1:
            stats = CandidatePoolServiceV2.get_date_statistics(db, target_dates[0])
            print(f"\n📊 {target_dates[0]} 统计:")
            for filter_type, count in stats.items():
                print(f"  {filter_type}: {count} 篇")
        
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
