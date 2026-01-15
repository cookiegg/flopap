"""
LLM服务 - 大语言模型客户端管理和工具函数

主要函数：
- get_deepseek_clients(count: int = None) -> List[OpenAI]
  输入：客户端数量（可选）
  输出：OpenAI客户端列表
  功能：创建DeepSeek客户端池，支持并发处理
  缓存：使用@lru_cache缓存客户端实例

- distribute_papers(papers: List[Paper], client_count: int) -> List[List[Paper]]
  输入：论文列表，客户端数量
  输出：分配给各客户端的论文列表
  功能：将论文均匀分配给不同客户端

配置参数：
- DEEPSEEK_API_KEY: DeepSeek API密钥
- deepseek_model_name: 模型名称
- deepseek_base_url: API基础URL

客户端配置：
- 每个客户端使用相同的API密钥
- 支持自定义base_url
- 内置重试机制（@retry装饰器）

重试策略：
- 最大重试次数：3次
- 等待策略：指数退避（1s, 2s, 4s）
- 适用于网络错误和API限流

使用场景：
- 翻译服务：并发翻译多篇论文
- AI解读服务：并发生成解读内容
- 信息图生成：并发处理可视化任务

性能优化：
- 客户端池复用，避免重复创建
- 负载均衡分配任务
- 支持动态调整并发数

调用关系：
- 被translation.py调用：批量翻译
- 被ai_interpretation.py调用：批量解读
- 被其他内容生成服务调用
"""
from __future__ import annotations

from functools import lru_cache
from typing import List, Tuple

from loguru import logger
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.models import Paper


@lru_cache(maxsize=1)
def get_deepseek_clients() -> List[OpenAI]:
    """获取所有可用的LLM客户端列表（DeepSeek或DashScope）"""
    import httpx
    import os
    
    api_keys = settings.deepseek_api_keys
    
    # Create HTTP client without proxy settings
    try:
        # For HTTpx < 0.24, use proxies=None might be valid or invalid depending on version.
        # But user asked to remove proxy. 
        # Safest way to disable proxy in httpx is usually transport or trust_env=False.
        # However, checking the error "unexpected keyword argument 'proxies'", 
        # it suggests httpx.Client(proxies=...) is failing.
        # Maybe httpx version is very new or very old?
        # In httpx 0.24+, params changed? 
        # Actually, let's just use trust_env=False which ignores env vars.
        
        http_client = httpx.Client(trust_env=False)
        
        # If no DeepSeek api key, try DashScope
        if not api_keys:
            if settings.dashscope_api_key:
                logger.info("Using DashScope API")
                client = OpenAI(
                    api_key=settings.dashscope_api_key, 
                    base_url=settings.dashscope_base_url,
                    http_client=http_client
                )
                return [client]
            raise RuntimeError("DEEPSEEK_API_KEY_01 to _30 or DASHSCOPE_API_KEY not configured")
        
        clients = []
        for api_key in api_keys:
            client = OpenAI(
                api_key=api_key, 
                base_url=settings.deepseek_base_url,
                http_client=httpx.Client(trust_env=False)
            )
            clients.append(client)
        
        logger.info("Initialized {} DeepSeek clients", len(clients))
        return clients
    
    except Exception as e:
        logger.error(f"Failed to initialize LLM clients: {e}")
        raise


def distribute_papers(papers: List[Paper], num_clients: int) -> List[List[Paper]]:
    """
    负载均衡分配论文列表给多个客户端
    
    策略：
    - papers_per_client = len(papers) // num_clients (每客户端基础分配数)
    - extra = len(papers) % num_clients (剩余论文数)
    - 前extra个客户端分配 papers_per_client + 1 篇
    - 其余客户端分配 papers_per_client 篇
    
    这样可以确保每个客户端分配数量最多相差1篇，避免不均衡
    """
    if num_clients == 0:
        raise ValueError("客户端数量必须大于0")
    
    if not papers:
        return [[] for _ in range(num_clients)]
    
    papers_per_client = len(papers) // num_clients
    extra = len(papers) % num_clients
    
    distributed: List[List[Paper]] = []
    start_idx = 0
    
    for i in range(num_clients):
        # 前extra个客户端多分配1篇
        count = papers_per_client + (1 if i < extra else 0)
        end_idx = start_idx + count
        distributed.append(papers[start_idx:end_idx])
        start_idx = end_idx
    
    # 验证分配正确性
    total_distributed = sum(len(batch) for batch in distributed)
    assert total_distributed == len(papers), f"分配错误：总数{len(papers)} != 分配总数{total_distributed}"
    
    # 验证负载均衡（最多相差1篇）
    sizes = [len(batch) for batch in distributed if batch]  # 只考虑非空批次
    if sizes:
        min_size = min(sizes)
        max_size = max(sizes)
        assert max_size - min_size <= 1, f"负载不均衡：最小{min_size}，最大{max_size}"
    
    logger.debug(
        "论文分配完成：总{}篇，{}个客户端，每客户端{}篇，前{}个客户端多分配1篇",
        len(papers),
        num_clients,
        papers_per_client,
        extra,
    )
    
    return distributed


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def translate_text(client: OpenAI, text: str, target_lang: str = "zh") -> str:
    """
    使用指定客户端翻译文本
    
    Args:
        client: OpenAI客户端
        text: 待翻译文本
        target_lang: 目标语言，默认为中文
        
    Returns:
        翻译后的文本
    """
    if not text or not text.strip():
        return text
    
    prompt = f"请将以下英文文本翻译成中文，只返回翻译结果，不要添加任何解释或其他内容：\n\n{text}"
    
    try:
        response = client.chat.completions.create(
            model=settings.deepseek_model_name,
            messages=[
                {"role": "system", "content": "你是一个专业的学术论文翻译助手，擅长将英文论文内容准确翻译成中文。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        
        translated = response.choices[0].message.content.strip()
        if not translated:
            raise ValueError("翻译结果为空")
        return translated
    except Exception as e:
        logger.error("翻译失败：{} - 文本长度：{}", str(e), len(text))
        raise


# DEPRECATED FUNCTION REMOVED: generate_interpretation
# Use app.services.ai_interpretation_unified.generate_ai_interpretation_unified instead


# DEPRECATED FUNCTION REMOVED: process_paper_translation
# Use translate_text() and generate_ai_interpretation_unified() separately instead

