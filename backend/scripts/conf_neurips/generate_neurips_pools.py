#!/usr/bin/env python3
"""
NeurIPS 2025 推荐池批量生成脚本

功能：
1. 获取所有活跃用户
2. 获取所有neurips2025论文
3. 为每个用户生成个性化排序表
4. 支持并发处理和进度跟踪
"""

import sys
import os
import asyncio
import logging
from datetime import datetime, date
from typing import List, Dict, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
from uuid import UUID

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from sqlalchemy import select, func, distinct
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import Paper, UserFeedback, UserPaperRanking
from app.services.recommendation.user_ranking_service import UserRankingService
from app.services.recommendation.multi_layer_recommendation import MultiLayerRecommendationService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'neurips_pool_generation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class NeurIPSPoolGenerator:
    """NeurIPS推荐池生成器"""
    
    def __init__(self):
        self.session = None
        self.ranking_service = None
        self.ml_service = None
        
    def setup_session(self):
        """设置数据库会话"""
        db_gen = get_db()
        self.session = next(db_gen)
        self.ranking_service = UserRankingService(self.session)
        self.ml_service = MultiLayerRecommendationService(self.session)
        
    def cleanup_session(self):
        """清理数据库会话"""
        if self.session:
            self.session.close()
    
    def get_active_users(self) -> List[str]:
        """获取活跃用户列表"""
        logger.info("获取活跃用户列表...")
        
        # 从UserFeedback表获取有反馈行为的用户
        feedback_users = set(self.session.execute(
            select(distinct(UserFeedback.user_id))
        ).scalars().all())
        
        # 从UserPaperRanking表获取有排序表的用户
        ranking_users = set(self.session.execute(
            select(distinct(UserPaperRanking.user_id))
        ).scalars().all())
        
        # 合并所有活跃用户
        all_users = feedback_users.union(ranking_users)
        
        logger.info(f"找到 {len(all_users)} 个活跃用户")
        return list(all_users)
    
    def get_neurips_papers(self) -> List[UUID]:
        """获取所有neurips2025论文"""
        logger.info("获取neurips2025论文...")
        
        # 查询neurips2025论文
        papers = self.session.execute(
            select(Paper.id).where(
                Paper.source.like('%neurips%')  # 支持neurips2025等变体
            )
        ).scalars().all()
        
        logger.info(f"找到 {len(papers)} 篇neurips论文")
        return list(papers)
    
    def check_existing_ranking(self, user_id: str) -> bool:
        """检查用户是否已有neurips2025排序表"""
        existing = self.session.execute(
            select(UserPaperRanking.id).where(
                UserPaperRanking.user_id == user_id,
                UserPaperRanking.source_key == 'neurips2025'
            )
        ).scalar_one_or_none()
        
        return existing is not None
    
    def generate_user_ranking(self, user_id: str, paper_ids: List[UUID], force_update: bool = False) -> Dict:
        """为单个用户生成neurips排序表"""
        result = {
            'user_id': user_id,
            'success': False,
            'message': '',
            'paper_count': 0
        }
        
        try:
            # 检查是否已存在
            if not force_update and self.check_existing_ranking(user_id):
                result['message'] = 'Already exists, skipped'
                result['success'] = True
                return result
            
            # 启用优化版排序算法
            from app.services.recommendation.user_paper_ranking_optimized import patch_ranking_service
            patch_ranking_service()
            
            # 使用ranking_service生成排序表
            success = self.ranking_service.update_user_ranking(
                user_id=user_id,
                source_key='neurips2025',
                paper_ids=paper_ids,
                force_update=force_update
            )
            
            if success:
                result['success'] = True
                result['message'] = 'Generated successfully (optimized)'
                result['paper_count'] = len(paper_ids)
            else:
                result['message'] = 'Generation failed'
                
        except Exception as e:
            result['message'] = f'Error: {str(e)}'
            logger.error(f"用户 {user_id} 排序表生成失败: {e}")
        
        return result
    
    def generate_batch(self, users: List[str], paper_ids: List[UUID], force_update: bool = False) -> Dict:
        """批量生成推荐池"""
        logger.info(f"开始为 {len(users)} 个用户生成neurips2025排序表...")
        
        results = {
            'total': len(users),
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'details': []
        }
        
        for i, user_id in enumerate(users, 1):
            logger.info(f"处理用户 {i}/{len(users)}: {user_id}")
            
            result = self.generate_user_ranking(user_id, paper_ids, force_update)
            results['details'].append(result)
            
            if result['success']:
                if 'skipped' in result['message']:
                    results['skipped'] += 1
                else:
                    results['success'] += 1
            else:
                results['failed'] += 1
            
            # 每10个用户输出一次进度
            if i % 10 == 0:
                logger.info(f"进度: {i}/{len(users)} - 成功: {results['success']}, 失败: {results['failed']}, 跳过: {results['skipped']}")
        
        return results
    
    def run(self, force_update: bool = False, max_users: int = None):
        """运行推荐池生成"""
        try:
            self.setup_session()
            
            logger.info("=" * 60)
            logger.info("NeurIPS 2025 推荐池批量生成开始")
            logger.info("=" * 60)
            
            # 获取neurips论文
            paper_ids = self.get_neurips_papers()
            if not paper_ids:
                logger.error("未找到neurips论文，退出")
                return
            
            # 获取活跃用户
            users = self.get_active_users()
            if not users:
                logger.error("未找到活跃用户，退出")
                return
            
            # 限制用户数量（用于测试）
            if max_users:
                users = users[:max_users]
                logger.info(f"限制处理用户数量为: {max_users}")
            
            # 批量生成
            start_time = datetime.now()
            results = self.generate_batch(users, paper_ids, force_update)
            end_time = datetime.now()
            
            # 输出结果
            logger.info("=" * 60)
            logger.info("生成完成！")
            logger.info(f"总用户数: {results['total']}")
            logger.info(f"成功生成: {results['success']}")
            logger.info(f"生成失败: {results['failed']}")
            logger.info(f"已存在跳过: {results['skipped']}")
            logger.info(f"耗时: {end_time - start_time}")
            logger.info("=" * 60)
            
            # 保存详细结果
            self.save_results(results, start_time)
            
        except Exception as e:
            logger.error(f"生成过程出错: {e}")
            raise
        finally:
            self.cleanup_session()
    
    def save_results(self, results: Dict, start_time: datetime):
        """保存结果到文件"""
        import json
        
        result_file = f"neurips_pool_results_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
        result_path = os.path.join(os.path.dirname(__file__), 'temp_results', result_file)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(result_path), exist_ok=True)
        
        # 转换UUID为字符串以便JSON序列化
        serializable_results = {
            'timestamp': start_time.isoformat(),
            'summary': {
                'total': results['total'],
                'success': results['success'],
                'failed': results['failed'],
                'skipped': results['skipped']
            },
            'details': results['details']
        }
        
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"详细结果已保存到: {result_path}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='NeurIPS 2025 推荐池批量生成')
    parser.add_argument('--force', action='store_true', help='强制更新已存在的排序表')
    parser.add_argument('--max-users', type=int, help='限制处理的最大用户数（用于测试）')
    parser.add_argument('--dry-run', action='store_true', help='试运行，只显示统计信息')
    
    args = parser.parse_args()
    
    if args.dry_run:
        # 试运行模式
        generator = NeurIPSPoolGenerator()
        generator.setup_session()
        
        users = generator.get_active_users()
        papers = generator.get_neurips_papers()
        
        print(f"📊 统计信息:")
        print(f"  活跃用户数: {len(users)}")
        print(f"  neurips论文数: {len(papers)}")
        
        if args.max_users:
            print(f"  将处理用户数: {min(len(users), args.max_users)}")
        else:
            print(f"  将处理用户数: {len(users)}")
        
        generator.cleanup_session()
        return
    
    # 正式运行
    generator = NeurIPSPoolGenerator()
    generator.run(force_update=args.force, max_users=args.max_users)


if __name__ == '__main__':
    main()
