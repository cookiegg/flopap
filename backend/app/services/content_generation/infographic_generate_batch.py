"""
信息图生成服务 - 论文可视化内容生成
功能：
- 使用Google Gemini生成论文信息图
- 支持批量信息图生成
- 图片存储和管理
- 信息图模板和样式定制
- 异步处理和并发优化
- 与推荐系统集成，为推荐论文生成可视化内容
"""

import asyncio
from typing import Optional, List, Dict
from uuid import UUID

import httpx
from loguru import logger
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models import Paper, PaperInfographic
from app.core.config import settings


class InfographicGenerator:
    """信息图生成器"""
    
    def __init__(self, api_keys: List[str]):
        self.api_keys = api_keys
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.prompt_template = """你是一个专业的学术信息可视化专家。请根据以下论文信息，生成一个视觉化的信息图网页。

论文标题：{title}

论文摘要：{abstract}

要求：
1. **结构**：按照"问题→方法→结果"三段式组织
2. **技术**：使用纯 HTML + 内联 CSS，不依赖外部库
3. **风格**：
   - 深色主题（背景 #0f172a）
   - 使用渐变色和图标（Unicode emoji 或 CSS 绘制）
   - 卡片式布局，圆角阴影
4. **内容**：
   - 用简洁的中文描述（每段不超过 50 字）
   - 多用视觉元素：流程图、对比图、数据可视化
   - 关键数字和术语用醒目颜色标注
5. **移动端优化**：
   - viewport 设置为 width=device-width, initial-scale=1.0
   - 默认宽度 100%，最大宽度 600px，居中显示
   - 字体大小适合手机阅读（16px 基准）
   - 内边距使用 16-20px，适合手指触控
   - 垂直滚动，总高度约 1000-1400px（适配主流手机屏幕比例）
6. **布局**：优先为竖屏手机设计（9:16 或 9:19.5 比例）

直接输出完整的 HTML 代码，不要有任何解释文字。代码要完整可运行。"""
    
    async def generate_single_infographic(
        self, 
        paper: Dict, 
        api_key: str, 
        client: httpx.AsyncClient,
        task_id: int
    ) -> Optional[str]:
        """生成单篇论文的信息图"""
        
        start_time = asyncio.get_event_loop().time()
        logger.debug("[Task {}] 开始生成信息图: {}...", task_id, paper['title'][:50])
        
        prompt = self.prompt_template.format(
            title=paper['title'],
            abstract=paper['abstract']
        )
        
        try:
            response = await client.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-reasoner",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 4000,
                    "temperature": 0.7
                },
                timeout=60.0
            )
            
            if response.status_code == 200:
                result = response.json()
                html_content = result['choices'][0]['message']['content'].strip()
                
                elapsed = asyncio.get_event_loop().time() - start_time
                logger.success("[Task {}] 完成: {} ({:.1f}s)", 
                             task_id, paper['arxiv_id'], elapsed)
                return html_content
            else:
                logger.error("[Task {}] API错误: {} - {}", 
                           task_id, response.status_code, response.text)
                return None
                
        except Exception as e:
            elapsed = asyncio.get_event_loop().time() - start_time
            logger.error("[Task {}] 异常: {} ({:.1f}s) - {}", 
                        task_id, paper['arxiv_id'], elapsed, str(e))
            return None
    
    async def batch_generate_infographics(
        self, 
        papers: List[Dict], 
        max_concurrent: int = 50
    ) -> List[Dict]:
        """批量生成信息图"""
        
        if not papers:
            logger.warning("没有论文需要生成信息图")
            return []
        
        logger.info("开始为{}篇论文生成信息图，使用{}个API密钥", 
                   len(papers), len(self.api_keys))
        
        # 创建异步HTTP客户端
        async with httpx.AsyncClient() as client:
            # 创建任务
            tasks = []
            for i, paper in enumerate(papers):
                api_key = self.api_keys[i % len(self.api_keys)]
                task = self.generate_single_infographic(paper, api_key, client, i + 1)
                tasks.append((task, paper))
            
            # 限制并发数
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def limited_task(task, paper):
                async with semaphore:
                    html_content = await task
                    return {
                        'paper_id': paper['id'],
                        'arxiv_id': paper['arxiv_id'],
                        'html_content': html_content,
                        'success': html_content is not None
                    }
            
            # 执行所有任务
            results = await asyncio.gather(*[
                limited_task(task, paper) for task, paper in tasks
            ])
            
            return results
    
    def save_infographics_to_db(self, session: Session, results: List[Dict]) -> int:
        """保存信息图到数据库"""
        
        success_count = 0
        
        for result in results:
            if not result['success'] or not result['html_content']:
                continue
            
            try:
                # 检查是否已存在信息图
                existing = session.execute(
                    select(PaperInfographic).where(
                        PaperInfographic.paper_id == result['paper_id']
                    )
                ).scalar_one_or_none()
                
                if existing:
                    # 更新现有记录
                    existing.html_content = result['html_content']
                    existing.model_name = "deepseek-reasoner"
                else:
                    # 创建新记录
                    infographic = PaperInfographic(
                        paper_id=result['paper_id'],
                        html_content=result['html_content'],
                        model_name="deepseek-reasoner"
                    )
                    session.add(infographic)
                
                success_count += 1
                
            except Exception as e:
                logger.error("保存信息图失败 {}: {}", result['arxiv_id'], str(e))
        
        if success_count > 0:
            session.commit()
            logger.success("成功保存{}篇论文的信息图", success_count)
        
        return success_count


def get_papers_without_infographic(
    session: Session,
    source: Optional[str] = None,
    limit: Optional[int] = None
) -> List[Dict]:
    """获取没有信息图的论文"""
    
    if source:
        # 从会议推荐池获取
        query = text("""
            SELECT p.id, p.arxiv_id, p.title, p.summary
            FROM papers p
            JOIN conference_recommendation_pool crp ON p.id = crp.paper_id
            LEFT JOIN paper_infographics pi ON p.id = pi.paper_id
            WHERE crp.source = :source 
              AND crp.is_active = true
              AND pi.id IS NULL
            ORDER BY RANDOM()
        """)
        params = {"source": source}
    else:
        # 从所有论文获取
        query = text("""
            SELECT p.id, p.arxiv_id, p.title, p.summary
            FROM papers p
            LEFT JOIN paper_infographics pi ON p.id = pi.paper_id
            WHERE pi.id IS NULL
            ORDER BY RANDOM()
        """)
        params = {}
    
    if limit:
        query = text(str(query) + f" LIMIT {limit}")
    
    result = session.execute(query, params)
    return [
        {
            "id": row[0],
            "arxiv_id": row[1], 
            "title": row[2],
            "abstract": row[3]
        }
        for row in result
    ]


async def generate_infographics_for_conference(
    session: Session,
    conference_source: str,
    api_keys: List[str],
    limit: int = 100
) -> int:
    """为会议论文生成信息图"""
    
    # 获取需要生成信息图的论文
    papers = get_papers_without_infographic(session, conference_source, limit)
    
    if not papers:
        logger.info("会议{}没有需要生成信息图的论文", conference_source)
        return 0
    
    # 生成信息图
    generator = InfographicGenerator(api_keys)
    results = await generator.batch_generate_infographics(papers)
    
    # 保存到数据库
    success_count = generator.save_infographics_to_db(session, results)
    
    logger.info("会议{}信息图生成完成：成功{}篇，失败{}篇", 
               conference_source, success_count, len(papers) - success_count)
    
    return success_count
