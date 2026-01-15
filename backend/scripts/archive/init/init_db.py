"""临时脚本：初始化数据库表"""
from app.db.base import Base
from app.db.session import engine

print("Creating database tables...")
Base.metadata.create_all(engine)
print("✅ Database tables created successfully!")
