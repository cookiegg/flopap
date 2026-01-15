import os
import sys
from sqlalchemy import text
from app.db.session import SessionLocal

def check_counts():
    db = SessionLocal()
    try:
        # 1. Total Papers
        res = db.execute(text("SELECT count(*) FROM papers"))
        total_papers = res.scalar()
        print(f"Total Papers: {total_papers}")

        # 2. Candidate Pool (last 7 days?)
        res = db.execute(text("SELECT count(*) FROM ingestion_batches"))
        total_batches = res.scalar()
        print(f"Total Ingestion Batches: {total_batches}")

        # 3. User Recommendations for 'default'
        res = db.execute(text("SELECT count(*) FROM user_recommendations WHERE user_id = 'default'"))
        total_recs = res.scalar()
        print(f"Total Recommendations for 'default': {total_recs}")
        
        # 4. Show Recs details if any
        if total_recs > 0:
            res = db.execute(text("SELECT paper_id, score, created_at FROM user_recommendations WHERE user_id = 'default' ORDER BY created_at DESC LIMIT 5"))
            for row in res:
                print(f"Rec: {row}")

    finally:
        db.close()

if __name__ == "__main__":
    check_counts()
