# CS 候选池处理脚本

本目录包含针对计算机科学(CS)领域候选池的处理脚本。

## 脚本列表

### `translate_candidate_pool.py` - 候选池翻译脚本

对筛选后的候选池论文进行批量翻译。

#### 功能特点
- ✅ 先保存翻译结果到JSON文件，再转储到数据库
- ✅ 支持断点续传，避免重复翻译
- ✅ 充分利用50个API KEY并发处理
- ✅ 错误隔离，单篇失败不影响整体进度
- ✅ 支持多种筛选类型 (cs, ai-ml-cv, math, physics, all)

#### 使用方法

```bash
# 基本用法：翻译cs候选池
python translate_candidate_pool.py <batch_id> cs

# 查看翻译状态
python translate_candidate_pool.py <batch_id> cs --status
```

### `interpret_candidate_pool.py` - 候选池AI解读生成脚本

对筛选后的候选池论文进行批量AI解读生成。

#### 功能特点
- ✅ 先保存AI解读结果到JSON文件，再转储到数据库
- ✅ 支持断点续传，避免重复生成
- ✅ 充分利用50个API KEY并发处理
- ✅ 错误隔离，单篇失败不影响整体进度
- ✅ 支持多种筛选类型 (cs, ai-ml-cv, math, physics, all)

#### 使用方法

```bash
# 基本用法：生成cs候选池AI解读
python interpret_candidate_pool.py <batch_id> cs

# 指定并发数和输出目录
python interpret_candidate_pool.py <batch_id> cs --max-workers 30 --output-dir my_interpretations

# 只生成AI解读到文件，不保存到数据库
python interpret_candidate_pool.py <batch_id> cs --only-interpret

# 只从文件加载到数据库
python interpret_candidate_pool.py <batch_id> cs --only-load

# 查看AI解读状态
python interpret_candidate_pool.py <batch_id> cs --status
```

#### 参数说明

- `batch_id`: 批次ID（必需）
- `filter_type`: 筛选类型，支持 cs, ai-ml-cv, math, physics, all
- `--max-workers`: 最大并发数，默认50
- `--output-dir`: 输出目录，默认 `interpretation_results_<filter_type>`
- `--only-interpret`: 只生成AI解读到文件，不保存到数据库
- `--only-load`: 只从文件加载到数据库
- `--status`: 查看AI解读状态

#### AI解读输出文件格式

```json
{
  "paper_id": "uuid",
  "arxiv_id": "2025.12345v1",
  "title": "Paper Title",
  "ai_interpretation": "详细的AI解读内容...",
  "timestamp": "2025-12-16T22:33:18.835",
  "model_name": "deepseek-chat"
}
```

## 完整工作流程

### 1. 创建候选池
```bash
# 在backend目录下
python manage_candidate_pool.py create <batch_id> cs
```

### 2. 翻译候选池论文
```bash
cd scripts/cs
python translate_candidate_pool.py <batch_id> cs
```

### 3. 生成AI解读
```bash
cd scripts/cs
python interpret_candidate_pool.py <batch_id> cs
```

### 4. 查看处理状态
```bash
# 查看翻译状态
python translate_candidate_pool.py <batch_id> cs --status

# 查看AI解读状态
python interpret_candidate_pool.py <batch_id> cs --status
```

## 示例

```bash
# 完整处理流程示例
BATCH_ID="d490f9aa-472d-4a2e-bf20-09727313d4b3"

# 1. 翻译
python translate_candidate_pool.py $BATCH_ID cs

# 2. AI解读
python interpret_candidate_pool.py $BATCH_ID cs

# 3. 查看状态
python translate_candidate_pool.py $BATCH_ID cs --status
python interpret_candidate_pool.py $BATCH_ID cs --status
```

## 性能数据

基于184篇cs论文的处理结果：

| 任务 | 论文数 | 并发数 | 耗时 | 成功率 |
|------|--------|--------|------|--------|
| 翻译 | 184篇 | 50 | ~50秒 | 100% |
| AI解读 | 184篇 | 50 | ~2分钟 | 100% |

## 注意事项

1. **API限制**: 脚本使用DeepSeek API，请确保有足够的API配额
2. **存储空间**: 输出文件会占用磁盘空间，建议定期清理
3. **网络稳定**: 大批量处理需要稳定的网络连接
4. **数据库连接**: 确保数据库连接正常，避免保存失败
5. **处理顺序**: 建议先完成翻译，再进行AI解读

## 错误处理

- 单篇论文处理失败不会影响其他论文
- 数据库保存失败时，输出文件仍然保留
- 支持重新运行脚本进行断点续传
- 详细的日志记录便于问题排查
