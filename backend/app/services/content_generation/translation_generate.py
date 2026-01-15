"""
🟢 ACTIVE - 纯翻译服务 (translation_pure.py)

纯翻译服务 - 只负责翻译功能，与数据源解耦

主要函数：
- translate_single_paper(client: OpenAI, paper: Paper) -> Optional[Tuple[str, str]]
  输入：OpenAI客户端，论文对象
  输出：(中文标题, 中文摘要)元组或None
  功能：翻译单篇论文的标题和摘要

- batch_translate_papers(session: Session, papers: List[Paper], max_workers: int = 30) -> int
  输入：数据库会话，论文列表，最大并发数
  输出：成功翻译的论文数量
  功能：批量翻译论文列表（不限于推荐池）

- translate_and_save_papers(session: Session, papers: List[Paper], max_workers: int = 30) -> Dict[str, int]
  输入：数据库会话，论文列表，最大并发数
  输出：处理结果统计字典
  功能：翻译并保存到数据库

翻译提示词模板：
```
请将以下英文学术论文的标题和摘要翻译成中文：

标题：{title}
摘要：{abstract}

要求：
1. 保持学术性和准确性
2. 标题简洁明了
3. 摘要完整传达原意
4. 使用规范的中文学术表达

请按以下格式返回：
标题：[中文标题]
摘要：[中文摘要]
```

并发处理机制：
- 使用ThreadPoolExecutor进行并发翻译
- 动态分配论文到不同DeepSeek客户端
- 支持自定义并发数（max_workers）

错误处理：
- 单篇论文翻译失败不影响其他论文
- 详细的错误日志记录
- 返回成功/失败统计信息

数据库操作：
- 读取：Paper（获取标题和摘要）
- 写入：PaperTranslation（保存翻译结果）
- 去重：检查已存在的翻译记录

外部依赖：
- app.services.llm: get_deepseek_clients, distribute_papers
- DeepSeek API: 实际的翻译服务
- OpenAI客户端：API调用接口

与translation.py的区别：
- translation.py：处理推荐池，集成AI解读
- translation_pure.py：纯翻译功能，可处理任意论文列表

调用关系：
- 被translation.py调用：处理推荐池翻译
- 被候选池翻译脚本调用：处理候选池翻译
- 可被其他服务直接调用：灵活的翻译接口
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from loguru import logger
from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Paper, PaperTranslation
from app.services.llm import distribute_papers, get_deepseek_clients


from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((Exception,)),
    reraise=True
)
def translate_single_paper(client: OpenAI, paper: Paper) -> Optional[Tuple[str, str]]:
    """翻译单篇论文的标题和摘要 (带重试机制)"""
    
    prompt = f"""请将以下英文学术论文的标题和摘要翻译成中文：

标题：{paper.title}

摘要：{paper.summary}

要求：
1. 翻译要准确、专业、符合中文学术表达习惯
2. 保持原文的学术严谨性
3. 专业术语要准确翻译
4. 格式：
   标题：[翻译后的标题]
   摘要：[翻译后的摘要]
"""
    
    try:
        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.3
        )
        
        content = response.choices[0].message.content.strip()
        
        # 解析返回的内容
        lines = content.split('\n')
        title_zh = ""
        summary_lines = []
        in_summary = False
        
        for line in lines:
            line = line.strip()
            if line.startswith('标题：'):
                title_zh = line[3:].strip()
            elif line.startswith('摘要：'):
                summary_lines.append(line[3:].strip())
                in_summary = True
            elif in_summary and line:
                summary_lines.append(line)
        
        summary_zh = '\n'.join(summary_lines) if summary_lines else ""
        
        if not title_zh or not summary_zh:
            logger.warning("翻译结果解析不完整: paper_id={}", paper.id)
            return None
            
        return title_zh, summary_zh
        
    except Exception as e:
        logger.error("翻译失败: paper_id={}, error={}", paper.id, str(e))
        return None


def batch_translate_papers(
    session: Session,
    paper_ids: List[UUID],
    max_workers: int = 30,
    force_retranslate: bool = False
) -> Dict[UUID, Tuple[str, str]]:
    """
    纯翻译功能: 批量翻译指定的论文列表
    
    Args:
        session: 数据库会话
        paper_ids: 论文ID列表
        max_workers: 并发线程数
        force_retranslate: 是否强制重新翻译已有翻译的论文
        
    Returns:
        {paper_id: (title_zh, summary_zh)} 成功翻译的结果
    """
    if not paper_ids:
        logger.info("没有需要翻译的论文")
        return {}
    
    logger.info("开始批量翻译 {} 篇论文", len(paper_ids))
    
    # 获取论文对象
    papers_stmt = select(Paper).where(Paper.id.in_(paper_ids))
    papers = list(session.execute(papers_stmt).scalars())
    
    if not papers:
        logger.warning("未找到指定的论文")
        return {}
    
    # 过滤已翻译的论文 (除非强制重新翻译)
    papers_to_translate = []
    if not force_retranslate:
        for paper in papers:
            existing = session.scalar(
                select(PaperTranslation).where(PaperTranslation.paper_id == paper.id)
            )
            if not existing or not existing.title_zh or not existing.summary_zh:
                papers_to_translate.append(paper)
        
        logger.info("过滤后需要翻译的论文: {} 篇", len(papers_to_translate))
    else:
        papers_to_translate = papers
    
    if not papers_to_translate:
        logger.info("所有论文都已有翻译")
        return {}
    
    # 获取LLM客户端并分发论文
    clients = get_deepseek_clients()
    paper_groups = distribute_papers(papers_to_translate, len(clients))
    
    translation_results = {}
    
    # 并发翻译
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_paper = {}
        
        for i, (client, paper_group) in enumerate(zip(clients, paper_groups)):
            for paper in paper_group:
                future = executor.submit(translate_single_paper, client, paper)
                future_to_paper[future] = paper
        
        # 收集结果
        for future in as_completed(future_to_paper):
            paper = future_to_paper[future]
            try:
                result = future.result()
                if result:
                    title_zh, summary_zh = result
                    translation_results[paper.id] = (title_zh, summary_zh)
                    logger.debug("翻译成功: {}", paper.title[:50])
                else:
                    logger.warning("翻译失败: {}", paper.title[:50])
            except Exception as e:
                logger.error("翻译异常: paper={}, error={}", paper.title[:50], str(e))
    
    logger.info("翻译完成: 成功 {} 篇，失败 {} 篇", 
                len(translation_results), 
                len(papers_to_translate) - len(translation_results))
    
    return translation_results


def save_translation_results(
    session: Session,
    translation_results: Dict[UUID, Tuple[str, str]],
    model_name: str = "deepseek-reasoner"
) -> int:
    """
    保存翻译结果到数据库
    
    Args:
        session: 数据库会话
        translation_results: 翻译结果字典
        model_name: 使用的模型名称
        
    Returns:
        成功保存的数量
    """
    if not translation_results:
        return 0
    
    saved_count = 0
    
    for paper_id, (title_zh, summary_zh) in translation_results.items():
        try:
            # 检查是否已存在翻译记录
            existing = session.scalar(
                select(PaperTranslation).where(PaperTranslation.paper_id == paper_id)
            )
            
            if existing:
                # 更新现有记录
                existing.title_zh = title_zh
                existing.summary_zh = summary_zh
                existing.model_name = model_name
            else:
                # 创建新记录
                translation = PaperTranslation(
                    paper_id=paper_id,
                    title_zh=title_zh,
                    summary_zh=summary_zh,
                    model_name=model_name
                )
                session.add(translation)
            
            saved_count += 1
            
        except Exception as e:
            logger.error("保存翻译失败: paper_id={}, error={}", paper_id, str(e))
    
    try:
        session.commit()
        logger.info("翻译结果保存完成: {} 篇", saved_count)
    except Exception as e:
        session.rollback()
        logger.error("翻译结果保存失败: {}", str(e))
        saved_count = 0
    
    return saved_count


def translate_and_save_papers(
    session: Session,
    paper_ids: List[UUID],
    max_workers: int = 30,
    force_retranslate: bool = False
) -> int:
    """
    翻译并保存论文 - 便捷接口
    
    Args:
        session: 数据库会话
        paper_ids: 论文ID列表
        max_workers: 并发线程数
        force_retranslate: 是否强制重新翻译
        
    Returns:
        成功处理的论文数量
    """
    # 批量翻译
    translation_results = batch_translate_papers(
        session, paper_ids, max_workers, force_retranslate
    )
    
    # 保存结果
    saved_count = save_translation_results(session, translation_results)
    
    return saved_count
