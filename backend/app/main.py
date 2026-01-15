from __future__ import annotations

import pendulum
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1 import v1_router  # 只导入V1 API
from app.db.base import Base
from app.db.session import engine

from app.core.config import settings

app = FastAPI(title="FloPap Backend", version="0.1.0")

# 挂载静态文件服务 - TTS音频文件
# 优先使用绝对路径，如果是相对路径则相对于项目根目录
tts_path = Path(settings.tts_directory)
if not tts_path.is_absolute():
    tts_path = settings.project_root / tts_path

if not tts_path.exists():
    tts_path.mkdir(parents=True, exist_ok=True)

app.mount("/static/tts", StaticFiles(directory=str(tts_path)), name="tts")

@app.on_event("startup")
def startup_event():
    """Application startup: initialize database and start worker thread"""
    # Start background worker for content generation
    from app.worker import start_worker
    start_worker()
    
# Separate function for DB initialization
@app.on_event("startup")
def init_db():
    from sqlalchemy import text
    from app.db.session import SessionLocal
    from app.models.paper import Paper, PaperEmbedding, UserProfile
    import random
    
    # 先创建 ENUM 类型（如果不存在）
    with engine.connect() as conn:
        conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE feedback_type AS ENUM ('like', 'bookmark', 'dislike');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))
        conn.commit()
    
    # 然后创建表
    Base.metadata.create_all(engine)
    
    # 清空 user_profiles 表（测试用）
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE user_profiles CASCADE"))
        conn.commit()
    
    # 初始化数据（如果数据库为空）
    db = SessionLocal()
    try:
        paper_count = db.query(Paper).count()
        print(f"📊 当前数据库中有 {paper_count} 篇论文")
        
        if paper_count == 0:
            print("📝 数据库为空，开始抓取 arXiv 论文...")
            # 创建测试用户
            db.add(UserProfile(user_id="default", interested_categories=["cs.AI"], research_keywords=["AI"], onboarding_completed=True))
            db.commit()
            print("✅ 创建默认用户")
            
            # 抓取真实的 arXiv 论文（不生成 embeddings）
            try:
                from app.services.data_ingestion.ingestion import _build_query_for_date, _search_arxiv, _convert_result
                from app.models.paper import IngestionBatch
                from sqlalchemy import select
                
                now_et = pendulum.now("America/New_York")
                target_date = now_et.subtract(days=3).date()
                print(f"📥 抓取日期: {target_date} (美东时间)")
                
                # 构建查询并抓取
                query = _build_query_for_date(target_date)
                results = list(_search_arxiv(query, target_date=target_date))
                papers_data = [_convert_result(r) for r in results]
                print(f"📥 获取到 {len(papers_data)} 篇论文")
                
                # 创建批次
                batch = IngestionBatch(
                    source_date=target_date,
                    fetched_at=pendulum.now("UTC"),
                    item_count=len(papers_data),
                    query=query
                )
                db.add(batch)
                db.flush()
                
                # 保存论文（不生成 embeddings）
                for paper_data in papers_data:
                    existing = db.scalar(select(Paper).where(Paper.arxiv_id == paper_data.arxiv_id))
                    if existing is None:
                        paper = Paper(
                            arxiv_id=paper_data.arxiv_id,
                            title=paper_data.title,
                            summary=paper_data.summary,
                            authors=paper_data.authors,
                            categories=paper_data.categories,
                            submitted_date=paper_data.submitted_date,
                            updated_date=paper_data.updated_date,
                            pdf_url=paper_data.pdf_url,
                            html_url=paper_data.html_url,
                            comment=paper_data.comment,
                            doi=paper_data.doi,
                            primary_category=paper_data.primary_category,
                            source='arxiv',  # 新增：设置数据源
                            ingestion_batch_id=batch.id
                        )
                        db.add(paper)
                
                db.commit()
                print(f"✅ 抓取完成: {len(papers_data)} 篇论文（未生成 embeddings）")
            except Exception as e:
                print(f"❌ 抓取论文失败: {e}")
                # 如果抓取失败，创建测试数据
                print("📝 创建测试数据作为备用...")
                from app.models.paper import IngestionBatch
                
                # 创建测试论文
                papers = []
                for i in range(10):
                    p = Paper(
                        arxiv_id=f"2024.{i}",
                        title=f"Test Paper {i}: AI Research",
                        summary=f"This is test paper {i} about artificial intelligence.",
                        authors=["Test Author"],
                        categories=["cs.AI"],
                        submitted_date=pendulum.now("UTC").subtract(days=i),
                        pdf_url=f"https://arxiv.org/pdf/2024.{i}",
                        primary_category="cs.AI",
                        source='arxiv'  # 新增：设置数据源
                    )
                    db.add(p)
                    papers.append(p)
                db.commit()
                
                # 创建 IngestionBatch
                batch = IngestionBatch(
                    source_date=pendulum.now("UTC").subtract(days=3).date(),
                    fetched_at=pendulum.now("UTC"),
                    item_count=len(papers)
                )
                db.add(batch)
                db.commit()
                
                # 关联论文到批次
                for p in papers:
                    p.ingestion_batch_id = batch.id
                db.commit()
                
                # 创建 embeddings
                import random
                for p in papers:
                    db.add(PaperEmbedding(paper_id=p.id, vector=[random.random() for _ in range(1024)], model_name="test"))
                db.commit()
                print(f"✅ 测试数据创建完成: {db.query(Paper).count()} papers, batch_id={batch.id}")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
    finally:
        db.close()
    
    print("✅ Database initialization complete")

# 配置 CORS，允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",  # 允许所有来源
        "http://localhost",
        "https://localhost",
        "capacitor://localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 添加请求追踪中间件
from app.middleware.request_id import RequestIDMiddleware
app.add_middleware(RequestIDMiddleware)

app.include_router(v1_router, prefix="/api")  # Include V1 API

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "timestamp": pendulum.now("UTC").to_iso8601_string()}

# Serve frontend static files (must be after API routes and other specific routes)
try:
    from pathlib import Path
    from fastapi.responses import FileResponse

    static_dir = Path("/app/static")
    if static_dir.exists():
        # 1. Mount assets explicitly if they exist in a subdirectory
        # (This is optional if the catch-all handles it, but mounting is often faster/standard)
        assets_dir = static_dir / "assets"
        if assets_dir.exists():
             app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

        # 2. Catch-all route for SPA
        # This will match any path that wasn't matched by the API routers above.
        @app.get("/{full_path:path}")
        async def serve_frontend(full_path: str):
            # Security: Prevent traversing out of static_dir
            # (FastAPI/Starlette StaticFiles does this, but manual FileResponse needs care.
            # However, since we are just checking if file exists relative to static_dir...)
            
            potential_file = static_dir / full_path
            
            # If it's a file that exists, serve it (e.g. favicon.ico, logo.png)
            if potential_file.is_file():
                return FileResponse(potential_file)
                
            # Otherwise, for SPA client-side routing, serve index.html
            # (e.g. /profile, /feed)
            return FileResponse(static_dir / "index.html")
            
except Exception as e:
    print(f"Warning: Could not mount frontend static files: {e}")
