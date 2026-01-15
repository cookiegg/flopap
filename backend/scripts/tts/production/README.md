# Production TTS Scripts

生产环境TTS音频生成脚本，采用单文件OPUS格式，优化存储效率和音质。

## 核心脚本

### generate_single_opus.py
**单文件OPUS生成脚本**
- 为每篇论文生成一个完整的OPUS音频文件
- 24kbps高质量编码，VBR可变比特率
- 最高压缩级别，优化存储空间
- 支持指定偏移量和数量进行批量处理

```bash
python generate_single_opus.py --offset 0 --limit 100 --voice zh-CN-XiaoxiaoNeural
```

### generate_single_opus_parallel.py
**并行单文件生成脚本**
- 支持多脚本并行处理大量论文
- 内置随机延迟避免API限流
- 唯一临时文件名防止冲突
- 可配置并发数和处理范围

```bash
python generate_single_opus_parallel.py --offset 0 --limit 50 --concurrency 6
```

### run_parallel_single_opus.sh
**并行执行管理脚本**
- 自动分割数据给多个脚本处理
- 支持 N脚本 × M并发 的灵活配置
- 等待所有脚本完成后统一报告

```bash
# 3个脚本，每个6并发，处理300篇论文
./run_parallel_single_opus.sh 3 6 300
```

## 架构优势

**存储优化**: 单文件比6段文件节省存储空间
**音质提升**: 24kbps比20kbps音质更好，避免分段间的不连贯
**处理效率**: 并行架构支持大规模批量处理
**稳定性**: 基于legacy版本经验，解决了API限流和文件冲突问题

## 使用流程

1. **小批量测试**: 使用 `generate_single_opus.py` 测试少量论文
2. **大批量生产**: 使用 `run_parallel_single_opus.sh` 进行并行处理
3. **监控进度**: 观察输出日志，确认生成成功率

## 配置建议

- **并发数**: 每脚本6并发，避免API限流
- **脚本数**: 根据论文总数和服务器性能调整（建议3-5个）
- **延迟设置**: 内置0.5-1.2秒随机延迟，无需调整

## 输出格式

- **文件名**: `{paper_id}.opus`
- **编码**: OPUS 24kbps VBR
- **采样率**: 24kHz
- **压缩**: 最高级别（level 10）

## 迁移说明

原6段生成脚本已移至 `../legacy/` 目录：
- `generate_batch_tts.py` - 基础6段生成
- `generate_batch_tts_optimized.py` - 优化6段生成
- `generate_neurips_plan2.py` - NeurIPS专用版本
- `final_fix.py` - 最终修复版本
- 其他相关工具脚本

新的单文件架构提供更好的存储效率和音质连贯性。
