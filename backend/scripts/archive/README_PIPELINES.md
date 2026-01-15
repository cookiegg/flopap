# 流水线脚本

推荐系统的完整流水线脚本已移至 `scripts/pipeline/` 目录。

## 🚀 快速开始

```bash
# 查看所有可用流水线
python scripts/pipeline/pipeline_master.py list

# 运行日常流水线集合
python scripts/pipeline/pipeline_master.py daily

# 运行单个流水线
python scripts/pipeline/pipeline_master.py run --pipeline arxiv_cs
```

## 📁 目录结构

```
scripts/
├── pipeline/                          # 流水线脚本目录
│   ├── pipeline_master.py            # 主编排器
│   ├── pipeline_arxiv_cs_complete.py # arXiv CS完整流水线
│   ├── pipeline_embedding_recommendation.py # Embedding推荐
│   ├── pipeline_daily_maintenance.py # 日常维护
│   ├── pipeline_conference_papers.py # 会议论文处理
│   ├── pipeline_user_onboarding.py   # 用户入驻
│   └── PIPELINE_README.md            # 详细文档
├── init/                             # 初始化脚本
├── data_sources/                     # 数据源脚本
└── 其他工具脚本...
```

## 📖 详细文档

完整的流水线文档请查看: [`scripts/pipeline/PIPELINE_README.md`](pipeline/PIPELINE_README.md)

## 🔧 主要流水线

- **arxiv_cs**: arXiv CS完整处理链路 (~30分钟)
- **embedding_rec**: 基于embedding的个性化推荐 (~10分钟)  
- **daily_maintenance**: 系统维护和健康检查 (~15分钟)
- **conference**: 会议论文专门处理 (~20分钟)
- **user_onboarding**: 新用户入驻和分析 (~5分钟)
