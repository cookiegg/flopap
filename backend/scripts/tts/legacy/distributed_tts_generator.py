#!/usr/bin/env python3
"""
混合策略TTS生成器
结合单机优化和分布式处理
"""

import argparse
import asyncio
import json
import time
from pathlib import Path
from typing import List, Tuple
from uuid import UUID

# 添加backend根目录到路径
backend_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_root))

from sqlalchemy import text
from app.db.session import SessionLocal
from large_batch_tts_manager import LargeBatchTTSManager

# 导入分段TTS函数
sys.path.append(str(backend_root / "scripts" / "tts"))
from generate_segmented_tts import process_paper_interpretation


class DistributedTTSCoordinator:
    """分布式TTS协调器"""
    
    def __init__(self, machine_id: int, total_machines: int):
        self.machine_id = machine_id
        self.total_machines = total_machines
        self.progress_file = Path(f"tts_progress_machine_{machine_id}.json")
    
    def get_machine_papers(self, all_papers: List, start_offset: int = 0) -> List:
        """获取当前机器负责的论文"""
        # 跳过start_offset，然后按机器数量分配
        papers_after_offset = all_papers[start_offset:]
        
        # 每台机器处理的论文
        machine_papers = []
        for i, paper in enumerate(papers_after_offset):
            if i % self.total_machines == self.machine_id:
                machine_papers.append(paper)
        
        return machine_papers
    
    async def run_distributed_generation(
        self,
        output_dir: Path,
        voice: str = "zh-CN-XiaoxiaoNeural",
        start_offset: int = 0,
        total_limit: int = 1000
    ):
        """运行分布式生成"""
        
        print(f"🤖 机器 {self.machine_id + 1}/{self.total_machines} 启动")
        print(f"📊 处理范围: 从第 {start_offset} 篇开始，总共 {total_limit} 篇")
        
        # 获取所有论文数据
        db = SessionLocal()
        try:
            query = text("""
                SELECT 
                    pi.paper_id, 
                    p.title,
                    COALESCE(pt.title_zh, p.title) as title_zh,
                    pi.interpretation
                FROM paper_interpretations pi
                JOIN papers p ON pi.paper_id = p.id
                LEFT JOIN paper_translations pt ON pi.paper_id = pt.paper_id
                WHERE pi.interpretation IS NOT NULL 
                AND LENGTH(pi.interpretation) > 100
                ORDER BY pi.paper_id
                LIMIT :limit OFFSET :offset
            """)
            
            result = db.execute(query, {"limit": total_limit, "offset": start_offset})
            all_papers = [(
                row[0] if isinstance(row[0], UUID) else UUID(row[0]), 
                row[1], 
                row[2], 
                row[3]
            ) for row in result.fetchall()]
            
        finally:
            db.close()
        
        # 获取当前机器负责的论文
        machine_papers = self.get_machine_papers(all_papers)
        
        print(f"📚 当前机器负责: {len(machine_papers)} 篇论文")
        
        if not machine_papers:
            print("❌ 当前机器无分配论文")
            return
        
        # 创建TTS管理器
        manager = LargeBatchTTSManager(
            max_concurrent_papers=2,
            max_concurrent_segments=6,
            retry_attempts=3,
            progress_file=str(self.progress_file)
        )
        
        # 开始生成
        await manager.generate_large_batch(
            machine_papers,
            output_dir,
            voice,
            batch_size=5  # 小批次，更好的错误恢复
        )


async def main():
    parser = argparse.ArgumentParser(description="分布式大规模TTS生成")
    parser.add_argument("--machine-id", type=int, default=0, help="机器ID (0-based)")
    parser.add_argument("--total-machines", type=int, default=1, help="总机器数")
    parser.add_argument("--start-offset", type=int, default=0, help="起始偏移")
    parser.add_argument("--total-limit", type=int, default=1000, help="总论文数")
    parser.add_argument("--voice", default="zh-CN-XiaoxiaoNeural", help="语音模型")
    parser.add_argument("--output-dir", default="backend/data/tts_segments_large", help="输出目录")
    
    args = parser.parse_args()
    
    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建分布式协调器
    coordinator = DistributedTTSCoordinator(args.machine_id, args.total_machines)
    
    # 运行分布式生成
    await coordinator.run_distributed_generation(
        output_dir=output_dir,
        voice=args.voice,
        start_offset=args.start_offset,
        total_limit=args.total_limit
    )


if __name__ == "__main__":
    asyncio.run(main())
