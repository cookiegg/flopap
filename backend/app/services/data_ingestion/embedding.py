"""
Embedding服务 - 论文向量化和相似度计算
功能：
- 使用DashScope生成论文embedding向量
- 支持批量embedding生成
- 向量分块处理和并发优化
- 用于推荐算法中的相似度计算
- 支持用户画像向量生成
"""
from __future__ import annotations

from functools import lru_cache
from typing import Iterable, Iterator, List, Sequence

from loguru import logger
from openai import OpenAI

from app.core.config import settings


def _chunk(iterable: Sequence[str], size: int) -> Iterator[Sequence[str]]:
    if size <= 0:
        raise ValueError("chunk size must be positive")
    for i in range(0, len(iterable), size):
        yield iterable[i : i + size]


@lru_cache(maxsize=1)
def get_embedding_client() -> OpenAI:
    api_key = settings.dashscope_api_key
    if not api_key:
        raise RuntimeError("DASHSCOPE_API_KEY 未配置，无法调用嵌入服务")
    return OpenAI(api_key=api_key, base_url=settings.dashscope_base_url)


def encode_documents(texts: Iterable[str]) -> List[List[float]]:
    texts_list = list(texts)
    if not texts_list:
        return []

    client = get_embedding_client()
    max_batch = max(1, settings.embedding_max_batch_size)
    all_vectors: List[List[float]] = []

    for batch in _chunk(texts_list, max_batch):
        logger.debug("请求DashScope Embedding，批次大小 {}", len(batch))
        response = client.embeddings.create(
            model=settings.embedding_model_name,
            input=list(batch),
            dimensions=settings.embedding_dimension,
        )
        # OpenAI兼容接口保证与输入顺序一致
        batch_vectors = [
            [float(value) for value in item.embedding]
            for item in sorted(response.data, key=lambda d: d.index)
        ]
        all_vectors.extend(batch_vectors)

    return all_vectors
