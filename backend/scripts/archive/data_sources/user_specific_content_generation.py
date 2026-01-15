#!/usr/bin/env python3
"""
用户特定内容生成脚本
根据用户ID和数据源类型获取推荐池，按需生成翻译、AI解读和信息图
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import asyncio
from typing import List, Optional
from sqlalchemy.orm import Session
from database.connection import get_db_session
from database.models import User, Paper, Recommendation, Translation
from services.translation_pure import translate_paper
from services.ai_interpretation_pure import generate_ai_interpretation
from services.infographic_pure import generate_infographic

class UserContentGenerator:
    def __init__(self):
        self.db = next(get_db_session())
    
    def get_user_recommendation_pool(self, user_id: int, data_source: str) -> List[int]:
        """获取用户特定数据源的推荐池paper_ids"""
        recommendations = self.db.query(Recommendation).filter(
            Recommendation.user_id == user_id,
            Recommendation.data_source == data_source
        ).all()
        return [rec.paper_id for rec in recommendations]
    
    def get_missing_translations(self, paper_ids: List[int]) -> List[int]:
        """获取缺少翻译的paper_ids"""
        existing = self.db.query(Translation.paper_id).filter(
            Translation.paper_id.in_(paper_ids),
            Translation.title_zh.isnot(None)
        ).all()
        existing_ids = {t[0] for t in existing}
        return [pid for pid in paper_ids if pid not in existing_ids]
    
    def get_missing_interpretations(self, paper_ids: List[int]) -> List[int]:
        """获取缺少AI解读的paper_ids"""
        existing = self.db.query(Translation.paper_id).filter(
            Translation.paper_id.in_(paper_ids),
            Translation.ai_interpretation.isnot(None)
        ).all()
        existing_ids = {ai[0] for ai in existing}
        return [pid for pid in paper_ids if pid not in existing_ids]
    
    def get_missing_infographics(self, paper_ids: List[int]) -> List[int]:
        """获取缺少信息图的paper_ids"""
        from database.models import Infographic
        existing = self.db.query(Infographic.paper_id).filter(
            Infographic.paper_id.in_(paper_ids)
        ).all()
        existing_ids = {ig[0] for ig in existing}
        return [pid for pid in paper_ids if pid not in existing_ids]
    
    async def generate_user_content(self, user_id: int, data_source: str, 
                                  generate_translation: bool = True, 
                                  generate_interpretation: bool = True,
                                  generate_infographic_flag: bool = True):
        """为特定用户和数据源生成内容"""
        print(f"开始为用户 {user_id} 的 {data_source} 数据源生成内容...")
        
        # 获取推荐池
        paper_ids = self.get_user_recommendation_pool(user_id, data_source)
        if not paper_ids:
            print(f"用户 {user_id} 在 {data_source} 数据源中没有推荐")
            return
        
        print(f"找到 {len(paper_ids)} 篇推荐论文")
        
        # 生成翻译
        if generate_translation:
            missing_translations = self.get_missing_translations(paper_ids)
            if missing_translations:
                print(f"需要翻译 {len(missing_translations)} 篇论文")
                for paper_id in missing_translations:
                    try:
                        await translate_paper(paper_id)
                        print(f"✓ 完成论文 {paper_id} 翻译")
                    except Exception as e:
                        print(f"✗ 论文 {paper_id} 翻译失败: {e}")
            else:
                print("所有推荐论文已有翻译")
        
        # 生成AI解读
        if generate_interpretation:
            missing_interpretations = self.get_missing_interpretations(paper_ids)
            if missing_interpretations:
                print(f"需要AI解读 {len(missing_interpretations)} 篇论文")
                for paper_id in missing_interpretations:
                    try:
                        await generate_ai_interpretation(paper_id)
                        print(f"✓ 完成论文 {paper_id} AI解读")
                    except Exception as e:
                        print(f"✗ 论文 {paper_id} AI解读失败: {e}")
            else:
                print("所有推荐论文已有AI解读")
        
        # 生成信息图
        if generate_infographic_flag:
            missing_infographics = self.get_missing_infographics(paper_ids)
            if missing_infographics:
                print(f"需要信息图 {len(missing_infographics)} 篇论文")
                for paper_id in missing_infographics:
                    try:
                        success = await generate_infographic(paper_id)
                        if success:
                            print(f"✓ 完成论文 {paper_id} 信息图")
                        else:
                            print(f"✗ 论文 {paper_id} 信息图失败")
                    except Exception as e:
                        print(f"✗ 论文 {paper_id} 信息图失败: {e}")
            else:
                print("所有推荐论文已有信息图")
        
        print(f"用户 {user_id} 的 {data_source} 内容生成完成")

async def main():
    if len(sys.argv) < 3:
        print("用法: python user_specific_content_generation.py <user_id> <data_source> [--translation] [--interpretation] [--infographic]")
        print("示例: python user_specific_content_generation.py 1 arxiv --translation --interpretation --infographic")
        sys.exit(1)
    
    user_id = int(sys.argv[1])
    data_source = sys.argv[2]
    
    generate_translation = "--translation" in sys.argv
    generate_interpretation = "--interpretation" in sys.argv
    generate_infographic_flag = "--infographic" in sys.argv
    
    if not any([generate_translation, generate_interpretation, generate_infographic_flag]):
        generate_translation = generate_interpretation = generate_infographic_flag = True
    
    generator = UserContentGenerator()
    await generator.generate_user_content(
        user_id, data_source, generate_translation, generate_interpretation, generate_infographic_flag
    )

if __name__ == "__main__":
    asyncio.run(main())
