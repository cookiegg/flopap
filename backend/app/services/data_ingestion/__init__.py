"""
数据导入服务模块
包含各个数据源的论文导入、数据质量检查、嵌入生成等服务

主要功能:
- ArXiv论文导入和候选池管理
- 会议论文导入
- 数据质量检查和清理
- 论文嵌入向量生成
- 通用数据导入框架

使用方式:
    from app.services.data_ingestion.ingestion import ingest_papers
    from app.services.data_ingestion.arxiv_candidate_pool import ArxivCandidatePoolService
    from app.services.data_ingestion.conference_import import import_conference_papers
    from app.services.data_ingestion.embedding import generate_embeddings
    from app.services.data_ingestion.data_quality import validate_paper_data
"""

# 数据导入服务文件夹
# 包含以下服务文件:
# - ingestion.py              # 通用数据导入框架
# - arxiv_candidate_pool.py   # ArXiv候选池管理
# - conference_import.py      # 会议论文导入
# - embedding.py              # 嵌入向量生成
# - data_quality.py           # 数据质量检查
