#!/usr/bin/env python3
"""
改进的翻译解析逻辑
"""

def improved_parse_translation(content: str):
    """改进的翻译结果解析"""
    lines = content.split('\n')
    title_zh = ""
    summary_lines = []
    in_summary = False
    
    for line in lines:
        line = line.strip()
        if line.startswith('标题：'):
            title_zh = line[3:].strip()
        elif line.startswith('摘要：'):
            # 开始收集摘要内容
            summary_lines.append(line[3:].strip())
            in_summary = True
        elif in_summary and line:
            # 继续收集摘要的后续行
            summary_lines.append(line)
    
    summary_zh = '\n'.join(summary_lines) if summary_lines else ""
    
    return title_zh, summary_zh

# 测试
test_content = """标题：基于OLIVER的大语言模型辅助文献摘要筛选：文献综述中校准性能及单模型与行动者-批判者配置的评估

摘要：引言：近期研究表明大语言模型（LLM）可加速文献筛选，但现有评估多聚焦早期LLM、标准化科克伦综述、单模型配置，并以准确性为核心指标，其在泛化性、配置效应及校准性能方面的表现尚未深入探究。
方法：我们开发了开源流程OLIVER（基于LLM的综述文献优化筛选引擎），用于LLM辅助摘要筛选。通过在两项非科克伦系统综述中测试多种当代LLM，采用准确性、AUC及校准指标在全文筛选和最终纳入阶段评估性能。进一步设计行动者-批判者筛选框架，在三种聚合规则下组合两种轻量化模型进行测试。
结果：各独立模型表现差异显著。在规模较小的综述1（821篇摘要，最终纳入63篇）中，部分模型对最终纳入文献具有高敏感度，但伴随大量假阳性结果且校准性能较差。在规模较大的综述2（7741篇摘要，最终纳入71篇）中，多数模型特异性较高但召回能力不足，提示词设计显著影响查全率。单模型配置虽总体准确性较高，但校准性能普遍薄弱。行动者-批判者筛选框架在两项综述中均提升了判别能力，显著降低校准误差，并获得更高AUC值。
讨论：LLM有望加速摘要筛选进程，但单模型性能受综述特征与提示词设计的显著影响，且校准能力有限。行动者-批判者框架在保持计算效率的同时，可提升分类质量与置信度可靠性，为实现低成本大规模文献筛选提供可行路径。"""

title, summary = improved_parse_translation(test_content)
print(f"标题: {title}")
print(f"摘要长度: {len(summary)} 字符")
print(f"摘要: {summary}")
