# TTS批量生成使用指南

## 快速开始

### 1. 一键生成 (推荐)
```bash
# 生成ICLR 2024论文TTS
./generate_tts_pipeline.sh "conf/iclr2024" 6

# 生成ICML 2024论文TTS  
./generate_tts_pipeline.sh "conf/icml2024" 8

# 使用不同语音模型
./generate_tts_pipeline.sh "conf/aaai2024" 6 "zh-CN-YunxiNeural"
```

### 2. 手动分步执行
```bash
cd /data/proj/flopap

# 步骤1: 主要生成
python backend/scripts/tts/generate_batch_tts_optimized.py \
    --source "conf/iclr2024" \
    --concurrency 6 \
    --voice "zh-CN-XiaoxiaoNeural"

# 步骤2: 修复不完整
python backend/scripts/tts/fix_incomplete_papers.py \
    --source "conf/iclr2024" \
    --voice "zh-CN-XiaoxiaoNeural"

# 步骤3: 清理临时文件
find backend/data/tts -name "*.wav" -delete
```

## 参数说明

### 论文来源 (source)
- `conf/neurips2025` - NeurIPS 2025
- `conf/iclr2024` - ICLR 2024  
- `conf/icml2024` - ICML 2024
- `conf/aaai2024` - AAAI 2024
- 或其他数据库中的source值

### 并发数 (concurrency)
- **推荐值**: 6-8 (平衡速度和稳定性)
- **保守值**: 3-4 (网络不稳定时)
- **激进值**: 10-12 (网络良好时)

### 语音模型 (voice)
- `zh-CN-XiaoxiaoNeural` - 晓晓 (女声，自然) **推荐**
- `zh-CN-YunxiNeural` - 云希 (男声，温和)
- `zh-CN-YunjianNeural` - 云健 (男声，稳重)

## 输出结构

```
backend/data/tts/
├── {paper-uuid-1}/
│   ├── segment_00_part_1.opus  # 论文标题
│   ├── segment_01_part_2.opus  # AI解读片段1
│   ├── segment_02_part_3.opus  # AI解读片段2
│   ├── segment_03_part_4.opus  # AI解读片段3
│   ├── segment_04_part_5.opus  # AI解读片段4
│   └── segment_05_part_6.opus  # AI解读片段5
├── {paper-uuid-2}/
└── ...
```

## 性能预估

| 论文数量 | 并发数 | 预计时间 | 输出大小 |
|---------|--------|----------|----------|
| 100篇   | 6      | 20分钟   | ~60MB    |
| 500篇   | 8      | 80分钟   | ~300MB   |
| 1000篇  | 8      | 160分钟  | ~600MB   |
| 5000篇  | 6      | 14小时   | ~3GB     |

## 故障排除

### 1. 生成失败率高
```bash
# 降低并发数
./generate_tts_pipeline.sh "conf/iclr2024" 3

# 或使用修复脚本
python backend/scripts/tts/fix_incomplete_papers.py --source "conf/iclr2024"
```

### 2. 检查完整性
```bash
# 统计不完整论文
python -c "
from pathlib import Path
from uuid import UUID

tts_dir = Path('backend/data/tts')
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
        print(f'不完整: {paper_dir.name} ({len(opus_files)}/6)')
        incomplete += 1

print(f'总计不完整: {incomplete}')
"
```

### 3. 清理和重新开始
```bash
# 删除特定来源的TTS文件 (谨慎使用)
# rm -rf backend/data/tts/*

# 或只删除临时文件
find backend/data/tts -name "*.wav" -delete
find backend/data/tts -name "temp_*" -delete
```

## 最佳实践

1. **首次运行**: 先用小批量测试 (如100篇)
2. **网络稳定**: 使用较高并发数 (8-10)
3. **网络不稳定**: 使用较低并发数 (3-4)
4. **长时间运行**: 使用screen或tmux避免中断
5. **磁盘空间**: 确保有足够空间 (每1000篇约600MB)

## 监控进度

```bash
# 实时监控生成进度
watch -n 10 "find backend/data/tts -name '*.opus' | wc -l"

# 查看最新生成的文件
ls -lt backend/data/tts/*/segment_*.opus | head -10
```
