#!/usr/bin/env python3
"""
大规模TTS生成管理器
支持断点续传、错误重试、进度监控
"""

import asyncio
import time
import json
from pathlib import Path
from typing import List, Dict, Set
from uuid import UUID
from dataclasses import dataclass, asdict

@dataclass
class BatchProgress:
    """批次进度跟踪"""
    total_papers: int = 0
    completed_papers: int = 0
    failed_papers: int = 0
    current_batch: int = 0
    total_batches: int = 0
    start_time: float = 0
    estimated_remaining: float = 0
    completed_paper_ids: Set[str] = None
    failed_paper_ids: Set[str] = None
    
    def __post_init__(self):
        if self.completed_paper_ids is None:
            self.completed_paper_ids = set()
        if self.failed_paper_ids is None:
            self.failed_paper_ids = set()


class LargeBatchTTSManager:
    """大规模TTS生成管理器"""
    
    def __init__(self, 
                 max_concurrent_papers: int = 2,  # 同时处理的论文数
                 max_concurrent_segments: int = 6,  # 每篇论文的片段并发数
                 retry_attempts: int = 3,
                 progress_file: str = "tts_progress.json"):
        
        self.max_concurrent_papers = max_concurrent_papers
        self.max_concurrent_segments = max_concurrent_segments
        self.retry_attempts = retry_attempts
        self.progress_file = Path(progress_file)
        
        # 全局并发控制 (2论文 × 6片段 = 12并发，略超10但在可控范围)
        self.global_semaphore = asyncio.Semaphore(max_concurrent_papers * max_concurrent_segments)
        
        self.progress = BatchProgress()
        self.load_progress()
    
    def load_progress(self):
        """加载进度文件"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    data = json.load(f)
                    self.progress.completed_paper_ids = set(data.get('completed_paper_ids', []))
                    self.progress.failed_paper_ids = set(data.get('failed_paper_ids', []))
                    self.progress.completed_papers = len(self.progress.completed_paper_ids)
                    self.progress.failed_papers = len(self.progress.failed_paper_ids)
                    print(f"📂 加载进度: 已完成 {self.progress.completed_papers} 篇")
            except Exception as e:
                print(f"⚠️  进度文件加载失败: {e}")
    
    def save_progress(self):
        """保存进度文件"""
        try:
            data = {
                'total_papers': self.progress.total_papers,
                'completed_papers': self.progress.completed_papers,
                'failed_papers': self.progress.failed_papers,
                'current_batch': self.progress.current_batch,
                'completed_paper_ids': list(self.progress.completed_paper_ids),
                'failed_paper_ids': list(self.progress.failed_paper_ids),
                'timestamp': time.time()
            }
            with open(self.progress_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️  进度保存失败: {e}")
    
    async def process_single_paper_with_retry(self, paper_data, output_dir, voice):
        """处理单篇论文，包含重试机制"""
        paper_id, title_en, title_zh, interpretation = paper_data
        
        # 检查是否已完成
        if str(paper_id) in self.progress.completed_paper_ids:
            return True
        
        for attempt in range(self.retry_attempts):
            try:
                # 使用全局信号量控制总并发数
                async with self.global_semaphore:
                    # 这里调用你的分段TTS生成函数
                    from generate_segmented_tts import process_paper_interpretation
                    
                    result = await process_paper_interpretation(
                        paper_id, title_en, title_zh, interpretation, output_dir, voice
                    )
                    
                    if result and result['successful_segments'] > 0:
                        self.progress.completed_paper_ids.add(str(paper_id))
                        self.progress.completed_papers += 1
                        return True
                    
            except Exception as e:
                print(f"  ❌ 论文 {paper_id} 第 {attempt + 1} 次尝试失败: {e}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(2 ** attempt)  # 指数退避
        
        # 所有重试都失败
        self.progress.failed_paper_ids.add(str(paper_id))
        self.progress.failed_papers += 1
        return False
    
    async def process_batch(self, papers_batch, output_dir, voice):
        """处理一个批次的论文"""
        # 限制同时处理的论文数量
        semaphore = asyncio.Semaphore(self.max_concurrent_papers)
        
        async def limited_process(paper_data):
            async with semaphore:
                return await self.process_single_paper_with_retry(paper_data, output_dir, voice)
        
        # 并发处理批次内的论文
        tasks = [limited_process(paper) for paper in papers_batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return sum(1 for r in results if r is True)
    
    async def generate_large_batch(self, papers, output_dir, voice, batch_size=10):
        """大规模批量生成"""
        self.progress.total_papers = len(papers)
        self.progress.start_time = time.time()
        
        # 过滤已完成的论文
        remaining_papers = [
            p for p in papers 
            if str(p[0]) not in self.progress.completed_paper_ids
        ]
        
        if not remaining_papers:
            print("✅ 所有论文都已完成!")
            return
        
        print(f"🎵 开始大规模TTS生成")
        print(f"总论文数: {len(papers)}")
        print(f"剩余论文: {len(remaining_papers)}")
        print(f"批次大小: {batch_size}")
        print(f"并发配置: {self.max_concurrent_papers}论文 × {self.max_concurrent_segments}片段")
        
        # 分批处理
        batches = [remaining_papers[i:i+batch_size] for i in range(0, len(remaining_papers), batch_size)]
        self.progress.total_batches = len(batches)
        
        for batch_idx, batch in enumerate(batches):
            self.progress.current_batch = batch_idx + 1
            
            print(f"\n📦 处理批次 {batch_idx + 1}/{len(batches)} ({len(batch)} 篇论文)")
            
            batch_start = time.time()
            success_count = await self.process_batch(batch, output_dir, voice)
            batch_time = time.time() - batch_start
            
            # 更新进度
            self.save_progress()
            
            # 计算预估剩余时间
            if self.progress.completed_papers > 0:
                avg_time_per_paper = (time.time() - self.progress.start_time) / self.progress.completed_papers
                remaining_papers_count = self.progress.total_papers - self.progress.completed_papers
                self.progress.estimated_remaining = avg_time_per_paper * remaining_papers_count
            
            print(f"  ✅ 批次完成: {success_count}/{len(batch)} 篇成功")
            print(f"  ⏱️  批次耗时: {batch_time:.1f}s")
            print(f"  📊 总进度: {self.progress.completed_papers}/{self.progress.total_papers} ({self.progress.completed_papers/self.progress.total_papers*100:.1f}%)")
            
            if self.progress.estimated_remaining > 0:
                print(f"  🕐 预估剩余: {self.progress.estimated_remaining/3600:.1f}小时")
            
            # 批次间休息，避免过度请求
            if batch_idx < len(batches) - 1:
                print("  😴 批次间休息 30秒...")
                await asyncio.sleep(30)
        
        # 最终统计
        total_time = time.time() - self.progress.start_time
        print(f"\n🎉 大规模生成完成!")
        print(f"总耗时: {total_time/3600:.1f}小时")
        print(f"成功: {self.progress.completed_papers} 篇")
        print(f"失败: {self.progress.failed_papers} 篇")
        print(f"成功率: {self.progress.completed_papers/(self.progress.completed_papers+self.progress.failed_papers)*100:.1f}%")


# 使用示例
async def main():
    manager = LargeBatchTTSManager(
        max_concurrent_papers=2,    # 同时处理2篇论文
        max_concurrent_segments=6,  # 每篇6个片段
        retry_attempts=3
    )
    
    # 获取1000篇论文数据
    # papers = get_papers_data(1000)
    
    # 开始批量生成
    # await manager.generate_large_batch(
    #     papers, 
    #     output_dir=Path("data/tts_segments"), 
    #     voice="zh-CN-XiaoxiaoNeural",
    #     batch_size=10
    # )

if __name__ == "__main__":
    asyncio.run(main())
