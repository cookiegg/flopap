#!/usr/bin/env python3
"""
获取今天美东时间-3天的arXiv论文

使用ingestion服务的默认获取日期逻辑
"""
import os
import sys
from pathlib import Path

# 禁用所有代理
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
from app.services.data_ingestion.ingestion import ingest_for_date


def get_default_target_date() -> pendulum.Date:
    """获取默认目标日期：今天美东时间-3天"""
    # 获取当前美东时间
    et_now = pendulum.now("America/New_York")
    # 减去3天（arXiv提交延迟）
    target_date = et_now.subtract(days=3).date()
    return target_date


def main():
    """主函数"""
    print("=== arXiv论文日常获取 ===")
    
    # 获取目标日期
    target_date = get_default_target_date()
    print(f"目标日期: {target_date} (美东时间-3天)")
    
    # 获取数据库会话
    db = SessionLocal()
    
    try:
        # 调用ingestion服务
        print("开始获取论文...")
        batch = ingest_for_date(session=db, target_date=target_date)
        
        print(f"\n✅ 获取完成!")
        print(f"批次ID: {batch.id}")
        print(f"获取日期: {batch.source_date}")
        print(f"论文数量: {batch.item_count}")
        print(f"查询条件: {batch.query}")
        print(f"获取时间: {batch.fetched_at}")
        
    except Exception as e:
        print(f"❌ 获取失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
