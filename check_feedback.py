
import sys
import os
from uuid import uuid4

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.db.session import SessionLocal
from app.models import UserFeedback, Paper, FeedbackTypeEnum
from sqlalchemy import select, text
from app.core.config import settings

def check_feedback():
    db = SessionLocal()
    try:
        print(f"Checking DB: {settings.database_url}")
        
        # 1. Check if table exists and has data
        try:
            count = db.execute(text("SELECT count(*) FROM user_feedback")).scalar()
            print(f"Current UserFeedback count: {count}")
        except Exception as e:
            print(f"Error querying table: {e}")
            return

        # 2. Get a paper ID
        paper = db.execute(select(Paper).limit(1)).scalar_one_or_none()
        if not paper:
            print("No papers found in DB! Cannot test feedback.")
            return
        
        print(f"Using Paper: {paper.id} ({paper.title})")
        user_id = "default"
        
        # 3. Insert Test Feedback
        print("Inserting test 'like' feedback...")
        from app.services.user_feedback_service import _ensure_feedback, _has_feedback
        
        _ensure_feedback(db, user_id, paper.id, FeedbackTypeEnum.LIKE)
        
        # 4. Verify Immediate Read
        exists = _has_feedback(db, user_id, paper.id, FeedbackTypeEnum.LIKE)
        print(f"Feedback exists after insert? {exists}")
        
        # 5. Verify Raw SQL Read (to check Enum storage)
        raw_row = db.execute(text(f"SELECT feedback_type FROM user_feedback WHERE user_id='{user_id}' AND paper_id='{paper.id}'")).fetchone()
        print(f"Raw DB value: {raw_row}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_feedback()
