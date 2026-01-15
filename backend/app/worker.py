"""
Background Worker - Runs content generation in a separate thread
"""
import threading
import time
from loguru import logger

from scripts.run_factory_mode import job_daily_refresh
import schedule


def start_worker():
    """Start background worker thread for content generation"""
    def worker_loop():
        logger.info("🏭 Background Worker Thread Started")
        logger.info("   - Daily content generation scheduled at 04:00")
        
        # Schedule daily job
        schedule.every().day.at("04:00").do(job_daily_refresh)
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)
            except Exception as e:
                logger.exception(f"Worker thread error: {e}")
                time.sleep(60)
    
    # Start worker in daemon thread (dies when main app exits)
    worker_thread = threading.Thread(target=worker_loop, daemon=True)
    worker_thread.start()
    logger.info("✅ Background worker thread started successfully")
