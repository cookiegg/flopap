#!/bin/bash
"""
TTS批量生成完整流程脚本
用法: ./generate_tts_pipeline.sh [论文来源] [并发数]
示例: ./generate_tts_pipeline.sh "conf/iclr2024" 8
"""

set -e  # 遇到错误立即退出

# 参数设置
PAPER_SOURCE=${1:-"conf/neurips2025"}  # 默认NeurIPS 2025
CONCURRENCY=${2:-6}                    # 默认6个并发
VOICE=${3:-"zh-CN-XiaoxiaoNeural"}     # 默认语音

# 目录设置
PROJECT_ROOT="/data/proj/flopap"
TTS_DIR="$PROJECT_ROOT/backend/data/tts"
SCRIPT_DIR="$PROJECT_ROOT/backend/scripts/tts"

cd "$PROJECT_ROOT"

echo "🚀 TTS批量生成流程启动"
echo "📚 论文来源: $PAPER_SOURCE"
echo "⚡ 并发数: $CONCURRENCY"
echo "🎵 语音模型: $VOICE"
echo "📁 输出目录: $TTS_DIR"
echo "----------------------------------------"

# 步骤1: 检查环境
echo "🔍 步骤1: 环境检查"
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ 错误: 未找到ffmpeg，请先安装"
    exit 1
fi

if ! python -c "import edge_tts" 2>/dev/null; then
    echo "❌ 错误: 未找到edge-tts，请先安装: pip install edge-tts"
    exit 1
fi

echo "✅ 环境检查通过"

# 步骤2: 统计论文数量
echo "🔍 步骤2: 统计论文数量"
PAPER_COUNT=$(python -c "
import sys
sys.path.insert(0, 'backend')
from app.db.session import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    result = db.execute(text('''
        SELECT COUNT(*)
        FROM paper_interpretations pi
        JOIN papers p ON pi.paper_id = p.id
        WHERE pi.interpretation IS NOT NULL 
        AND LENGTH(pi.interpretation) > 50
        AND p.source = :source
    '''), {'source': '$PAPER_SOURCE'})
    print(result.scalar())
finally:
    db.close()
")

if [ "$PAPER_COUNT" -eq 0 ]; then
    echo "❌ 错误: 未找到来源为 '$PAPER_SOURCE' 的论文"
    exit 1
fi

echo "📊 找到 $PAPER_COUNT 篇论文需要处理"

# 步骤3: 主要生成阶段
echo "🎵 步骤3: 主要TTS生成 (预计时间: $((PAPER_COUNT * 2 / CONCURRENCY))分钟)"

python "$SCRIPT_DIR/generate_batch_tts_optimized.py" \
    --source "$PAPER_SOURCE" \
    --concurrency "$CONCURRENCY" \
    --voice "$VOICE" \
    --output-dir "$TTS_DIR"

echo "✅ 主要生成完成"

# 步骤4: 完整性检查
echo "🔍 步骤4: 完整性检查"
INCOMPLETE_COUNT=$(python -c "
from pathlib import Path
from uuid import UUID

tts_dir = Path('$TTS_DIR')
incomplete = 0

for paper_dir in tts_dir.iterdir():
    if not paper_dir.is_dir():
        continue
    
    try:
        UUID(paper_dir.name)
    except ValueError:
        continue
    
    opus_files = list(paper_dir.glob('*.opus'))
    if len(opus_files) < 6:
        incomplete += 1

print(incomplete)
")

echo "📊 发现 $INCOMPLETE_COUNT 篇不完整论文"

# 步骤5: 修复不完整论文
if [ "$INCOMPLETE_COUNT" -gt 0 ]; then
    echo "🔧 步骤5: 修复不完整论文"
    
    python "$SCRIPT_DIR/fix_incomplete_papers.py" \
        --source "$PAPER_SOURCE" \
        --voice "$VOICE" \
        --output-dir "$TTS_DIR"
    
    echo "✅ 修复完成"
else
    echo "✅ 步骤5: 无需修复，所有论文都完整"
fi

# 步骤6: 清理临时文件
echo "🧹 步骤6: 清理临时文件"
find "$TTS_DIR" -name "*.wav" -delete 2>/dev/null || true
find "$TTS_DIR" -name "temp_*" -delete 2>/dev/null || true
echo "✅ 清理完成"

# 步骤7: 最终统计
echo "📊 步骤7: 最终统计"
TOTAL_OPUS=$(find "$TTS_DIR" -name "*.opus" | wc -l)
TOTAL_SIZE=$(du -sh "$TTS_DIR" | cut -f1)
COMPLETE_PAPERS=$(find "$TTS_DIR" -mindepth 1 -maxdepth 1 -type d | wc -l)

echo "----------------------------------------"
echo "🎉 TTS生成流程完成！"
echo "📚 处理论文: $COMPLETE_PAPERS 篇"
echo "🎵 音频文件: $TOTAL_OPUS 个"
echo "💾 总大小: $TOTAL_SIZE"
echo "📁 输出目录: $TTS_DIR"
echo "----------------------------------------"

# 验证完整性
EXPECTED_FILES=$((COMPLETE_PAPERS * 6))
if [ "$TOTAL_OPUS" -eq "$EXPECTED_FILES" ]; then
    echo "✅ 完整性验证通过: $TOTAL_OPUS/$EXPECTED_FILES"
else
    echo "⚠️  完整性警告: $TOTAL_OPUS/$EXPECTED_FILES (可能有部分论文片段数不足6个)"
fi
