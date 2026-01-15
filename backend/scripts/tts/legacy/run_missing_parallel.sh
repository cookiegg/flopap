#!/bin/bash
# 3个脚本×4并发补全缺失的OPUS文件

cd /data/proj/flopap

echo "🚀 启动3个批次并行补全缺失OPUS文件"
echo "配置：每批次4个并发，总并发12个"

# 同时启动3个批次，降低并发数
python backend/scripts/tts/generate_missing_opus.py --batch-id 0 --concurrency 4 &
python backend/scripts/tts/generate_missing_opus.py --batch-id 1 --concurrency 4 &
python backend/scripts/tts/generate_missing_opus.py --batch-id 2 --concurrency 4 &

echo "⏳ 等待所有批次完成..."
wait

echo "🎉 所有批次补全完成！"
