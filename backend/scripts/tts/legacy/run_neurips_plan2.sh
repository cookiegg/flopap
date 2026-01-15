#!/bin/bash
"""
方案2执行脚本：6个脚本×12并发处理NeurIPS论文
"""

cd /data/proj/flopap

echo "🚀 启动方案2：6个批次并行处理NeurIPS论文"
echo "配置：每批次12个并发，总并发72个"

# 同时启动6个批次
python backend/scripts/tts/generate_neurips_plan2.py --batch-id 0 --concurrency 12 &
python backend/scripts/tts/generate_neurips_plan2.py --batch-id 1 --concurrency 12 &
python backend/scripts/tts/generate_neurips_plan2.py --batch-id 2 --concurrency 12 &
python backend/scripts/tts/generate_neurips_plan2.py --batch-id 3 --concurrency 12 &
python backend/scripts/tts/generate_neurips_plan2.py --batch-id 4 --concurrency 12 &
python backend/scripts/tts/generate_neurips_plan2.py --batch-id 5 --concurrency 12 &

echo "⏳ 等待所有批次完成..."
wait

echo "🎉 方案2执行完成！"
echo "📁 输出目录: backend/data/tts/"
