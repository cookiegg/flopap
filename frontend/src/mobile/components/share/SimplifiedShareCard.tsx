import React from 'react';
import { Paper } from '../../../types';

interface SimplifiedShareCardProps {
  paper: Paper;
}

const SimplifiedShareCard: React.FC<SimplifiedShareCardProps> = ({ paper }) => {
  // 解析 AI 解读
  const getAIInsights = () => {
    const aiInsights = paper.aiInsights;
    if (!aiInsights) return null;

    if (Array.isArray(aiInsights)) {
      return aiInsights.slice(0, 3).map(item => item.zh || item.en || '');
    }

    if (typeof aiInsights === 'string') {
      try {
        let cleaned = (aiInsights as string).replace(/^```json\s*\n?/i, '').replace(/\n?```\s*$/i, '').trim();
        if (cleaned.includes('```')) {
          cleaned = cleaned.replace(/```.*$/s, '').trim();
        }
        const parsed = JSON.parse(cleaned);
        if (Array.isArray(parsed)) {
          return parsed.slice(0, 3).map(item => item.zh || item.en || '');
        }
      } catch (e) {
        // 如果不是JSON，返回纯文本的前几行
        return (aiInsights as string).split('\n').filter(line => line.trim()).slice(0, 3);
      }
    }
    
    return null;
  };

  const insights = getAIInsights();

  return (
    <div className="bg-gradient-to-br from-slate-900 to-slate-800 p-6" style={{ width: '400px' }}>
      {/* Header */}
      <div className="text-center mb-6">
        <div className="text-2xl font-bold mb-2">📚 FloPap</div>
        <div className="text-xs text-slate-400">AI 论文，像刷短视频一样简单</div>
      </div>

      {/* Paper Title */}
      <div className="bg-slate-800/50 rounded-xl p-4 mb-4 border border-slate-700">
        <h2 className="text-lg font-bold text-white mb-2 leading-tight">
          {paper.title}
        </h2>
        <div className="text-xs text-slate-400">
          {paper.authors.slice(0, 3).join(', ')}
          {paper.authors.length > 3 && ' et al.'}
        </div>
      </div>

      {/* AI Insights */}
      {insights && insights.length > 0 ? (
        <div className="space-y-3 mb-4">
          <div className="text-base font-semibold text-emerald-400 mb-3">
            🤖 AI 核心解读
          </div>
          {insights.map((insight, index) => (
            <div 
              key={index}
              className="bg-slate-800/30 rounded-lg p-3 border-l-4 border-emerald-500"
            >
              <div className="text-xs text-slate-300">
                {insight}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-slate-800/30 rounded-lg p-4 mb-4">
          <div className="text-base font-semibold text-blue-400 mb-2">
            📄 论文摘要
          </div>
          <div className="text-xs text-slate-300 line-clamp-6">
            {paper.translatedAbstract || paper.abstract}
          </div>
        </div>
      )}

      {/* Categories */}
      <div className="flex flex-wrap gap-2 mb-4">
        {paper.categories.slice(0, 3).map((cat, index) => (
          <span 
            key={index}
            className="px-2 py-1 bg-blue-500/20 text-blue-300 rounded-full text-xs"
          >
            {cat}
          </span>
        ))}
      </div>

      {/* CTA */}
      <div className="text-center text-slate-400 text-xs mb-3">
        在 FloPap 发现更多精彩论文 👇
      </div>
    </div>
  );
};

export default SimplifiedShareCard;
