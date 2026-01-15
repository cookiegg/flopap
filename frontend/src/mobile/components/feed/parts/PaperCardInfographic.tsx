import React, { useState, useEffect } from 'react';
import { Paper, AppLanguage, AppTheme } from '../../../../types';
import { Loader2, BarChart2, FileCode } from 'lucide-react';
import { UI_STRINGS } from '../../../../constants';
import { AIService } from '../../../../services/aiService';
import { APIKeyService } from '../../../../services/apiKeyService';
import { saveInfographic, checkInfographicStatus } from '../../../../services/backendService';
import PaperInfographicReal from '../PaperInfographicReal';

interface PaperCardInfographicProps {
    paper: Paper;
    language: AppLanguage;
    theme: AppTheme;
    isActive: boolean;
    onUpdatePaper: (paper: Paper) => void;
    onInfographicHtmlChange?: (html: string) => void;
    onSwipe?: (direction: 'left' | 'right') => void;
}

const PaperCardInfographic: React.FC<PaperCardInfographicProps> = ({
    paper,
    language,
    theme,
    isActive,
    onUpdatePaper,
    onInfographicHtmlChange,
    onSwipe
}) => {
    const isDark = theme === 'dark';
    const ui = UI_STRINGS[language];

    const [infoStatus, setInfoStatus] = useState<'idle' | 'confirm' | 'generating' | 'error'>('idle');
    const [loadingAI, setLoadingAI] = useState(false);
    const [errorMsg, setErrorMsg] = useState('');
    const [infographicHtml, setInfographicHtml] = useState<string>(paper.infographicHtml || '');
    const [checkingInfographic, setCheckingInfographic] = useState<boolean>(false);

    useEffect(() => {
        setInfographicHtml(paper.infographicHtml || '');
    }, [paper.id, paper.infographicHtml]);

    const handleInfographicLoaded = (html: string) => {
        setInfographicHtml(html);
        if (isActive) {
            onInfographicHtmlChange?.(html);
        }
    };

    const handleGenerateInfographic = async () => {
        // 1. Check API Key
        const hasKey = APIKeyService.getAPIKey('deepseek');
        if (!hasKey) {
            setInfoStatus('error');
            setErrorMsg('未配置 DeepSeek API 密钥。请前往设置页配置。');
            return;
        }

        setInfoStatus('generating');
        setLoadingAI(true);

        try {
            const prompt = `你是一个专业的学术信息可视化专家。请根据以下论文信息，生成一个视觉化的信息图网页。

论文标题：${paper.title}

论文摘要：${paper.abstract}

要求：
1. **结构**：按照"问题→方法→结果"三段式组织
2. **技术**：使用纯 HTML + 内联 CSS，不依赖外部库
3. **风格**：
   - 深色主题（背景 #0f172a）
   - 使用渐变色和图标（Unicode emoji 或 CSS 绘制）
   - 卡片式布局，圆角阴影
4. **内容**：
   - 用简洁的中文描述（每段不超过 50 字）
   - 多用视觉元素：流程图、对比图、数据可视化
   - 关键数字和术语用醒目颜色标注
5. **移动端优化**：
   - viewport 设置为 width=device-width, initial-scale=1.0
   - 默认宽度 100%，最大宽度 600px，居中显示
   - 字体大小适合手机阅读（16px 基准）
   - 内边距使用 16-20px，适合手指触控
   - 垂直滚动，总高度约 1000-1400px（适配主流手机屏幕比例）
6. **布局**：优先为竖屏手机设计（9:16 或 9:19.5 比例）

直接输出完整的 HTML 代码，不要有任何解释文字。代码要完整可运行。`;

            // DeepSeek Reasoner Call
            const result = await AIService.generateContent({
                service: 'deepseek',
                prompt: prompt,
                maxTokens: 4000
            });

            if (result.success && result.content) {
                console.log('[handleGenerateInfographic] AI generation successful, content length:', result.content.length);

                // Save to Backend
                console.log('[handleGenerateInfographic] Saving to backend...');
                const saveSuccess = await saveInfographic(paper.id, result.content);

                if (saveSuccess) {
                    console.log('[handleGenerateInfographic] Save successful, updating local state');
                    // Update Local State
                    setInfographicHtml(result.content);
                    onUpdatePaper({ ...paper, infographicHtml: result.content });
                    setInfoStatus('idle');

                    // Refresh status to ensure consistency
                    setTimeout(async () => {
                        try {
                            const status = await checkInfographicStatus(paper.id);
                            // logic relying on has_infographic check can happen here but we already updated local state
                        } catch (error) {
                            console.error('Failed to refresh infographic status:', error);
                        }
                    }, 1000);
                } else {
                    console.error('[handleGenerateInfographic] Save failed');
                    throw new Error('保存信息图到服务器失败');
                }
            } else {
                console.error('[handleGenerateInfographic] AI generation failed:', result.error);
                throw new Error(result.error || '生成失败');
            }
        } catch (e: any) {
            setInfoStatus('error');
            setErrorMsg(e.message || '生成出错');
        } finally {
            setLoadingAI(false);
        }
    };

    if (checkingInfographic) {
        return (
            <div className="mt-4 flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
                <span className="ml-2 text-gray-600">检查信息图状态...</span>
            </div>
        );
    }

    if (infographicHtml) {
        return (
            <div className="mt-4 animate-fade-in pb-2 h-full">
                <PaperInfographicReal paper={{ ...paper, infographicHtml }} isDark={isDark} onHtmlLoaded={handleInfographicLoaded} onSwipe={onSwipe} />
            </div>
        );
    }

    // Empty State
    return (
        <div className="flex flex-col justify-center items-center mt-8 px-8 animate-fade-in text-center h-full pb-2">
            <div className="mb-6 bg-blue-500/10 p-6 rounded-full border border-blue-500/30">
                <BarChart2 size={48} className="text-blue-500" />
            </div>

            {infoStatus === 'idle' || infoStatus === 'error' ? (
                <div className="space-y-6">
                    <h2 className={`text-xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>由 AI 生成信息图</h2>
                    <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>这篇论文尚未生成信息图。您可以使用 DeepSeek Reasoner 模型生成一张。</p>

                    {infoStatus === 'error' && (
                        <div className="bg-red-500/10 border border-red-500/30 text-red-500 px-4 py-2 rounded-lg text-xs font-bold">
                            {errorMsg}
                        </div>
                    )}

                    <button
                        onClick={(e) => { e.stopPropagation(); setInfoStatus('confirm'); }}
                        className={`${isDark ? 'bg-blue-600 text-white' : 'bg-blue-600 text-white'} font-bold py-3 px-8 rounded-full hover:scale-105 transition-transform shadow-lg`}
                    >
                        生成信息图
                    </button>
                    {loadingAI && (
                        <div className="flex justify-center items-center gap-2 text-blue-500 text-sm animate-pulse">
                            <Loader2 className="w-4 h-4 animate-spin" />
                            <span>正在生成... (这可能需要几分钟)</span>
                        </div>
                    )}
                </div>
            ) : infoStatus === 'confirm' ? (
                <div className={`backdrop-blur-md p-6 rounded-2xl border w-full max-w-sm animate-fade-in ${isDark ? 'bg-gray-800/80 border-blue-500/30' : 'bg-white/90 border-blue-500/50 shadow-lg'}`}>
                    <div className="flex justify-center mb-4 text-blue-500"><FileCode size={32} /></div>
                    <h3 className={`text-lg font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>确认生成?</h3>
                    <div className={`text-left p-4 rounded-lg mb-6 space-y-2 text-sm ${isDark ? 'bg-black/40' : 'bg-gray-100'}`}>
                        <div className="flex justify-between text-xs">
                            <span className="text-gray-500">模型:</span>
                            <span className={`${isDark ? 'text-white' : 'text-gray-900'} font-mono`}>deepseek-reasoner</span>
                        </div>
                        <p className="text-xs text-gray-400 mt-2">将消耗您的 DeepSeek API 额度。</p>
                    </div>
                    <div className="flex gap-3">
                        <button onClick={(e) => { e.stopPropagation(); setInfoStatus('idle'); }} className="flex-1 py-3 rounded-xl font-bold text-gray-500 hover:bg-black/5">取消</button>
                        <button onClick={(e) => { e.stopPropagation(); handleGenerateInfographic(); }} className="flex-1 bg-blue-600 text-white py-3 rounded-xl font-bold hover:bg-blue-500 shadow-lg">确认生成</button>
                    </div>
                </div>
            ) : (
                <div className="space-y-6 animate-pulse w-full max-w-sm">
                    <h3 className={`text-xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>正在分析论文结构...</h3>
                    <div className="w-full bg-gray-200 h-2 rounded-full overflow-hidden">
                        <div className="h-full bg-blue-500 w-2/3 animate-[shimmer_2s_infinite_linear]" />
                    </div>
                </div>
            )}
        </div>
    );
};

export default PaperCardInfographic;
