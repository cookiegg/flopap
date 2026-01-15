import React from 'react';
import { Paper, AppLanguage, AppTheme, ViewMode } from '../../../../types';
import { Sparkles } from 'lucide-react';
import { UI_STRINGS } from '../../../../constants';

interface PaperCardTextContentProps {
    paper: Paper;
    language: AppLanguage;
    theme: AppTheme;
    viewMode: ViewMode;
}

const PaperCardTextContent: React.FC<PaperCardTextContentProps> = ({
    paper,
    language,
    theme,
    viewMode
}) => {
    const isDark = theme === 'dark';
    const ui = UI_STRINGS[language];

    // Helper functions for rendering text
    const renderInlineStyles = (text: string) => {
        const parts = text.split(/(\*\*[^*]+\*\*)/g);
        return parts.map((part, i) => {
            if (part.startsWith('**') && part.endsWith('**')) {
                return <strong key={i} className={isDark ? 'text-purple-300' : 'text-purple-700'}>{part.slice(2, -2)}</strong>;
            }
            return part;
        });
    };

    const renderMarkdown = (text: string) => {
        return text
            .replace(/### (.*)/g, '<h3 class="text-base font-bold mt-4 mb-2">$1</h3>')
            .replace(/## (.*)/g, '<h2 class="text-lg font-bold mt-5 mb-2">$1</h2>')
            .replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-purple-300">$1</strong>')
            .replace(/- (.*)/g, '<li class="ml-4 mb-1">$1</li>')
            .replace(/\n/g, '<br/>');
    };

    const renderAbstractMarkdown = (text: string) => {
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold">$1</strong>')
            .replace(/\*(.*?)\*/g, '<em class="italic">$1</em>')
            .replace(/`(.*?)`/g, '<code class="bg-gray-100 px-1 rounded text-sm font-mono">$1</code>')
            .replace(/\n\n/g, '</p><p class="mb-4">')
            .replace(/\n/g, '<br/>');
    };


    if (viewMode === ViewMode.TRANSLATION) {
        return (
            <div className="mt-4 animate-fade-in px-6 pb-2">
                <div className={`p-4 rounded-xl border mb-4 ${isDark ? 'bg-white/5 border-white/5' : 'bg-gray-50 border-gray-200'}`}>
                    <p className="text-xs text-green-500 font-mono mb-3 uppercase tracking-wider font-bold">{language === 'en' ? 'Translated Abstract' : '中文摘要'}</p>
                    <p className={`text-base leading-relaxed whitespace-pre-wrap font-sans text-justify md:max-w-prose md:text-lg ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
                        {paper.translatedAbstract || (language === 'en' ? "Translating..." : "正在翻译...")}
                    </p>
                </div>
                <div className="flex justify-end opacity-50"><span className="text-[10px] font-mono text-gray-500">{ui.translatedBy}</span></div>
            </div>
        );
    }

    if (viewMode === ViewMode.AI_INSIGHT) {
        const aiInsights = paper.aiInsights;
        if (!aiInsights || aiInsights.length === 0) {
            return (
                <div className="mt-4 px-6 pb-2">
                    <div className="flex items-center gap-2 pb-2"><Sparkles className="w-4 h-4 text-purple-500" /><h2 className={`text-sm font-bold uppercase tracking-widest ${isDark ? 'text-purple-100' : 'text-purple-900'}`}>{ui.aiInsights}</h2></div>
                    <p className={`text-base ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>暂无 AI 解读</p>
                </div>
            );
        }

        let aiContent;
        if (Array.isArray(aiInsights)) {
            // JSON array format
            aiContent = aiInsights.map((item, idx) => (
                <div key={idx} className="mb-4">
                    {item.zh && <p className="mb-1 text-justify"><span className="font-bold">{item.zh.split('：')[0]}：</span>{item.zh.split('：')[1] || ''}</p>}
                    {item.en && <p className="text-sm opacity-70 text-justify">{item.en}</p>}
                </div>
            ));
        } else if (typeof aiInsights === 'string') {
            // String/Markdown format
            aiContent = (
                <div
                    className="prose prose-sm max-w-none"
                    dangerouslySetInnerHTML={{ __html: renderMarkdown(aiInsights) }}
                />
            );
        }

        return (
            <div className="mt-4 px-6 pb-2">
                <div className="flex items-center gap-2 pb-2"><Sparkles className="w-4 h-4 text-purple-500" /><h2 className={`text-sm font-bold uppercase tracking-widest ${isDark ? 'text-purple-100' : 'text-purple-900'}`}>{ui.aiInsights}</h2></div>
                <div className={`text-base ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                    {aiContent}
                </div>
            </div>
        );
    }

    // Default: Original Abstract
    return (
        <div className="mt-4 animate-fade-in px-6 pb-2">
            <div
                className={`text-base leading-relaxed font-serif tracking-wide text-justify opacity-90 md:max-w-prose md:text-lg md:mx-auto ${isDark ? 'text-gray-200' : 'text-gray-900'}`}
                dangerouslySetInnerHTML={{ __html: `<p>${renderAbstractMarkdown(paper.abstract)}</p>` }}
            />
            <div className={`text-xs mt-8 font-mono border-t pt-4 ${isDark ? 'text-gray-600 border-gray-800' : 'text-gray-400 border-gray-200'}`}>{ui.published}: {paper.publishedDate}</div>
        </div>
    );
};

export default PaperCardTextContent;
