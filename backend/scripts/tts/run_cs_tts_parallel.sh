#!/bin/bash
# CS候选池TTS并行生成脚本
# 用法: ./run_cs_tts_parallel.sh [脚本数] [每脚本并发数]

SCRIPT_COUNT=${1:-3}      # 默认3个脚本
CONCURRENCY=${2:-6}       # 默认每脚本6并发
TOTAL_PAPERS=347          # CS候选池总论文数

cd /data/proj/flopap

echo "🚀 启动 ${SCRIPT_COUNT} 个并行脚本，每个 ${CONCURRENCY} 并发"
echo "📊 CS候选池总论文数: ${TOTAL_PAPERS}, 每脚本处理: $((TOTAL_PAPERS / SCRIPT_COUNT))"

# 计算每个脚本的处理范围
PAPERS_PER_SCRIPT=$((TOTAL_PAPERS / SCRIPT_COUNT))
REMAINDER=$((TOTAL_PAPERS % SCRIPT_COUNT))

# 启动并行脚本
for i in $(seq 0 $((SCRIPT_COUNT - 1))); do
    OFFSET=$((i * PAPERS_PER_SCRIPT))
    LIMIT=$PAPERS_PER_SCRIPT
    
    # 最后一个脚本处理剩余论文
    if [ $i -eq $((SCRIPT_COUNT - 1)) ]; then
        LIMIT=$((PAPERS_PER_SCRIPT + REMAINDER))
    fi
    
    echo "📝 脚本 $((i+1)): 偏移 ${OFFSET}, 数量 ${LIMIT}"
    
    python backend/scripts/tts/generate_cs_tts_parallel.py \
        --offset ${OFFSET} \
        --limit ${LIMIT} \
        --concurrency ${CONCURRENCY} \
        --output-dir /data/proj/flopap/data/tts_opus &
done

echo "⏳ 等待所有脚本完成..."
wait

echo "🎉 所有脚本执行完成"
echo "📁 输出目录: /data/proj/flopap/data/tts_opus"
echo "📊 检查生成结果..."

# 统计生成结果
GENERATED_COUNT=$(find /data/proj/flopap/data/tts_opus -name "*.opus" | wc -l)
echo "✅ 成功生成 (含历史) ${GENERATED_COUNT}/${TOTAL_PAPERS} 个TTS文件"
