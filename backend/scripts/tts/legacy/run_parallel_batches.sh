#!/bin/bash
# 并行运行多个TTS生成批次

cd /data/proj/flopap

echo "🚀 启动3个并行批次，每批12个并发"

# 同时运行3个批次，每批约33篇论文，每个脚本12个并发
python backend/scripts/tts/generate_batch_tts.py --offset 0 --limit 33 --concurrency 12 &
python backend/scripts/tts/generate_batch_tts.py --offset 33 --limit 33 --concurrency 12 &
python backend/scripts/tts/generate_batch_tts.py --offset 66 --limit 34 --concurrency 12 &

wait
echo "🎉 所有批次完成"
