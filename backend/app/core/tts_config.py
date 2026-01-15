import os
import hmac
import hashlib
import time

class TTSConfig:
    """TTS音频文件配置"""
    
    # 环境配置
    ENVIRONMENT = os.getenv('TTS_ENVIRONMENT', 'local')  # 'local' 或 'production'
    
    # 本地配置
    LOCAL_TTS_DIR = "/data/proj/flopap/data/tts_opus"
    LOCAL_BASE_URL = "http://localhost:8000/static/tts"
    
    # 云端配置
    CLOUD_CDN_URL = "https://cdn.flopap.com"
    CLOUD_SIGNATURE_KEY = os.getenv('TX_COS_SIGNATURE_KEY', 'ZrauVMuFu3df_1ADi1ORi1Zgv_-OMRsVPeqno01oWvM')
    CLOUD_SIGNATURE_EXPIRES = 21600  # 6小时
    
    @classmethod
    def get_environment(cls):
        """动态获取环境配置"""
        return os.getenv('TTS_ENVIRONMENT', 'local')
    
    @classmethod
    def is_local_mode(cls):
        """是否为本地模式"""
        return cls.get_environment() == 'local'
    
    @classmethod
    def is_production_mode(cls):
        """是否为生产模式"""
        return cls.get_environment() == 'production'
