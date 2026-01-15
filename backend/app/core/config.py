import os
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

from app.core.edition import Edition

# Load environment variables from a `.env` file if it exists
# config.py 位于 backend/app/core/config.py，所以：
# parents[0] = backend/app/core/
# parents[1] = backend/app/
# parents[2] = backend/
# parents[3] = 项目根目录
ENV_PATHS = [
    Path(__file__).resolve().parents[3] / ".env",  # 项目根目录
    Path(__file__).resolve().parents[2] / ".env",  # backend 目录
    Path(__file__).resolve().parents[1] / ".env",  # backend/app 目录
]
for env_path in ENV_PATHS:
    if env_path.exists():
        # 在容器环境下，我们希望环境变量优先（docker-compose 设置的）
        # 所以使用 override=False (默认值)
        load_dotenv(env_path, override=False)
        break  # 找到第一个存在的就停止


class Settings(BaseSettings):
    # Edition configuration
    edition: Edition = Field(
        default=Edition.COMMUNITY,
        alias="FLOPAP_EDITION",
        description="FloPap edition: community or cloud"
    )
    
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/flopap",
        alias="DATABASE_URL",
    )
    arxiv_query: str = Field(default="all", alias="ARXIV_QUERY")
    arxiv_max_results: int = Field(default=30000, alias="ARXIV_MAX_RESULTS", description="最多获取的结果数（最多 30000，arXiv API 限制）")
    arxiv_submission_delay_days: int = Field(default=3, alias="ARXIV_SUBMISSION_DELAY_DAYS")
    arxiv_page_size: int = Field(default=2000, alias="ARXIV_PAGE_SIZE", description="每页获取的论文数量（最多 2000，arXiv API 限制）")
    arxiv_delay_seconds: float = Field(default=1.0, alias="ARXIV_DELAY_SECONDS", description="每次请求之间的延迟（秒，建议 1-3）")
    arxiv_num_retries: int = Field(default=3, alias="ARXIV_NUM_RETRIES", description="请求失败重试次数")
    http_proxy: str | None = Field(default=None, alias="HTTP_PROXY", description="HTTP 代理地址，如 http://127.0.0.1:7890")
    https_proxy: str | None = Field(default=None, alias="HTTPS_PROXY", description="HTTPS 代理地址，如 http://127.0.0.1:7890")
    
    # Standalone edition does not require SMS authentication
    dashscope_api_key: str | None = Field(default=None, alias="DASHSCOPE_API_KEY")
    dashscope_base_url: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        alias="DASHSCOPE_BASE_URL",
    )
    embedding_model_name: str = Field(default="text-embedding-v4", alias="EMBEDDING_MODEL_NAME")
    embedding_dimension: int = Field(default=1024, alias="EMBEDDING_DIMENSION")
    embedding_max_batch_size: int = Field(default=10, alias="EMBEDDING_MAX_BATCH_SIZE")
    batch_ratio: float = Field(default=0.1, alias="RECOMMENDATION_BATCH_RATIO")
    batch_min_size: int = Field(default=50, alias="RECOMMENDATION_BATCH_MIN_SIZE")
    batch_max_size: int = Field(default=200, alias="RECOMMENDATION_BATCH_MAX_SIZE")
    default_user_id: str = Field(default="default", alias="DEFAULT_USER_ID")
    retries: int = Field(default=3, alias="FETCH_RETRIES")
    retry_backoff_seconds: float = Field(default=2.0, alias="FETCH_RETRY_BACKOFF")
    deepseek_api_keys: List[str] = Field(default_factory=list, description="DeepSeek API Keys列表")
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com/v1",
        alias="DEEPSEEK_BASE_URL",
        description="DeepSeek API Base URL"
    )
    deepseek_model_name: str = Field(
        default="deepseek-reasoner",
        alias="DEEPSEEK_MODEL_NAME",
        description="DeepSeek模型名称"
    )
    
    # Standalone edition does not require OAuth authentication
    
    # JWT Settings
    jwt_secret_key: str = Field(
        default="dev-secret-key-change-in-production-" + os.urandom(32).hex()[:32],
        alias="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=60 * 24 * 7,  # 7 days
        alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    
    # Redis Settings
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    redis_password: str | None = Field(default=None, alias="REDIS_PASSWORD")
    redis_cache_ttl: int = Field(default=3600, alias="REDIS_CACHE_TTL", description="默认缓存时间(秒)")
    
    # Path Settings
    tts_directory: str = Field(default="/app/data/tts_opus", alias="TTS_DIRECTORY")
    static_directory: str = Field(default="app/static", alias="STATIC_DIRECTORY")
    
    # Standalone edition: no cloud sync needed


    @classmethod
    def _from_env(cls) -> dict:
        """从环境变量构建参数字典"""
        env_mappings = {
            "edition": "FLOPAP_EDITION",
            "database_url": "DATABASE_URL",
            "arxiv_query": "ARXIV_QUERY",
            "arxiv_max_results": "ARXIV_MAX_RESULTS",
            "arxiv_submission_delay_days": "ARXIV_SUBMISSION_DELAY_DAYS",
            "arxiv_page_size": "ARXIV_PAGE_SIZE",
            "arxiv_delay_seconds": "ARXIV_DELAY_SECONDS",
            "arxiv_num_retries": "ARXIV_NUM_RETRIES",
            "http_proxy": "HTTP_PROXY",
            "https_proxy": "HTTPS_PROXY",
            "dashscope_api_key": "DASHSCOPE_API_KEY",
            "dashscope_base_url": "DASHSCOPE_BASE_URL",
            "embedding_model_name": "EMBEDDING_MODEL_NAME",
            "embedding_dimension": "EMBEDDING_DIMENSION",
            "embedding_max_batch_size": "EMBEDDING_MAX_BATCH_SIZE",
            "batch_ratio": "RECOMMENDATION_BATCH_RATIO",
            "batch_min_size": "RECOMMENDATION_BATCH_MIN_SIZE",
            "batch_max_size": "RECOMMENDATION_BATCH_MAX_SIZE",
            "default_user_id": "DEFAULT_USER_ID",
            "retries": "FETCH_RETRIES",
            "retry_backoff_seconds": "FETCH_RETRY_BACKOFF",
            "deepseek_base_url": "DEEPSEEK_BASE_URL",
            "deepseek_model_name": "DEEPSEEK_MODEL_NAME",
            "google_client_id": "GOOGLE_CLIENT_ID",
            "google_client_secret": "GOOGLE_CLIENT_SECRET",
            "github_client_id": "GITHUB_CLIENT_ID",
            "github_client_secret": "GITHUB_CLIENT_SECRET",
            "oauth_redirect_uri": "OAUTH_REDIRECT_URI",
            "jwt_secret_key": "JWT_SECRET_KEY",
            "jwt_algorithm": "JWT_ALGORITHM",
            "jwt_access_token_expire_minutes": "JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
            "internal_ingest_token": "INTERNAL_INGEST_TOKEN",
            "internal_allowed_ips": "INTERNAL_ALLOWED_IPS",
        }
        
        kwargs = {}
        for field_name, env_name in env_mappings.items():
            env_value = os.getenv(env_name)
            if env_value is not None:
                kwargs[field_name] = env_value
        
        # 读取DeepSeek API Keys (DEEPSEEK_API_KEY_01 到 DEEPSEEK_API_KEY_50)
        deepseek_keys = []
        for i in range(1, 51):
            key = os.getenv(f"DEEPSEEK_API_KEY_{i:02d}")
            if key:
                deepseek_keys.append(key)
        if deepseek_keys:
            kwargs["deepseek_api_keys"] = deepseek_keys
        
        return kwargs
    
    def __init__(self, **kwargs):
        # Pydantic v2 不会自动从环境变量读取，需要手动处理
        # 合并环境变量的值（环境变量优先级较低，kwargs 中的值会覆盖环境变量）
        env_kwargs = self._from_env()
        
        # 处理 DeepSeek API Keys（支持 JSON 格式）
        import json
        keys_json = os.getenv("DEEPSEEK_API_KEYS")
        if keys_json:
            try:
                env_kwargs["deepseek_api_keys"] = json.loads(keys_json)
            except json.JSONDecodeError:
                pass  # 如果解析失败，使用默认的环境变量方式
        
        env_kwargs.update(kwargs)  # kwargs 中的值会覆盖环境变量
        super().__init__(**env_kwargs)

    @computed_field
    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[3]  # 项目根目录

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )




@lru_cache
def get_settings() -> Settings:
    # 确保环境变量已加载（在创建 Settings 之前）
    # ENV_PATHS 已经在模块加载时处理过了
    return Settings()


# 在模块加载时创建 settings 实例
# 注意：如果 .env 文件在模块加载后添加，可能需要清除缓存
settings = get_settings()
