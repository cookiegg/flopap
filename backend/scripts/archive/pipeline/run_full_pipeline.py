#!/usr/bin/env python3
"""完整数据流水线：获取论文 -> 生成翻译和解读 -> 生成推荐池"""
import sys
import pendulum
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.db.session import SessionLocal
from app.services.data_ingestion.ingestion import ingest_for_date
from app.models import Paper, PaperTranslation
from app.services.ai_interpretation_unified import generate_ai_interpretation_unified
from app.services.llm import get_deepseek_clients
from app.services.translation import batch_translate_pool
from app.services.recommendation import generate_personalized_pool

print("=" * 60)
print("完整数据流水线")
print("=" * 60)

# 1. 获取论文
print("\n[1/3] 获取 arXiv 论文...")
from app.core.config import settings
now_et = pendulum.now("America/New_York")
target_date = now_et.subtract(days=settings.arxiv_submission_delay_days).date()
print(f"目标日期（美东时间 - {settings.arxiv_submission_delay_days} 天）: {target_date}")

db = SessionLocal()
try:
    batch = ingest_for_date(db, target_date)
    db.commit()
    print(f"✅ 获取完成: {batch.item_count} 篇新论文")
except Exception as e:
    print(f"⚠️  获取过程有错误: {e}")
    print(f"   论文可能已保存，继续执行...")
    db.rollback()

# 2. 生成 AI 内容（翻译和解读）
print("\n[2/3] 生成 AI 内容...")

# 2.1 生成解读
papers_without_interp = db.query(Paper).filter(Paper.interpretation == None).limit(20).all()
print(f"需要生成解读: {len(papers_without_interp)} 篇")

for i, paper in enumerate(papers_without_interp, 1):
    try:
        print(f"  [{i}/{len(papers_without_interp)}] {paper.arxiv_id}...", end=" ")
        clients = get_deepseek_clients()
        if clients:
            interpretation = generate_ai_interpretation_unified(clients[0], paper)
        else:
            interpretation = None
        paper.interpretation = interpretation
        db.commit()
        print("✓")
    except Exception as e:
        print(f"✗ {e}")
        db.rollback()

# 2.2 批量生成翻译（使用推荐池中的论文）
print(f"批量生成翻译...")
try:
    count = batch_translate_pool(db)
    print(f"✅ 翻译完成: {count} 篇")
except Exception as e:
    print(f"❌ 翻译失败: {e}")

# 3. 生成推荐池
print("\n[3/3] 生成推荐池...")
try:
    from app.core.config import settings
    entries = generate_personalized_pool(db, user_id=settings.default_user_id)
    db.commit()
    print(f"✅ 推荐池生成完成: {len(entries)} 条")
except Exception as e:
    print(f"❌ 推荐池生成失败: {e}")

db.close()

print("\n" + "=" * 60)
print("✅ 完整流水线执行完成！")
print("=" * 60)
