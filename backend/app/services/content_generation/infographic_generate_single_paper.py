"""
统一信息图生成服务
使用PaperInfographic表，与batch服务保持一致
"""

import os
import asyncio
from typing import Optional
from uuid import UUID
import httpx
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models import Paper, PaperInfographic

# DeepSeek API配置
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

def get_deepseek_api_key() -> str:
    """获取DeepSeek API密钥"""
    for i in range(1, 51):
        key = os.getenv(f"DEEPSEEK_API_KEY_{i:02d}")
        if key:
            return key
    raise ValueError("未找到DeepSeek API密钥")

INFOGRAPHIC_PROMPT = """你是一个专业的学术信息可视化专家。请根据以下论文信息，生成一个视觉化的信息图网页。

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

直接输出完整的 HTML 代码，不要有任何解释文字。"""

async def generate_infographic(paper_id: UUID) -> bool:
    """为指定论文生成信息图"""
    db = SessionLocal()
    
    try:
        # 获取论文信息
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            print(f"论文 {paper_id} 不存在")
            return False
        
        # 检查是否已有信息图
        existing = db.query(PaperInfographic).filter(PaperInfographic.paper_id == paper_id).first()
        if existing:
            print(f"论文 {paper_id} 已有信息图")
            return True
        
        # 生成信息图
        api_key = get_deepseek_api_key()
        prompt = INFOGRAPHIC_PROMPT.format(
            title=paper.title,
            abstract=paper.summary
        )
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                DEEPSEEK_API_URL,
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
        
        if response.status_code != 200:
            print(f"API错误: {response.status_code}")
            return False
        
        result = response.json()
        html_content = result['choices'][0]['message']['content'].strip()
        
        # 保存信息图
        infographic = PaperInfographic(
            paper_id=paper_id,
            html_content=html_content,
            model_name="deepseek-reasoner"
        )
        db.add(infographic)
        db.commit()
        return True
        
    except Exception as e:
        print(f"生成信息图失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()
