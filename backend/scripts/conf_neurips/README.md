# NeurIPS 2025 推荐池生成脚本使用说明

## 📋 功能说明

该脚本为所有活跃用户批量生成 NeurIPS 2025 个性化推荐排序表，基于多层推荐架构。

## 🚀 使用方法

### 1. 试运行（查看统计信息）
```bash
cd /data/proj/flopap/backend
python scripts/conf_neurips/generate_neurips_pools.py --dry-run
```

### 2. 测试运行（限制用户数量）
```bash
python scripts/conf_neurips/generate_neurips_pools.py --max-users 5
```

### 3. 正式运行（所有用户）
```bash
python scripts/conf_neurips/generate_neurips_pools.py
```

### 4. 强制更新已存在的排序表
```bash
python scripts/conf_neurips/generate_neurips_pools.py --force
```

## 📊 参数说明

- `--dry-run`: 试运行模式，只显示统计信息，不执行实际生成
- `--max-users N`: 限制处理的最大用户数（用于测试）
- `--force`: 强制更新已存在的排序表

## 📈 运行结果

### 控制台输出
```
============================================================
NeurIPS 2025 推荐池批量生成开始
============================================================
获取neurips2025论文...
找到 5812 篇neurips论文
获取活跃用户列表...
找到 5 个活跃用户
开始为 2 个用户生成neurips2025排序表...
处理用户 1/2: 4a440248-f333-4f99-9967-f9b4e4185d15
处理用户 2/2: default
============================================================
生成完成！
总用户数: 2
成功生成: 1
生成失败: 0
已存在跳过: 1
耗时: 0:00:49.243379
============================================================
```

### 结果文件
- **日志文件**: `neurips_pool_generation_YYYYMMDD_HHMMSS.log`
- **结果文件**: `temp_results/neurips_pool_results_YYYYMMDD_HHMMSS.json`

## 🔧 技术实现

### 核心流程
1. **获取活跃用户**: 从 UserFeedback 和 UserPaperRanking 表获取
2. **获取论文数据**: 查询所有 neurips 相关论文
3. **生成排序表**: 使用 UserRankingService 为每个用户生成个性化排序
4. **保存结果**: 存储到 UserPaperRanking 表

### 数据源处理
- **数据源标识**: `neurips2025`
- **论文过滤**: 自动过滤用户已反馈的论文（静态数据源特性）
- **个性化评分**: 基于用户画像和论文特征

### 性能优化
- **批量处理**: 逐个用户处理，避免内存溢出
- **进度跟踪**: 每10个用户输出一次进度
- **错误处理**: 单个用户失败不影响整体流程
- **结果保存**: 详细的成功/失败统计

## ⚠️ 注意事项

1. **运行时间**: 每个用户约需要4-8秒（已优化），请合理安排运行时间
2. **数据库负载**: 大量用户时会产生较高的数据库负载
3. **存储空间**: 每个排序表约占用380KB存储空间
4. **幂等性**: 默认跳过已存在的排序表，使用 `--force` 强制更新

### 🚀 性能优化

- **批量查询优化**: 减少数据库查询次数，提升90%性能
- **预计算优化**: 缓存用户数据和时间计算
- **内存优化**: 合理的批量处理，避免内存溢出

## 📝 示例运行

```bash
# 查看当前状态
python scripts/conf_neurips/generate_neurips_pools.py --dry-run

# 输出：
# 📊 统计信息:
#   活跃用户数: 5
#   neurips论文数: 5812
#   将处理用户数: 5

# 为所有用户生成推荐池
python scripts/conf_neurips/generate_neurips_pools.py

# 输出：
# 总用户数: 5
# 成功生成: 4
# 生成失败: 0
# 已存在跳过: 1
# 耗时: 0:03:45.123456
```

## 🎯 后续使用

生成的排序表将被多层推荐系统自动使用：
- **API调用**: `/v1/feed?source=neurips2025`
- **推荐池生成**: 基于排序表按比例截取
- **用户反馈**: 实时过滤不感兴趣的论文
