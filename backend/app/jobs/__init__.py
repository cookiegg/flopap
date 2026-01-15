"""
后台任务 Jobs 模块

可用任务:
- fetch_arxiv: 获取arXiv论文
- generate_cs_pool: 生成CS候选池
- generate_user_recommendations: 生成用户推荐
- daily_scheduler: 每日调度器 (按顺序执行上述任务)

使用方式:
    python -m app.jobs.daily_scheduler
    python -m app.jobs.fetch_arxiv --target-date 2025-12-29
"""

from .fetch_arxiv import main as fetch_arxiv
from .generate_cs_pool import main as generate_cs_pool
from .generate_user_recommendations import main as generate_user_recommendations
from .daily_scheduler import main as daily_scheduler

__all__ = [
    "fetch_arxiv",
    "generate_cs_pool", 
    "generate_user_recommendations",
    "daily_scheduler",
]
