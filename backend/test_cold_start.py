import sys
import os

# Ensure backend path is in pythonpath
sys.path.append("/data/proj/flopap/backend")

from app.db.session import SessionLocal
from app.services.recommendation.cold_start_service import ColdStartService
from app.models import Paper

def test_cold_start():
    db = SessionLocal()
    try:
        service = ColdStartService(db)
        
        print("--- Testing Hot Papers (Last 7 Days) ---")
        hot = service.get_hot_papers(limit=10)
        print(f"Hot Count: {len(hot)}")
        for pid in hot:
            print(f"  - Hot ID: {pid}")

        print("\n--- Testing Latest Papers (Fallback) ---")
        latest = service.get_latest_papers(limit=10)
        print(f"Latest Count: {len(latest)}")
        for pid in latest:
             p = db.get(Paper, pid)
             print(f"  - Latest: {p.title[:50]}... ({p.submitted_date})")

        print("\n--- Testing Combined Pool (Limit=5) ---")
        pool = service.get_cold_start_pool(limit=5)
        print(f"Pool Count: {len(pool)}")
        print(f"Pool IDs: {pool}")
        
    finally:
        db.close()

if __name__ == "__main__":
    test_cold_start()
