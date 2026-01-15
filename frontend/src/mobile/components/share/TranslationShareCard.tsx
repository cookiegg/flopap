import React from 'react';
import { Paper } from '../../../types';

interface TranslationShareCardProps {
  paper: Paper;
}

const TranslationShareCard: React.FC<TranslationShareCardProps> = ({ paper }) => {
  return (
    <div className="bg-gradient-to-br from-slate-900 to-slate-800 p-6" style={{ width: '400px' }}>
      {/* Header */}
      <div className="text-center mb-6">
        <div className="text-2xl font-bold mb-2">📚 FloPap</div>
        <div className="text-xs text-slate-400">AI 论文，像刷短视频一样简单</div>
      </div>

      {/* Paper Title (Chinese) */}
      <div className="bg-slate-800/50 rounded-xl p-4 mb-4 border border-slate-700">
        <h2 className="text-lg font-bold text-white mb-2 leading-tight">
          {paper.translatedTitle || paper.title}
        </h2>
        <div className="text-xs text-slate-400">
          {paper.authors.slice(0, 3).join(', ')}
          {paper.authors.length > 3 && ' 等'}
        </div>
      </div>

      {/* Abstract (Chinese) */}
      <div className="bg-slate-800/30 rounded-lg p-4 mb-4">
        <div className="text-base font-semibold text-purple-400 mb-2">
          📄 摘要
        </div>
        <div className="text-xs text-slate-300 leading-relaxed line-clamp-6">
          {paper.translatedAbstract || paper.abstract}
        </div>
      </div>

      {/* Categories */}
      <div className="flex flex-wrap gap-2 mb-4">
        {paper.categories.slice(0, 3).map((cat, index) => (
          <span 
            key={index}
            className="px-2 py-1 bg-purple-500/20 text-purple-300 rounded-full text-xs"
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

export default TranslationShareCard;
