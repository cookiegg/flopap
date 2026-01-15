"""快速初始化 Railway 数据库"""
import pendulum, random
from app.db.session import SessionLocal
from app.models.paper import Paper, PaperEmbedding, DailyRecommendationPool, UserProfile

db = SessionLocal()

# 创建用户
if not db.query(UserProfile).filter(UserProfile.user_id == "default").first():
    db.add(UserProfile(user_id="default", interested_categories=["cs.AI"], research_keywords=["AI"], onboarding_completed=True))
    db.commit()

# 创建 10 篇论文
if db.query(Paper).count() == 0:
    for i in range(10):
        p = Paper(arxiv_id=f"2024.{i}", title=f"Paper {i}", summary=f"Summary {i}", authors=["Author"], categories=["cs.AI"], submitted_date=pendulum.now("UTC"), pdf_url=f"https://arxiv.org/pdf/2024.{i}", primary_category="cs.AI")
        db.add(p)
    db.commit()

# 创建 embeddings
for p in db.query(Paper).all():
    if not db.query(PaperEmbedding).filter(PaperEmbedding.paper_id == p.id).first():
        db.add(PaperEmbedding(paper_id=p.id, vector=[random.random() for _ in range(1024)], model_name="test"))
db.commit()

# 生成推荐池
today = pendulum.now('UTC').date()
db.query(DailyRecommendationPool).filter(DailyRecommendationPool.pool_date == today).delete()
for i, p in enumerate(db.query(Paper).limit(10).all()):
    db.add(DailyRecommendationPool(pool_date=today, paper_id=p.id, score=1.0-i*0.1, position=i, is_active=True))
db.commit()

print(f"✅ 初始化完成: {db.query(Paper).count()} papers, {db.query(DailyRecommendationPool).count()} pool")
db.close()
