"""
数据质量检查服务 - 论文数据验证和清洗
功能：
- 论文数据完整性检查（标题、摘要、作者等）
- 数据格式验证和标准化
- 重复数据检测和去重
- 数据质量评分和报告
- 异常数据过滤和修复
- 为数据摄取提供质量保障
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from app.services.data_ingestion.ingestion import ArxivPaper


@dataclass
class ValidationResult:
    """数据验证结果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]


class DataQualityValidator:
    """数据质量验证器"""
    
    # 必需字段
    REQUIRED_FIELDS = ['arxiv_id', 'title', 'summary', 'authors']
    
    # arXiv ID 格式正则
    ARXIV_ID_PATTERN = re.compile(r'^\d{4}\.\d{4,5}(v\d+)?$')
    
    def validate_paper(self, paper: "ArxivPaper") -> ValidationResult:
        """验证单篇论文数据质量"""
        errors = []
        warnings = []
        
        # 1. 必需字段检查
        for field in self.REQUIRED_FIELDS:
            value = getattr(paper, field, None)
            if not value:
                errors.append(f"缺少必需字段: {field}")
            elif isinstance(value, str) and not value.strip():
                errors.append(f"字段为空: {field}")
        
        # 2. arXiv ID 格式验证
        if paper.arxiv_id and not self.ARXIV_ID_PATTERN.match(paper.arxiv_id):
            errors.append(f"arXiv ID 格式错误: {paper.arxiv_id}")
        
        # 3. 标题长度检查
        if paper.title:
            if len(paper.title.strip()) < 10:
                warnings.append("标题过短")
            elif len(paper.title) > 500:
                warnings.append("标题过长")
        
        # 4. 摘要长度检查
        if paper.summary:
            if len(paper.summary.strip()) < 50:
                warnings.append("摘要过短")
            elif len(paper.summary) > 5000:
                warnings.append("摘要过长")
        
        # 5. 作者信息检查
        if paper.authors:
            if len(paper.authors) == 0:
                errors.append("作者列表为空")
            else:
                for i, author in enumerate(paper.authors):
                    if not isinstance(author, dict) or not author.get('name'):
                        errors.append(f"作者信息格式错误: 索引{i}")
        
        # 6. 分类检查
        if paper.categories and len(paper.categories) == 0:
            warnings.append("分类信息为空")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_batch(self, papers: List["ArxivPaper"]) -> dict:
        """批量验证论文数据质量"""
        total_count = len(papers)
        valid_count = 0
        invalid_papers = []
        all_errors = []
        all_warnings = []
        
        for i, paper in enumerate(papers):
            result = self.validate_paper(paper)
            
            if result.is_valid:
                valid_count += 1
            else:
                invalid_papers.append({
                    'index': i,
                    'arxiv_id': paper.arxiv_id,
                    'errors': result.errors
                })
            
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
        
        quality_score = (valid_count / total_count) * 100 if total_count > 0 else 0
        
        return {
            'total_count': total_count,
            'valid_count': valid_count,
            'invalid_count': total_count - valid_count,
            'quality_score': quality_score,
            'invalid_papers': invalid_papers,
            'error_summary': self._summarize_issues(all_errors),
            'warning_summary': self._summarize_issues(all_warnings)
        }
    
    def _summarize_issues(self, issues: List[str]) -> dict:
        """汇总问题统计"""
        summary = {}
        for issue in issues:
            summary[issue] = summary.get(issue, 0) + 1
        return summary


def validate_and_filter_papers(papers: List["ArxivPaper"]) -> tuple[List["ArxivPaper"], dict]:
    """验证并过滤论文数据，返回有效论文和质量报告"""
    validator = DataQualityValidator()
    quality_report = validator.validate_batch(papers)
    
    # 过滤出有效论文
    valid_papers = []
    for i, paper in enumerate(papers):
        result = validator.validate_paper(paper)
        if result.is_valid:
            valid_papers.append(paper)
        else:
            logger.warning("论文数据质量不合格: {} - {}", paper.arxiv_id, result.errors)
    
    # 记录质量报告
    logger.info(
        "数据质量检查完成: 总数={}, 有效={}, 质量评分={:.1f}%",
        quality_report['total_count'],
        quality_report['valid_count'],
        quality_report['quality_score']
    )
    
    # 质量告警
    if quality_report['quality_score'] < 95:
        logger.warning("数据质量评分低于95%: {:.1f}%", quality_report['quality_score'])
    
    if quality_report['invalid_count'] > 0:
        logger.warning("发现{}篇无效论文", quality_report['invalid_count'])
        for error, count in quality_report['error_summary'].items():
            logger.warning("错误类型: {} ({}次)", error, count)
    
    return valid_papers, quality_report
