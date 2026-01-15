
import os
from pathlib import Path
from app.db.session import SessionLocal
from app.models.paper_tts import PaperTTS
from app.core.config import settings
from sqlalchemy import select

def fix_tts_files():
    db = SessionLocal()
    try:
        # Find all records ending with .wav
        records = db.execute(select(PaperTTS).where(PaperTTS.file_path.like('%.wav'))).scalars().all()
        print(f"Found {len(records)} records with .wav extension")
        
        tts_dir = Path(settings.tts_directory)
        
        for record in records:
            old_filename = record.file_path
            new_filename = old_filename.replace('.wav', '.mp3')
            
            old_path = tts_dir / old_filename
            new_path = tts_dir / new_filename
            
            if old_path.exists():
                print(f"Renaming {old_filename} -> {new_filename}")
                old_path.rename(new_path)
                
                # Update DB
                record.file_path = new_filename
                
            elif new_path.exists():
                print(f"Target file {new_filename} already exists, updating DB only")
                record.file_path = new_filename
            else:
                print(f"⚠️ File {old_filename} not found!")
                
        db.commit()
        print("✅ Fix completed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_tts_files()
