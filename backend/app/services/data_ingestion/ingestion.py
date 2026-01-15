"""
数据摄取服务 - arXiv论文数据获取和处理

主要函数：
- ingest_for_date(session, target_date: pendulum.Date, query: str = "all") -> IngestionBatch
  输入：数据库会话，目标日期，查询条件
  输出：摄取批次对象
  功能：获取指定日期的arXiv论文并生成embedding

- _search_arxiv(query: str, target_date: pendulum.Date, max_results: int = 30000) -> Iterator[arxiv.Result]
  输入：查询字符串，目标日期，最大结果数
  输出：arXiv结果迭代器
  功能：从arXiv API搜索论文

- _build_query_for_date(target_date: pendulum.Date) -> str
  输入：目标日期
  输出：arXiv查询字符串
  功能：构建基于提交日期的查询

- _convert_result(result: arxiv.Result) -> PaperData
  输入：arXiv结果对象
  输出：标准化论文数据
  功能：转换arXiv数据格式

数据处理流程：
1. 构建查询 -> 2. 调用arXiv API -> 3. 数据质量检查 -> 4. 保存论文数据 -> 5. 生成embedding

配置参数：
- arxiv_submission_delay_days: arXiv提交延迟天数（默认3天）
- embedding_model_name: embedding模型名称
- 重试机制：3次重试，指数退避

数据库依赖：
- 写入：IngestionBatch, Paper, PaperEmbedding

外部服务依赖：
- arxiv: arXiv API客户端
- app.services.data_quality: validate_and_filter_papers
- app.services.embedding: encode_documents
- DashScope API: embedding生成

错误处理：
- 网络重试机制
- 数据验证和过滤
- 部分失败容错（论文保存成功但embedding失败）
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional

import arxiv
import pendulum
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session
from tenacity import RetryError, retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.models import IngestionBatch, Paper, PaperEmbedding
from app.services.data_ingestion.embedding import encode_documents
from app.services.data_ingestion.data_quality import validate_and_filter_papers

# arxiv 2.3.0 已经默认使用 HTTPS，无需修复
# 新版本使用 requests.Session，会自动读取环境变量中的代理设置（HTTP_PROXY, HTTPS_PROXY）
# 如果需要使用代理，请在 .env 文件或系统环境变量中设置 HTTP_PROXY 和 HTTPS_PROXY


@dataclass
class ArxivPaper:
    arxiv_id: str
    title: str
    summary: str
    authors: List[dict[str, str]]
    categories: List[str]
    submitted_date: pendulum.DateTime
    updated_date: Optional[pendulum.DateTime]
    pdf_url: Optional[str]
    html_url: Optional[str]
    comment: Optional[str]
    doi: Optional[str]
    primary_category: Optional[str]


def _build_query_for_date(target_date: pendulum.Date) -> str:
    # 使用简化版本的查询格式（已验证可用）
    # 直接使用日期字符串 YYYYMMDD 格式，arXiv API 会自动处理时区
    # 格式：submittedDate:[YYYYMMDD000000 TO YYYYMMDD235959]
    # Support both pendulum.Date and datetime.date
    if hasattr(target_date, 'format'):
        date_str = target_date.format("YYYYMMDD")
    else:
        date_str = target_date.strftime("%Y%m%d")
    
    range_query = f"submittedDate:[{date_str}000000 TO {date_str}235959]"
    logger.debug("构建查询：美东日期 {} -> {}", target_date, range_query)
    
    if settings.arxiv_query.lower() == "all":
        return range_query
    return f"({settings.arxiv_query}) AND {range_query}"


@retry(
    stop=stop_after_attempt(settings.arxiv_num_retries),
    wait=wait_exponential(multiplier=max(1.0, settings.arxiv_delay_seconds)),
    retry=retry_if_exception_type((arxiv.HTTPError, ConnectionError)),
)
def _search_arxiv(query: str, target_date: Optional[pendulum.Date] = None) -> Iterable[arxiv.Result]:
    # arxiv 2.3.0+ 使用 Client().results() 而不是 Search.results()
    # arxiv.Client 内部使用 requests.Session，会自动读取环境变量中的代理设置
    # 根据 arXiv API 文档：每次请求最多 2000 条，总共最多 30000 条
    # arxiv 库会自动处理分页（如果 max_results > page_size）
    client = arxiv.Client(
        page_size=min(settings.arxiv_page_size, 2000),  # API 限制：每次请求最多 2000
        delay_seconds=settings.arxiv_delay_seconds,
        num_retries=settings.arxiv_num_retries,
    )
    
    search = arxiv.Search(
        query=query,
        max_results=min(settings.arxiv_max_results, 30000),  # API 限制：总共最多 30000
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,  # 使用 Descending，与简化脚本保持一致
    )
    
    logger.debug("执行 arXiv 查询: {}", query)
    try:
        # 使用 Client.results() 方法（新 API）
        results = list(client.results(search))
        logger.info("成功获取 {} 条结果", len(results))
        
        # 如果使用 submittedDate 查询但没有结果，且提供了目标日期，尝试备用策略
        if len(results) == 0 and target_date is not None and "submittedDate" in query:
            logger.warning("submittedDate 查询未返回结果，尝试备用策略：获取最新论文并过滤")
            return _search_arxiv_fallback(client, target_date)
        
        return results
    except arxiv.HTTPError as e:
        error_str = str(e)
        logger.warning("arXiv API 请求失败: {}", error_str)
        raise
    except ConnectionError as e:
        error_msg = str(e)
        logger.warning("网络连接错误: {}", error_msg)
        # 如果是代理连接问题，提供排查建议
        if "Connection reset" in error_msg or "Connection aborted" in error_msg:
            import os
            proxy_env = os.environ.get("HTTP_PROXY") or os.environ.get("HTTPS_PROXY") or os.environ.get("http_proxy") or os.environ.get("https_proxy")
            if proxy_env:
                logger.error(
                    "检测到代理配置，但代理连接失败。可能的原因：\n"
                    "1. 代理服务器未运行或地址不正确（当前配置: {}）\n"
                    "2. 代理服务器不支持 HTTPS CONNECT 方法\n"
                    "3. 代理服务器需要认证\n"
                    "解决方案：\n"
                    "- 检查代理服务器状态\n"
                    "- 如不需要代理，请移除 .env 文件或系统环境变量中的 HTTP_PROXY/HTTPS_PROXY 配置",
                    proxy_env
                )
        raise


def _search_arxiv_fallback(client: arxiv.Client, target_date: pendulum.Date) -> Iterable[arxiv.Result]:
    """备用策略：获取最近论文并按美东日期过滤"""
    # 目标日期是美东日期，需要将论文的 UTC 时间转换为美东时间后比较日期
    # 这样才能确保获取的是"美东时间该日期"提交的论文
    
    logger.info("获取最新论文并按美东日期过滤: {}", target_date)
    
    # 根据测试发现，arXiv API 分页有特殊限制：
    # - start 必须是 max_results 的倍数才能正常工作
    # - 例如：start=0,100,200... + max_results=100 可以工作
    # - 但 start=50 + max_results=50 会返回 0 条
    # - 使用 start=0,100,200... + max_results=100 的组合可以可靠获取
    
    import urllib.request as libreq
    import urllib.parse
    import xml.etree.ElementTree as ET
    import time
    
    base_url = 'http://export.arxiv.org/api/query'
    max_results_per_request = 100  # 每次请求最多 100 条
    start_step = 100  # start 每次增加 100（必须是 max_results 的倍数）
    
    # 收集所有找到的论文 ID，然后用 arxiv 库重新获取详细信息
    found_paper_ids = []
    consecutive_no_target = 0  # 连续没有目标日期的批次数量
    max_consecutive_no_target = 5  # 连续5批没有目标日期就停止
    
    # 分段获取论文 ID
    for start in range(0, 5000, start_step):  # 最多尝试 50 次（5000 条）
        params = {
            'search_query': 'all',
            'start': start,
            'max_results': max_results_per_request,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }
        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        
        try:
            with libreq.urlopen(url) as response:
                data = response.read()
                xml_data = data.decode('utf-8')
                root = ET.fromstring(xml_data)
                
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                entries = root.findall('atom:entry', ns)
                
                if len(entries) == 0:
                    logger.debug("start={} 返回 0 条论文，停止获取", start)
                    break
                
                batch_target_count = 0
                min_et_date = None
                
                for entry in entries:
                    published = entry.find('atom:published', ns)
                    if published is not None:
                        pub_dt = pendulum.parse(published.text)
                        et_dt = pub_dt.in_timezone("America/New_York")
                        et_date = et_dt.date()
                        
                        if min_et_date is None or et_date < min_et_date:
                            min_et_date = et_date
                        
                        if et_date == target_date:
                            paper_id_elem = entry.find('atom:id', ns)
                            if paper_id_elem is not None:
                                # 提取 arXiv ID（从 http://arxiv.org/abs/2510.12345v1 提取 2510.12345）
                                paper_url = paper_id_elem.text
                                if 'arxiv.org/abs/' in paper_url:
                                    paper_id = paper_url.split('arxiv.org/abs/')[-1]
                                    if paper_id not in found_paper_ids:
                                        found_paper_ids.append(paper_id)
                                        batch_target_count += 1
                
                logger.debug(
                    "start={}: 获取 {} 条论文，其中 {} 条为目标日期（美东日期: {}）",
                    start,
                    len(entries),
                    batch_target_count,
                    target_date,
                )
                
                if batch_target_count > 0:
                    consecutive_no_target = 0
                else:
                    consecutive_no_target += 1
                    if consecutive_no_target >= max_consecutive_no_target and len(found_paper_ids) > 0:
                        logger.debug("连续 {} 批没有目标日期的论文，停止获取", consecutive_no_target)
                        break
                
                # 如果已经过了目标日期，停止获取
                if min_et_date is not None and min_et_date < target_date and len(found_paper_ids) > 0:
                    logger.debug("已过目标日期范围（{} < {}），停止获取", min_et_date, target_date)
                    break
                    
            time.sleep(settings.arxiv_delay_seconds)  # 遵守 API 使用条款
                    
        except Exception as e:
            logger.warning("获取 start={} 时出错: {}，已找到 {} 条论文 ID", start, e, len(found_paper_ids))
            if len(found_paper_ids) > 0:
                break
            continue
    
    logger.info("通过直接 API 调用找到 {} 条目标日期的论文 ID，现在使用 arxiv 库获取详细信息", len(found_paper_ids))
    
    # 使用 arxiv 库通过 id_list 获取详细信息
    if not found_paper_ids:
        return []
    
    # arxiv 库的 id_list 参数接受逗号分隔的 ID 列表
    # 但由于可能有很多 ID，我们需要分批获取
    results = []
    batch_size = 100  # arxiv API 的 id_list 也可能有长度限制
    
    for i in range(0, len(found_paper_ids), batch_size):
        batch_ids = found_paper_ids[i:i+batch_size]
        id_list_str = ','.join(batch_ids)
        
        try:
            search = arxiv.Search(
                id_list=batch_ids,  # arxiv 库接受列表
                max_results=len(batch_ids),
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending,
            )
            
            batch_results = list(client.results(search))
            results.extend(batch_results)
            
            logger.debug("批次 {}-{}: 获取 {} 条论文的详细信息", i, min(i+batch_size-1, len(found_paper_ids)-1), len(batch_results))
            
        except Exception as e:
            logger.warning("获取论文详细信息时出错: {}，批次: {}-{}", e, i, min(i+batch_size-1, len(found_paper_ids)-1))
            continue
    
    logger.info("备用策略：从最新论文中过滤出 {} 条目标美东日期的论文", len(results))
    return results


def _convert_result(result: arxiv.Result) -> ArxivPaper:
    authors = [{"name": author.name} for author in result.authors]
    submitted = pendulum.instance(result.published)
    updated = pendulum.instance(result.updated) if result.updated else None
    return ArxivPaper(
        arxiv_id=result.get_short_id(),
        title=result.title.strip(),
        summary=result.summary.strip(),
        authors=authors,
        categories=list(result.categories),
        submitted_date=submitted,
        updated_date=updated,
        pdf_url=result.pdf_url,
        html_url=result.entry_id,
        comment=result.comment,
        doi=result.doi,
        primary_category=result.primary_category,
    )


def ingest_for_date(session: Session, target_date: pendulum.Date) -> IngestionBatch:
    logger.info("Starting ingestion for {}", target_date)
    query = _build_query_for_date(target_date)
    try:
        results = _search_arxiv(query, target_date=target_date)
    except RetryError as exc:  # pragma: no cover - network failure path
        logger.exception("Failed to fetch arXiv data for {} after retries", target_date)
        raise exc

    papers = [_convert_result(result) for result in results]
    logger.info("Fetched {} papers for {}", len(papers), target_date)

    # 数据质量检查和过滤
    valid_papers, quality_report = validate_and_filter_papers(papers)
    logger.info("数据质量检查: 原始{}篇 -> 有效{}篇", len(papers), len(valid_papers))

    batch = IngestionBatch(
        source_date=target_date,
        fetched_at=pendulum.now("UTC"),
        item_count=len(valid_papers),  # 使用有效论文数量
        query=query,
    )
    session.add(batch)
    session.flush()

    if not valid_papers:
        logger.warning("No valid papers found for {} after quality check", target_date)
        return batch

    # 第一步：先保存所有论文数据到数据库
    logger.info("保存 {} 篇有效论文数据到数据库", len(valid_papers))
    saved_papers = []
    for paper_data in valid_papers:
        paper = session.scalar(select(Paper).where(Paper.arxiv_id == paper_data.arxiv_id))
        if paper is None:
            paper = Paper(
                arxiv_id=paper_data.arxiv_id,
                title=paper_data.title,
                summary=paper_data.summary,
                authors=paper_data.authors,
                categories=paper_data.categories,
                submitted_date=paper_data.submitted_date,
                updated_date=paper_data.updated_date,
                pdf_url=paper_data.pdf_url,
                html_url=paper_data.html_url,
                comment=paper_data.comment,
                doi=paper_data.doi,
                primary_category=paper_data.primary_category,
                source='arxiv',  # 新增：设置数据源为 arxiv
                ingestion_batch_id=batch.id,
            )
            session.add(paper)
        else:
            # 更新已存在的论文信息
            paper.title = paper_data.title
            paper.summary = paper_data.summary
            paper.authors = paper_data.authors
            paper.categories = paper_data.categories
            paper.submitted_date = paper_data.submitted_date
            paper.updated_date = paper_data.updated_date
            paper.pdf_url = paper_data.pdf_url
            paper.html_url = paper_data.html_url
            paper.comment = paper_data.comment
            paper.doi = paper_data.doi
            paper.primary_category = paper_data.primary_category
            paper.ingestion_batch_id = batch.id
        
        session.flush()  # 确保 paper.id 可用
        saved_papers.append(paper)
    
    # 提交事务，确保论文数据已持久化
    session.commit()
    logger.info("论文数据已保存到数据库，开始生成 embedding")
    
    # 第二步：对已保存的论文生成 embedding
    # 只对还没有 embedding 的论文生成（避免重复计算）
    papers_to_embed = [
        paper for paper in saved_papers
        if session.scalar(
            select(PaperEmbedding).where(
                PaperEmbedding.paper_id == paper.id,
                PaperEmbedding.model_name == settings.embedding_model_name,
            )
        ) is None
    ]
    
    if not papers_to_embed:
        logger.info("所有论文已有 embedding，跳过生成")
        return batch
    
    logger.info("为 {} 篇论文生成 embedding", len(papers_to_embed))
    texts = [f"{paper.title}\n\n{paper.summary}" for paper in papers_to_embed]
    
    try:
        embeddings = encode_documents(texts)
    except Exception as e:
        logger.error("生成 embedding 失败，但论文数据已保存: {}", e)
        raise
    
    # 第三步：保存 embedding
    for idx, paper in enumerate(papers_to_embed):
        embedding_vector = embeddings[idx]
        dimension = len(embedding_vector)
        
        embedding = PaperEmbedding(
            paper_id=paper.id,
            model_name=settings.embedding_model_name,
            dimension=dimension,
            vector=embedding_vector,
        )
        session.add(embedding)
    
    session.commit()
    logger.info("Embedding 生成完成并已保存")

    return batch
