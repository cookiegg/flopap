#!/usr/bin/env python3
"""
无代理获取arXiv论文

专门用于绕过代理问题的获取脚本
"""
import argparse
import os
import sys
from pathlib import Path

# 强制禁用所有代理设置
proxy_vars = [
    'http_proxy', 'https_proxy', 'ftp_proxy', 'socks_proxy',
    'HTTP_PROXY', 'HTTPS_PROXY', 'FTP_PROXY', 'SOCKS_PROXY',
    'all_proxy', 'ALL_PROXY', 'no_proxy', 'NO_PROXY'
]

for var in proxy_vars:
    os.environ.pop(var, None)

# 设置无代理环境
os.environ['NO_PROXY'] = '*'

print("🚫 已禁用所有代理设置")

# 添加backend根目录到路径
backend_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_root))

import pendulum
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.data_ingestion.ingestion import ingest_for_date


def main():
    parser = argparse.ArgumentParser(description="无代理获取arXiv论文")
    parser.add_argument(
        "--date", 
        type=str, 
        help="目标日期 (YYYY-MM-DD格式)，默认为今天美东时间-3天"
    )
    parser.add_argument(
        "--days-ago", 
        type=int, 
        default=3,
        help="获取N天前的论文（基于美东时间），默认3天"
    )
    args = parser.parse_args()
    
    print("=== arXiv论文无代理获取 ===")
    
    # 确定目标日期
    if args.date:
        target_date = pendulum.parse(args.date).date()
        print(f"使用指定日期: {target_date}")
    else:
        et_now = pendulum.now("America/New_York")
        target_date = et_now.subtract(days=args.days_ago).date()
        print(f"获取 {args.days_ago} 天前的论文: {target_date}")
    
    # 获取数据库会话
    db = SessionLocal()
    
    try:
        print(f"\n开始获取 {target_date} 的论文...")
        print("📡 使用直连模式（无代理）")
        
        batch = ingest_for_date(session=db, target_date=target_date)
        
        print(f"\n✅ 获取完成!")
        print(f"批次ID: {batch.id}")
        print(f"获取日期: {batch.source_date}")
        print(f"论文数量: {batch.item_count}")
        print(f"查询条件: {batch.query}")
        print(f"获取时间: {batch.fetched_at}")
        
        if batch.item_count == 0:
            print("\n⚠️  未获取到论文，可能原因:")
            print("- 该日期没有新论文")
            print("- 网络连接问题")
            print("- arXiv API限制")
        else:
            print(f"\n🎉 成功获取 {batch.item_count} 篇论文!")
        
    except Exception as e:
        print(f"❌ 获取失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
