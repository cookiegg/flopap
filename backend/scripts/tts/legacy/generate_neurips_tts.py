#!/usr/bin/env python3
"""
为NeurIPS 2025论文生成TTS语音

用法：
  python scripts/tts/generate_neurips_tts.py --count 100
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


def get_random_neurips_papers(session, count: int = 100):
    """获取随机NeurIPS 2025论文ID"""
    query = text("""
        SELECT p.id
        FROM papers p
        JOIN paper_translations pt ON p.id = pt.paper_id
        JOIN paper_interpretations pi ON p.id = pi.paper_id
        WHERE p.source = 'conf/neurips2025'
        AND pt.title_zh IS NOT NULL 
        AND pi.interpretation IS NOT NULL
        ORDER BY RANDOM()
        LIMIT :count
    """)
    
    result = session.execute(query, {"count": count})
    return [row[0] for row in result.fetchall()]


def main():
    parser = argparse.ArgumentParser(description="为NeurIPS 2025论文生成TTS语音")
    parser.add_argument("--count", "-c", type=int, default=100, help="生成数量")
    parser.add_argument("--voice", default="zh-CN-XiaoxiaoNeural", help="语音模型")
    parser.add_argument("--max-workers", type=int, default=5, help="并发数")
    args = parser.parse_args()
    
    print(f"🎵 开始为NeurIPS 2025论文生成TTS语音")
    print(f"配置: {args.count}篇论文，{args.max_workers}个并发，语音模型: {args.voice}")
    
    # 获取数据库会话
    db = SessionLocal()
    
    try:
        # 获取随机论文ID
        print(f"正在随机选择 {args.count} 篇NeurIPS 2025论文...")
        paper_ids = get_random_neurips_papers(db, args.count)
        
        if not paper_ids:
            print("❌ 未找到可用的NeurIPS论文")
            return
        
        print(f"✅ 找到 {len(paper_ids)} 篇论文")
        
        # 生成TTS
        print(f"开始生成TTS（并发数：{args.max_workers}）...")
        tts_file_paths = batch_generate_tts_with_storage(
            session=db,
            paper_ids=paper_ids,
            voice=args.voice,
            max_workers=args.max_workers,
            save_to_storage=True
        )
        
        print(f"\n🎉 生成完成！")
        print(f"成功生成: {len(tts_file_paths)}/{len(paper_ids)} 个TTS文件")
        print(f"文件保存在: backend/data/tts/")
        
        # 显示前5个文件路径
        if tts_file_paths:
            print(f"\n示例文件:")
            for i, (paper_id, file_path) in enumerate(list(tts_file_paths.items())[:5]):
                print(f"  {i+1}. {Path(file_path).name}")
            if len(tts_file_paths) > 5:
                print(f"  ... 还有 {len(tts_file_paths) - 5} 个文件")
        
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
