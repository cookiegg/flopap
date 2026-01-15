#!/bin/bash
# 并行运行多个单OPUS生成脚本
# 用法: ./run_parallel_single_opus.sh [脚本数] [每脚本并发数] [总论文数]

SCRIPT_COUNT=${1:-3}      # 默认3个脚本
CONCURRENCY=${2:-6}       # 默认每脚本6并发
TOTAL_PAPERS=${3:-300}    # 默认处理300篇论文

cd /data/proj/flopap

echo "🚀 启动 ${SCRIPT_COUNT} 个并行脚本，每个 ${CONCURRENCY} 并发"
echo "📊 总论文数: ${TOTAL_PAPERS}, 每脚本处理: $((TOTAL_PAPERS / SCRIPT_COUNT))"

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
    
    python backend/scripts/tts/production/generate_single_opus_parallel.py \
        --offset ${OFFSET} \
        --limit ${LIMIT} \
        --concurrency ${CONCURRENCY} \
        --output-dir ./data/tts_single &
done

echo "⏳ 等待所有脚本完成..."
wait

echo "🎉 所有脚本执行完成"
echo "📁 输出目录: ./data/tts_single"
