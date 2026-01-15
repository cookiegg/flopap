import React from 'react';
import { Globe } from 'lucide-react';
import { Paper, ViewMode, AppLanguage, AppTheme } from '../../../../types';

interface PaperCardHeaderProps {
    paper: Paper;
    viewMode: ViewMode;
    language: AppLanguage;
    theme: AppTheme;
}

const PaperCardHeader: React.FC<PaperCardHeaderProps> = ({
    paper,
    viewMode,
    language,
    theme
}) => {
    const isDark = theme === 'dark';
    const showBilingualTitle = viewMode === ViewMode.TRANSLATION || language === 'zh';
    const titleColor = isDark ? 'text-white' : 'text-gray-900';
    const subTitleColor = isDark ? 'text-gray-400' : 'text-gray-600';
    const authorColor = isDark ? 'text-gray-400' : 'text-gray-500';
    const bgHeader = isDark ? 'bg-gradient-to-b from-transparent to-black/10' : 'bg-gradient-to-b from-transparent to-gray-200/50';

    const handleOpenWeb = (e: React.MouseEvent) => {
        e.stopPropagation();

        // 根据论文来源决定外部链接
        if (paper.arxiv_id) {
            // ArXiv 论文 - 使用 ArXiv 链接
            window.open(`https://arxiv.org/abs/${paper.arxiv_id}`, '_blank');
        } else if (paper.pdfUrl) {
            // 其他来源论文 - 使用 PDF 链接
            window.open(paper.pdfUrl, '_blank');
        } else {
            console.warn('No external link available for this paper');
        }
    };

    return (
        <div className={`shrink-0 pt-24 px-6 pb-4 z-10 select-text ${bgHeader}`}>
            <div className="flex items-center justify-between mb-3">
                <div className="flex flex-wrap gap-2">
                    {paper.categories.map((cat, idx) => (
                        <span key={`${paper.id}-cat-${idx}`} className="px-2.5 py-0.5 bg-blue-500/20 border border-blue-500/30 text-blue-500 text-[10px] font-bold rounded-full backdrop-blur-sm">
                            {cat}
                        </span>
                    ))}
                </div>
                <div className="flex items-center gap-3 shrink-0 ml-2">
                    <button onClick={handleOpenWeb} className={`${subTitleColor} hover:text-blue-500 transition-colors`}>
                        <Globe size={16} />
                    </button>
                </div>
            </div>
            <div>
                {showBilingualTitle ? (
                    <>
                        <h1 className={`text-lg font-bold leading-snug drop-shadow-sm mb-1 ${titleColor}`}>{paper.translatedTitle || (language === 'zh' ? "正在加载标题..." : paper.title)}</h1>
                        <h2 className={`text-sm font-medium leading-tight ${subTitleColor}`}>{paper.title}</h2>
                    </>
                ) : (
                    <h1 className={`text-lg font-bold leading-snug drop-shadow-sm ${titleColor}`}>{paper.title}</h1>
                )}
            </div>
            <div className={`mt-3 text-xs font-medium line-clamp-1 ${authorColor}`}>{paper.authors.join(', ')}</div>
            <div className={`w-full h-px mt-4 ${isDark ? 'bg-white/10' : 'bg-gray-200'}`} />
        </div>
    );
};

export default PaperCardHeader;
