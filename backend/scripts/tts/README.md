# TTS 批量生成脚本集合

## 目录结构

```
backend/scripts/tts/
├── production/          # 生产环境脚本 (推荐使用)
├── experimental/        # 实验性脚本 (调试用)
├── legacy/             # 遗留脚本 (历史版本)
└── README.md           # 本文档
```

## 🚀 快速开始 (生产环境)

### 一键生成TTS
```bash
cd /data/proj/flopap

# 生成ICLR 2024论文TTS
./backend/scripts/tts/production/generate_tts_pipeline.sh "conf/iclr2024" 6

# 生成其他会议论文
./backend/scripts/tts/production/generate_tts_pipeline.sh "conf/icml2024" 8
```

### 手动分步执行
```bash
cd /data/proj/flopap

# 步骤1: 主要生成
python backend/scripts/tts/production/generate_batch_tts_optimized.py \
    --source "conf/iclr2024" \
    --concurrency 6

# 步骤2: 修复不完整
python backend/scripts/tts/production/fix_incomplete_papers.py \
    --source "conf/iclr2024"
```

## 📁 脚本分类说明

### Production (生产环境)
- `generate_tts_pipeline.sh` - **一键生成脚本** (推荐)
- `generate_batch_tts_optimized.py` - 优化的批量生成
- `fix_incomplete_papers.py` - 修复不完整论文
- `final_fix.py` - 最终修复版本 (解决空片段问题)

### Experimental (实验性)
- `quick_fix.py` - 快速修复尝试
- `conservative_fix.py` - 保守修复版本
- `final_cleanup.py` - 清理和转换脚本

### Legacy (遗留版本)
- `generate_tts_*.py` - 各种历史生成脚本
- `test_tts_*.py` - 测试脚本
- `distributed_tts_generator.py` - 分布式生成尝试

## 🎯 推荐使用流程

1. **新用户**: 直接使用 `production/generate_tts_pipeline.sh`
2. **高级用户**: 使用 `production/generate_batch_tts_optimized.py`
3. **调试问题**: 参考 `experimental/` 中的脚本
4. **学习历史**: 查看 `legacy/` 中的演进过程

## 📊 成功案例

- ✅ **NeurIPS 2025**: 5842篇论文，35052个音频文件，100%完成率
- ✅ **技术栈**: Edge-TTS + FFmpeg + OPUS格式
- ✅ **解决问题**: 空片段、API限流、并发竞争、文件清理

## 🔧 技术特性

- **智能分段**: 避免空片段问题
- **并发控制**: 防止API限流
- **增量生成**: 跳过已存在文件
- **自动修复**: 补全缺失片段
- **格式统一**: OPUS 24kHz 20kbps

详细使用说明请参考: `TTS_USAGE_GUIDE.md`
