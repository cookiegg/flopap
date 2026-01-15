# arXiv候选论文池生成脚本

使用 `app/services/arxiv_candidate_pool.py` 服务生成不同领域的候选论文池。

## 脚本说明

### 1. `generate_cs_pool.py` - CS候选池生成
专门生成计算机科学领域的候选论文池。

```bash
cd backend

# 生成今天的CS候选池
python scripts/arxiv_candidate_pool/generate_cs_pool.py

# 生成指定日期的CS候选池
python scripts/arxiv_candidate_pool/generate_cs_pool.py --date 2025-12-15

# 生成3天前的CS候选池
python scripts/arxiv_candidate_pool/generate_cs_pool.py --days-ago 3

# 生成最近7天的CS候选池
python scripts/arxiv_candidate_pool/generate_cs_pool.py --recent-days 7
```

### 2. `generate_candidate_pools.py` - 多领域候选池生成
支持生成多种领域的候选论文池。

```bash
# 生成CS候选池（默认）
python scripts/arxiv_candidate_pool/generate_candidate_pools.py

# 生成AI/ML/CV候选池
python scripts/arxiv_candidate_pool/generate_candidate_pools.py --filter-type ai-ml-cv

# 生成数学候选池
python scripts/arxiv_candidate_pool/generate_candidate_pools.py --filter-type math

# 生成物理候选池
python scripts/arxiv_candidate_pool/generate_candidate_pools.py --filter-type physics

# 生成所有论文候选池
python scripts/arxiv_candidate_pool/generate_candidate_pools.py --filter-type all
```

### 3. `query_candidate_pool.py` - 候选池查询
查询候选池的统计信息和论文详情。

```bash
# 查询今天的候选池统计
python scripts/arxiv_candidate_pool/query_candidate_pool.py

# 查询指定日期的统计
python scripts/arxiv_candidate_pool/query_candidate_pool.py --date 2025-12-15

# 查询特定领域的详细信息
python scripts/arxiv_candidate_pool/query_candidate_pool.py --filter-type cs

# 显示论文详细信息
python scripts/arxiv_candidate_pool/query_candidate_pool.py --filter-type cs --show-papers
```

## 筛选类型说明

| 类型 | 描述 | 筛选条件 |
|------|------|----------|
| `cs` | 计算机科学 | 分类以 `cs.` 开头 |
| `ai-ml-cv` | AI/机器学习/计算机视觉 | `cs.AI`, `cs.LG`, `cs.CV`, `cs.CL`, `cs.RO` |
| `math` | 数学 | 分类以 `math.` 开头 |
| `physics` | 物理 | `physics.`, `astro-ph.`, `cond-mat.` 开头 |
| `all` | 所有论文 | 无筛选条件 |

## 工作原理

### 1. 时间分区设计
- 基于论文的 `submitted_date` 进行日期分区
- 每个日期生成唯一的批次UUID
- 支持按日期独立管理候选池

### 2. 筛选流程
1. **清除旧数据**: 删除指定日期和类型的旧候选池
2. **查询论文**: 获取指定日期提交的所有论文
3. **应用筛选**: 使用筛选函数过滤论文
4. **保存结果**: 将筛选结果保存到候选池表

### 3. 数据库表
- `candidate_pool`: 存储候选池数据
  - `batch_id`: 日期对应的UUID
  - `paper_id`: 论文ID
  - `filter_type`: 筛选类型

## 使用场景

- **日常维护**: 为新获取的论文生成候选池
- **历史数据**: 为历史日期补充候选池
- **多领域支持**: 根据不同需求生成不同领域的候选池
- **数据分析**: 查询和分析候选池统计信息

## 注意事项

- 脚本已集成无代理逻辑，避免网络问题
- 支持批量处理多个日期
- 自动处理数据库事务和错误回滚
- 提供详细的执行日志和统计信息
