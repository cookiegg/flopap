#!/usr/bin/env python3
"""
主流水线编排器
统一管理和调度所有流水线脚本
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

import subprocess
import argparse
from datetime import datetime
import json

# 可用的流水线
AVAILABLE_PIPELINES = {
    'arxiv_cs': {
        'script': 'pipeline_arxiv_cs_complete.py',
        'description': 'arXiv CS完整流水线: 获取+embedding+候选池+翻译+解读+推荐+推送',
        'schedule': 'daily',
        'duration': '~30min'
    },
    'embedding_rec': {
        'script': 'pipeline_embedding_recommendation.py', 
        'description': 'Embedding个性化推荐: 用户embedding更新+相似度计算+推荐生成',
        'schedule': 'daily',
        'duration': '~10min'
    },
    'daily_maintenance': {
        'script': 'pipeline_daily_maintenance.py',
        'description': '日常维护: 数据质量检查+清理+推荐池更新+健康检查+统计',
        'schedule': 'daily',
        'duration': '~15min'
    },
    'conference': {
        'script': 'pipeline_conference_papers.py',
        'description': '会议论文处理: 获取+筛选+内容生成+推荐池+专题推荐',
        'schedule': 'weekly',
        'duration': '~20min'
    },
    'user_onboarding': {
        'script': 'pipeline_user_onboarding.py',
        'description': '用户入驻: 新用户检测+冷启动推荐+兴趣探索+个性化推送+行为分析',
        'schedule': 'daily',
        'duration': '~5min'
    }
}

def list_pipelines():
    """列出所有可用的流水线"""
    print("🚀 可用流水线:")
    print()
    
    for name, info in AVAILABLE_PIPELINES.items():
        print(f"📋 {name}")
        print(f"   描述: {info['description']}")
        print(f"   调度: {info['schedule']}")
        print(f"   预计耗时: {info['duration']}")
        print()

def run_pipeline(pipeline_name, verbose=False):
    """运行指定的流水线"""
    if pipeline_name not in AVAILABLE_PIPELINES:
        print(f"❌ 未知流水线: {pipeline_name}")
        print(f"可用流水线: {', '.join(AVAILABLE_PIPELINES.keys())}")
        return False
    
    pipeline_info = AVAILABLE_PIPELINES[pipeline_name]
    script_path = Path(__file__).parent / pipeline_info['script']
    
    if not script_path.exists():
        print(f"❌ 流水线脚本不存在: {script_path}")
        return False
    
    print(f"🚀 启动流水线: {pipeline_name}")
    print(f"📝 描述: {pipeline_info['description']}")
    print(f"⏱️  预计耗时: {pipeline_info['duration']}")
    print(f"📄 脚本: {pipeline_info['script']}")
    print("-" * 60)
    
    start_time = datetime.now()
    
    try:
        # 运行流水线脚本
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=not verbose,
            text=True,
            cwd=script_path.parent.parent.parent
        )
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        if result.returncode == 0:
            print("-" * 60)
            print(f"✅ 流水线 {pipeline_name} 执行成功")
            print(f"⏱️  实际耗时: {duration}")
            
            if not verbose and result.stdout:
                # 显示最后几行输出
                lines = result.stdout.strip().split('\n')
                print("📊 执行摘要:")
                for line in lines[-5:]:
                    if line.strip():
                        print(f"   {line}")
            
            return True
        else:
            print("-" * 60)
            print(f"❌ 流水线 {pipeline_name} 执行失败")
            print(f"⏱️  执行时间: {duration}")
            print(f"🔍 错误信息:")
            if result.stderr:
                print(result.stderr)
            if result.stdout:
                print(result.stdout)
            
            return False
            
    except Exception as e:
        print(f"❌ 流水线执行异常: {e}")
        return False

def run_daily_pipelines():
    """运行所有日常流水线"""
    print("🌅 开始执行日常流水线集合")
    start_time = datetime.now()
    
    daily_pipelines = [
        'user_onboarding',    # 用户入驻 (快速)
        'daily_maintenance',  # 日常维护 (中等)
        'embedding_rec',      # Embedding推荐 (中等)
        'arxiv_cs'           # arXiv完整流程 (较慢)
    ]
    
    results = {}
    
    for pipeline in daily_pipelines:
        print(f"\n{'='*60}")
        success = run_pipeline(pipeline, verbose=False)
        results[pipeline] = success
        
        if not success:
            print(f"⚠️  流水线 {pipeline} 失败，继续执行下一个...")
    
    # 总结
    end_time = datetime.now()
    total_duration = end_time - start_time
    
    print(f"\n{'='*60}")
    print(f"🎉 日常流水线集合执行完成")
    print(f"⏱️  总耗时: {total_duration}")
    print(f"📊 执行结果:")
    
    success_count = sum(results.values())
    for pipeline, success in results.items():
        status = "✅" if success else "❌"
        print(f"   {status} {pipeline}")
    
    print(f"\n📈 成功率: {success_count}/{len(daily_pipelines)} ({success_count/len(daily_pipelines)*100:.1f}%)")
    
    return results

def run_weekly_pipelines():
    """运行所有周度流水线"""
    print("📅 开始执行周度流水线集合")
    
    weekly_pipelines = [
        'conference',         # 会议论文处理
        'daily_maintenance'   # 深度维护
    ]
    
    results = {}
    
    for pipeline in weekly_pipelines:
        print(f"\n{'='*60}")
        success = run_pipeline(pipeline, verbose=False)
        results[pipeline] = success
    
    return results

def main():
    parser = argparse.ArgumentParser(description='流水线编排器')
    parser.add_argument('command', choices=['list', 'run', 'daily', 'weekly'], 
                       help='命令: list(列出流水线), run(运行单个), daily(日常集合), weekly(周度集合)')
    parser.add_argument('--pipeline', '-p', help='要运行的流水线名称 (用于run命令)')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        list_pipelines()
        
    elif args.command == 'run':
        if not args.pipeline:
            print("❌ 请指定要运行的流水线名称 (--pipeline)")
            list_pipelines()
            return
        
        success = run_pipeline(args.pipeline, args.verbose)
        sys.exit(0 if success else 1)
        
    elif args.command == 'daily':
        results = run_daily_pipelines()
        success_count = sum(results.values())
        sys.exit(0 if success_count == len(results) else 1)
        
    elif args.command == 'weekly':
        results = run_weekly_pipelines()
        success_count = sum(results.values())
        sys.exit(0 if success_count == len(results) else 1)

if __name__ == "__main__":
    main()
