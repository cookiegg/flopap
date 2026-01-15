"""在 Railway 上初始化完整数据"""
import pendulum
from app.db.session import SessionLocal
from app.services.data_ingestion.ingestion import ingest_for_date
from app.services.recommendation import generate_personalized_pool
from app.models.paper import UserProfile

print("=" * 60)
print("Railway 数据初始化")
print("=" * 60)

db = SessionLocal()

# 1. 创建默认用户
print("\n1. 创建默认用户...")
user = db.query(UserProfile).filter(UserProfile.user_id == "default").first()
if not user:
    user = UserProfile(
        user_id="default",
        interested_categories=["cs.AI", "cs.LG"],
        research_keywords=["machine learning", "deep learning"],
        onboarding_completed=True
    )
    db.add(user)
    db.commit()
    print("✅ 用户创建成功")
else:
    print("✅ 用户已存在")

# 2. 抓取论文（使用美东时间 - 3天）
print("\n2. 抓取论文...")
now_et = pendulum.now("America/New_York")
target_date = now_et.subtract(days=3).date()
print(f"   目标日期（美东）: {target_date}")

try:
    batch = ingest_for_date(db, target_date)
    print(f"✅ 抓取完成: {batch.item_count} 篇论文")
except Exception as e:
    print(f"❌ 抓取失败: {e}")
    db.close()
    exit(1)

# 3. 生成推荐池
print("\n3. 生成推荐池...")
try:
    entries = generate_personalized_pool(db, user_id="default")
    db.commit()
    print(f"✅ 推荐池生成完成: {len(entries)} 篇")
except Exception as e:
    print(f"❌ 推荐池生成失败: {e}")
    db.close()
    exit(1)

db.close()

print("\n" + "=" * 60)
print("✅ Railway 数据初始化完成！")
print("=" * 60)
