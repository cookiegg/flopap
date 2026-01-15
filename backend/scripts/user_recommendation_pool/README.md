# 用户推荐池管理脚本

本目录包含用户推荐池生成和管理的相关脚本。

## 脚本说明

### generate_user_recommendations.py
为所有用户生成个性化推荐池

**功能：**
- 获取所有系统用户
- 基于CS候选池生成个性化排序表
- 提取前10%作为推荐池
- 支持批量处理

**使用方法：**
```bash
cd /data/proj/flopap/backend
python scripts/user_recommendation_pool/generate_user_recommendations.py
```

### verify_recommendations.py
验证用户推荐池生成情况

**功能：**
- 检查所有用户的排序表状态
- 显示推荐池大小和生成日期
- 验证数据完整性

**使用方法：**
```bash
cd /data/proj/flopap/backend
python scripts/user_recommendation_pool/verify_recommendations.py
```

## 推荐系统架构

- **排序表生成**: UserRankingService
- **推荐池提取**: RecommendationFacade
- **数据持久化**: user_paper_rankings表
- **推荐比例**: 默认10%

## 注意事项

- 脚本需要在backend目录下执行
- 确保数据库连接正常
- 推荐生成需要CS候选池数据
