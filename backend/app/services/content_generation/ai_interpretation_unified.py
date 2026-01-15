"""
统一AI解读服务 - 新架构
只生成纯文本格式，包含质量控制和重试机制
"""

from typing import Optional
from openai import OpenAI
from loguru import logger
from app.models import Paper

def generate_ai_interpretation_unified(client: OpenAI, paper: Paper) -> Optional[str]:
    """
    统一AI解读生成 - 新架构
    只生成纯文本格式，确保内容完整性
    """
    
    # 提取作者姓名
    author_names = []
    for author in paper.authors:
        if isinstance(author, dict) and 'name' in author:
            author_names.append(author['name'])
        elif isinstance(author, str):
            author_names.append(author)
    
    prompt = f"""STRICT LENGTH REQUIREMENT: Your response must be between 800-1200 Chinese characters total. Responses exceeding 1200 characters will be rejected.

Please provide a concise analysis of the following paper using exactly 800-1200 Chinese characters. Keep explanations brief and focus only on the most essential points.

Analyze the following paper abstract and provide 3 distinct key takeaways.

CRITICAL INSTRUCTION (Target Audience: First-Year College Student):

- Your goal is to explain this paper to a university freshman concisely.
- Keep each section brief and to the point.

  - Example: Instead of "manifold alignment", say "manifold alignment (matching up the underlying structures of different data types)".

- Tone: Educational, Objective, and Clear. Avoid hype (no "revolutionary", "amazing"), but use analogies to make concepts stick.

- Focus: Explain the *intuition* and *concepts* rather than just listing technical specs.

Please structure the 3 takeaways to specifically cover the following distinct aspects:

1. Context & Motivation: What is the real-world problem? Why were previous methods stuck?

2. Methodology Details (Crucial): What is the clever idea here? Explain the mechanism simply (use analogies if helpful).

3. Results & Impact: What is the actual improvement? (e.g., "It runs 2x faster", "It makes fewer errors").

Return the output in markdown format with Chinese text (use ## for section headers):

## 研究背景
[Context & Motivation content in Chinese]

## 核心方法  
[Methodology Details content in Chinese]

## 主要贡献
[Results & Impact content in Chinese]

Paper Title: {paper.title}
Author(s): {', '.join(author_names)}
Categories: {', '.join(paper.categories)}
Abstract: {paper.summary}"""
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[
                    {"role": "system", "content": "你是专业的学术论文解读助手，用清晰的中文提供完整的论文分析。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1200,  # 进一步减少token限制以严格控制长度
                temperature=0.7
            )
            
            interpretation = response.choices[0].message.content.strip()
            
            # 质量检查
            if is_interpretation_complete(interpretation):
                logger.success("AI解读生成成功: paper_id={}, length={}", paper.id, len(interpretation))
                return interpretation
            else:
                logger.warning("AI解读质量不达标，重试: attempt={}", attempt + 1)
                
        except Exception as e:
            logger.error("AI解读生成失败: paper_id={}, attempt={}, error={}", paper.id, attempt + 1, str(e))
    
    logger.error("AI解读生成最终失败: paper_id={}", paper.id)
    return None

def is_interpretation_complete(content: str) -> bool:
    """检查AI解读内容是否完整"""
    if not content or len(content) < 200:
        return False
    
    # 检查是否包含关键部分
    required_sections = ["背景", "方法", "结果", "影响"]
    section_count = sum(1 for section in required_sections if section in content)
    
    # 检查是否被截断（常见截断标志）
    truncation_indicators = ["...", "未完", "待续", "```", "{", "}"]
    has_truncation = any(indicator in content[-100:] for indicator in truncation_indicators)
    
    return section_count >= 2 and not has_truncation


