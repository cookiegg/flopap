# Legacy Scripts

这里保存了TTS系统开发过程中的历史版本脚本，展示了从简单测试到复杂并行处理的演进过程。

## 发展历程

### 第一阶段：基础探索
- `generate_tts_simple.py` - 最初的简单实现
- `test_tts_simple.py` - 基础功能测试
- `test_tts_direct.py` - 直接调用测试

### 第二阶段：批量处理
- `generate_tts_batch.py` - 小批量处理
- `generate_neurips_tts.py` - 针对NeurIPS的专用版本
- `generate_neurips_tts_batch.py` - NeurIPS批量处理

### 第三阶段：分段优化
- `generate_segmented_tts.py` - 引入分段概念
- `generate_100_segmented_tts.py` - 100篇测试版本

### 第四阶段：大规模并行
- `large_batch_tts_manager.py` - 大批量管理器
- `distributed_tts_generator.py` - 分布式处理尝试
- `run_parallel_batches.sh` - 并行执行脚本

### 第五阶段：问题修复
- `generate_missing_tts.py` - 补全缺失文件
- `run_missing_parallel.sh` - 并行补全

### 第六阶段：生产6段版本 (2025-12-27迁移)
- `generate_batch_tts.py` - 基础6段生成脚本
- `generate_batch_tts_optimized.py` - 优化6段生成，解决并发冲突
- `generate_neurips_plan2.py` - NeurIPS大规模6段生成
- `generate_missing_opus.py` - 补全缺失的6段OPUS文件
- `complete_tts_files.py` - 6段文件完整性检查
- `fix_incomplete_papers.py` - 修复不完整的6段论文
- `final_fix.py` - 最终6段修复版本，100%成功率
- `generate_tts_pipeline.sh` - 6段生成完整流程脚本

## 主要问题和解决

1. **空片段问题** - 在final_fix.py中最终解决
2. **API限流** - 通过降低并发和增加延迟解决
3. **文件清理** - 改进异常处理和临时文件管理
4. **并发竞争** - 从72并发降到6并发
5. **存储效率** - 最终采用单文件OPUS替代6段方案

## 架构演进

**文件格式**: WAV → 6段OPUS → 单文件OPUS
**并发控制**: 3并发 → 72并发 → 6并发 → 多脚本×6并发
**错误处理**: 无 → 基础异常 → 断点续传 → 完善重试
**存储优化**: 无压缩 → 20kbps → 24kbps VBR

## 学习价值

这些脚本展示了：
- 渐进式开发的重要性
- 性能优化的权衡
- 错误处理的演进
- 并发控制的学习过程
- 存储架构的优化历程

**注意**: 这些脚本仅供学习参考，生产环境请使用 `production/` 目录中的单文件OPUS脚本。
