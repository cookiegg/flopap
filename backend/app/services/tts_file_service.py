import os
from pathlib import Path
from app.core.config import settings

class TTSFileService:
    """TTS File Service - Standalone Edition (Local-only)"""
    
    def get_file_url(self, filename):
        """Get file access URL - local mode only"""
        return f"/api/v1/tts/file/{filename}"
    
    def file_exists(self, filename):
        """Check if file exists in local storage"""
        file_path = Path(settings.tts_directory) / filename
        return file_path.exists()
    
    def get_file_path(self, filename):
        """Get absolute local file path"""
        return str(Path(settings.tts_directory) / filename)

# Global instance
tts_service = TTSFileService()
