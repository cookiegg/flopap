import time
import schedule
import subprocess
import os
import sys
from datetime import datetime
from loguru import logger

# Configuration
DAILY_REFRESH_TIME = "04:00"  # Local time

# Ensure we are in the correct directory context
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ["PYTHONPATH"] = BACKEND_DIR
sys.path.insert(0, BACKEND_DIR)  # Add to Python path for imports

def run_command(command, description):
    """Run a shell command and log output"""
    logger.info(f"🚀 Starting {description}...")
    try:
        # Use sys.executable to ensure we use the same python interpreter
        full_command = f"{sys.executable} {command}"
        result = subprocess.run(
            full_command, 
            shell=True, 
            check=True, 
            cwd=BACKEND_DIR,
            capture_output=True,
            text=True
        )
        logger.success(f"✅ {description} Completed Successfully")
        logger.debug(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ {description} Failed")
        logger.error(e.stderr)
        return False

def job_daily_refresh():
    """Daily Arxiv Fetch & Content Generation - Standalone Edition"""
    logger.info("⏰ Triggering Daily Refresh Workflow...")
    
    # 1. Fetch raw papers first
    if not run_command("scripts/arxiv_ingestion/fetch_daily_papers.py", "Fetch Daily Arxiv Papers"):
        logger.error("🛑 Aborting Daily Refresh due to Fetch Failure")
        return
    
    # 2. Generate content (Translation, Interpretation, TTS)
    if not run_command("scripts/daily_arxiv_refresh.py", "Daily Arxiv Refresh"):
        logger.error("🛑 Aborting Daily Refresh due to Content Generation Failure")
        return
    
    logger.success("✨ Daily Refresh Complete - All content saved locally")

def main():
    logger.add("logs/factory_mode.log", rotation="1 day")
    logger.info("🏭 Flopap Factory Mode Started (Standalone Edition)")
    logger.info(f"   - Daily Refresh scheduled at: {DAILY_REFRESH_TIME}")
    logger.info("   - All content will be saved locally (no cloud sync)")
    
    # Schedule jobs
    schedule.every().day.at(DAILY_REFRESH_TIME).do(job_daily_refresh)
    
    # Optional: Run once on startup for testing (commented out by default)
    # job_daily_refresh()
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except KeyboardInterrupt:
            logger.info("🛑 Factory Mode Stopped by User")
            break
        except Exception as e:
            logger.exception(f"Unexpected Error in Factory Loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
