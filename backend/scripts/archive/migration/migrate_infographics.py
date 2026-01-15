#!/usr/bin/env python3
"""
迁移信息图数据从 paper_translations 到 infographics 表
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.session import SessionLocal
from app.models.paper import Paper, PaperTranslation
from app.models.infographic import Infographic
from sqlalchemy import text

def migrate_infographics():
    """迁移信息图数据"""
    db = SessionLocal()
    
    try:
        # 获取所有有信息图的翻译记录
        translations_with_infographics = db.execute(text("""
            SELECT pt.paper_id, pt.infographic_html, pt.model_name, pt.created_at, pt.updated_at
            FROM paper_translations pt 
            WHERE pt.infographic_html IS NOT NULL 
            AND pt.infographic_html != ''
        """)).fetchall()
        
        print(f"找到 {len(translations_with_infographics)} 个信息图需要迁移")
        
        migrated_count = 0
        skipped_count = 0
        
        for row in translations_with_infographics:
            paper_id, html_content, model_name, created_at, updated_at = row
            
            # 检查是否已存在
            existing = db.query(Infographic).filter(
                Infographic.paper_id == paper_id
            ).first()
            
            if existing:
                print(f"跳过已存在的信息图: {paper_id}")
                skipped_count += 1
                continue
            
            # 创建新的信息图记录
            infographic = Infographic(
                paper_id=paper_id,
                html_content=html_content,
                model_name=model_name or "deepseek-chat"
            )
            
            db.add(infographic)
            migrated_count += 1
            
            if migrated_count % 10 == 0:
                print(f"已迁移 {migrated_count} 个信息图...")
        
        db.commit()
        print(f"✅ 迁移完成: {migrated_count} 个新增, {skipped_count} 个跳过")
        
        # 验证迁移结果
        new_count = db.query(Infographic).count()
        print(f"新表中总计: {new_count} 个信息图")
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_infographics()
