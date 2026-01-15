#!/usr/bin/env python3
"""
分批为NeurIPS 2025论文生成TTS语音

用法：
  python scripts/tts/generate_neurips_tts_batch.py --batch-size 10 --max-workers 10
"""
import argparse
import sys
from pathlib import Path
from uuid import UUID

# 添加backend根目录到路径
backend_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_root))

from sqlalchemy import text
from app.db.session import SessionLocal
from app.services.content_generation.tts_generate import batch_generate_tts_with_storage


def get_all_neurips_papers(session, offset: int = 0, limit: int = 10):
    """获取NeurIPS 2025论文ID（分页）"""
    query = text("""
        SELECT p.id
        FROM papers p
        JOIN paper_translations pt ON p.id = pt.paper_id
        JOIN paper_interpretations pi ON p.id = pi.paper_id
        WHERE p.source = 'conf/neurips2025'
        AND pt.title_zh IS NOT NULL 
        AND pi.interpretation IS NOT NULL
        ORDER BY p.id
        LIMIT :limit OFFSET :offset
    """)
    
    result = session.execute(query, {"limit": limit, "offset": offset})
    return [row[0] for row in result.fetchall()]


def main():
    parser = argparse.ArgumentParser(description="分批为NeurIPS 2025论文生成TTS语音")
    parser.add_argument("--batch-size", type=int, default=10, help="每批处理数量")
    parser.add_argument("--voice", default="zh-CN-XiaoxiaoNeural", help="语音模型")
    parser.add_argument("--max-workers", type=int, default=10, help="并发数")
    parser.add_argument("--start-batch", type=int, default=0, help="起始批次")
    args = parser.parse_args()
    
    print(f"🎵 开始分批为NeurIPS 2025论文生成TTS语音")
    print(f"配置: 每批{args.batch_size}篇，{args.max_workers}个并发，语音模型: {args.voice}")
    
    db = SessionLocal()
    
    try:
        # 获取总数
        total_query = text("""
            SELECT COUNT(*)
            FROM papers p
            JOIN paper_translations pt ON p.id = pt.paper_id
            JOIN paper_interpretations pi ON p.id = pi.paper_id
            WHERE p.source = 'conf/neurips2025'
            AND pt.title_zh IS NOT NULL 
            AND pi.interpretation IS NOT NULL
        """)
        total_count = db.execute(total_query).scalar()
        total_batches = (total_count + args.batch_size - 1) // args.batch_size
        
        print(f"总计: {total_count}篇论文，{total_batches}批次")
        
        success_count = 0
        
        for batch_num in range(args.start_batch, total_batches):
            offset = batch_num * args.batch_size
            print(f"\n📦 处理第 {batch_num + 1}/{total_batches} 批 (偏移: {offset})")
            
            # 获取当前批次的论文ID
            paper_ids = get_all_neurips_papers(db, offset, args.batch_size)
            
            if not paper_ids:
                print("❌ 当前批次无可用论文")
                continue
            
            print(f"✅ 当前批次: {len(paper_ids)} 篇论文")
            
            # 生成TTS
            try:
                tts_file_paths = batch_generate_tts_with_storage(
                    session=db,
                    paper_ids=paper_ids,
                    voice=args.voice,
                    max_workers=args.max_workers,
                    save_to_storage=True
                )
                
                batch_success = len(tts_file_paths)
                success_count += batch_success
                
                print(f"🎉 第 {batch_num + 1} 批完成: {batch_success}/{len(paper_ids)} 个文件")
                print(f"📊 总进度: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
                
            except Exception as e:
                print(f"❌ 第 {batch_num + 1} 批失败: {e}")
                continue
        
        print(f"\n🎉 全部完成！")
        print(f"成功生成: {success_count}/{total_count} 个TTS文件")
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
