#!/usr/bin/env python3
"""
导入2025年会议论文数据

使用方法:
  python import_2025_conferences.py                    # 导入所有可用会议
  python import_2025_conferences.py neurips2025       # 导入指定会议
  python import_2025_conferences.py --list            # 列出可用会议
"""

import sys
import argparse
from pathlib import Path

# 添加backend根目录到路径
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(backend_root))

from app.db.session import SessionLocal
from app.services.data_ingestion.conference_import import (
    import_conference_papers,
    import_all_2025_conferences,
    get_available_2025_conferences,
    SUPPORTED_2025_CONFERENCES
)


def list_available_conferences():
    """列出可用的会议数据"""
    print("📋 可用的2025年会议数据:")
    print("-" * 60)
    
    available = get_available_2025_conferences()
    
    if not available:
        print("❌ 未找到任何会议数据文件")
        return
    
    for conf in available:
        size_mb = conf['file_size'] / (1024 * 1024)
        print(f"✅ {conf['id']:<15} {conf['name']:<20} ({size_mb:.1f} MB)")
    
    print(f"\n📊 总计: {len(available)} 个会议")


def import_single_conference(conference_id: str):
    """导入单个会议数据"""
    if conference_id not in SUPPORTED_2025_CONFERENCES:
        print(f"❌ 不支持的会议: {conference_id}")
        print(f"支持的会议: {', '.join(SUPPORTED_2025_CONFERENCES.keys())}")
        return False
    
    with SessionLocal() as db:
        try:
            batch = import_conference_papers(db, conference_id)
            print(f"\n✅ 导入成功!")
            print(f"会议: {SUPPORTED_2025_CONFERENCES[conference_id]['name']}")
            print(f"批次ID: {batch.id}")
            print(f"论文数量: {batch.item_count}")
            return True
        except Exception as e:
            print(f"❌ 导入失败: {e}")
            return False


def import_all_conferences():
    """导入所有会议数据"""
    with SessionLocal() as db:
        try:
            results = import_all_2025_conferences(db)
            
            print("\n📊 导入结果汇总:")
            print("-" * 60)
            
            total_papers = 0
            success_count = 0
            
            for conf_id, batch in results.items():
                conf_name = SUPPORTED_2025_CONFERENCES[conf_id]['name']
                if batch:
                    print(f"✅ {conf_id:<15} {conf_name:<20} {batch.item_count:>6} 篇")
                    total_papers += batch.item_count
                    success_count += 1
                else:
                    print(f"❌ {conf_id:<15} {conf_name:<20} {'失败':>6}")
            
            print("-" * 60)
            print(f"📈 成功导入: {success_count}/{len(results)} 个会议")
            print(f"📚 总论文数: {total_papers:,} 篇")
            
            return True
        except Exception as e:
            print(f"❌ 批量导入失败: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="导入2025年会议论文数据")
    parser.add_argument('conference', nargs='?', help='会议ID (如: neurips2025)')
    parser.add_argument('--list', action='store_true', help='列出可用会议')
    
    args = parser.parse_args()
    
    if args.list:
        list_available_conferences()
        return
    
    if args.conference:
        success = import_single_conference(args.conference)
        sys.exit(0 if success else 1)
    else:
        success = import_all_conferences()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
