"""
用户内容管理服务 - 处理用户生成内容的保存和校验
"""
import hashlib
import re
import uuid
from typing import Optional
from sqlalchemy.orm import Session
from app.models.paper import PaperVisual
from app.models import PaperInfographic


def validate_html_content(html: str) -> bool:
    """验证HTML内容安全性"""
    if not html or len(html.strip()) == 0:
        return False
    if len(html) > 1024 * 1024:  # 1MB限制
        return False
    
    # 危险模式检查 - 只检查真正危险的内容
    # Note: We allow <script> tags because the frontend injects resize/swipe scripts.
    # These are necessary for the infographic to function properly in the iframe.
    dangerous_patterns = [
        r'javascript:',   # javascript协议 (inline handlers)
        r'vbscript:',     # vbscript协议
        r'data:text/html',  # data URL with HTML
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, html, re.IGNORECASE | re.DOTALL):
            return False
    
    return True


def verify_content_integrity(content: str, checksum: str) -> bool:
    """验证内容完整性"""
    expected = hashlib.sha256(content.encode()).hexdigest()
    return expected == checksum


def save_user_infographic(
    db: Session,
    paper_id: uuid.UUID,
    html_content: str,
    checksum: Optional[str] = None,
    model_name: str = "deepseek-chat"
) -> Optional[uuid.UUID]:
    """保存用户信息图"""
    # 内容验证
    if not validate_html_content(html_content):
        return None
    
    # 完整性校验
    if checksum and not verify_content_integrity(html_content, checksum):
        return None
    
    # 检查是否已存在，存在则更新
    existing = db.query(PaperInfographic).filter(
        PaperInfographic.paper_id == paper_id
    ).first()
    
    if existing:
        existing.html_content = html_content
        existing.model_name = model_name
        infographic_id = existing.id
    else:
        infographic = PaperInfographic(
            id=str(uuid.uuid4()),
            paper_id=str(paper_id),
            html_content=html_content,
            model_name=model_name
        )
        db.add(infographic)
        infographic_id = infographic.id
    
    db.commit()
    return infographic_id


def save_user_visualization(
    db: Session,
    paper_id: uuid.UUID,
    image_data: str,
    checksum: Optional[str] = None,
    model_name: str = "gemini-2.5-flash-image"
) -> Optional[uuid.UUID]:
    """保存用户可视化图"""
    # 基础验证
    if not image_data or len(image_data) > 10 * 1024 * 1024:  # 10MB限制
        return None
    
    # 完整性校验
    if checksum and not verify_content_integrity(image_data, checksum):
        return None
    
    # 检查是否已存在，存在则更新
    existing = db.query(PaperVisual).filter(
        PaperVisual.paper_id == paper_id
    ).first()
    
    if existing:
        existing.image_data = image_data
        existing.model_name = model_name
        visual_id = existing.id
    else:
        visual = PaperVisual(
            id=uuid.uuid4(),
            paper_id=paper_id,
            image_data=image_data,
            model_name=model_name
        )
        db.add(visual)
        visual_id = visual.id
    
    db.commit()
    return visual_id
