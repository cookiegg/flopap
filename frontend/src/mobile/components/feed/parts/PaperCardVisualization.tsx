import React, { useState, useEffect } from 'react';
import { Paper, AppLanguage, AppTheme } from '../../../../types';
import { AlertTriangle, Loader2, Image as ImageIcon } from 'lucide-react';
import { UI_STRINGS } from '../../../../constants';
import { AIService } from '../../../../services/aiService';
import { APIKeyService } from '../../../../services/apiKeyService';
import { saveVisualization } from '../../../../services/backendService';

interface PaperCardVisualizationProps {
    paper: Paper;
    language: AppLanguage;
    theme: AppTheme;
    onUpdatePaper: (paper: Paper) => void;
}

const PaperCardVisualization: React.FC<PaperCardVisualizationProps> = ({
    paper,
    language,
    theme,
    onUpdatePaper
}) => {
    const isDark = theme === 'dark';
    const ui = UI_STRINGS[language];

    const [visStatus, setVisStatus] = useState<'idle' | 'confirm' | 'generating' | 'error'>('idle');
    const [loadingAI, setLoadingAI] = useState(false);
    const [errorMsg, setErrorMsg] = useState('');
    const [visualizationUrl, setVisualizationUrl] = useState<string>(paper.visual_html || paper.visualizationUrl || '');

    useEffect(() => {
        const visualData = paper.visual_html || paper.visualizationUrl || '';
        setVisualizationUrl(visualData);
    }, [paper.id, paper.visual_html, paper.visualizationUrl]);

    const handleGenerateVis = async () => {
        // 1. Check API Key
        const hasKey = APIKeyService.getAPIKey('gemini');
        if (!hasKey) {
            setVisStatus('error');
            setErrorMsg('未配置 Google Gemini API 密钥。请前往设置页配置。');
            return;
        }

        setVisStatus('generating');
        setLoadingAI(true);
        try {
            const prompt = `Create an educational infographic to explain this academic paper in simple terms:

Paper Title: ${paper.title}

Paper Abstract: ${paper.abstract.substring(0, 600)}

Requirements:
1. Simple diagrams showing core concepts
2. Clear method/approach flowchart with step-by-step process
3. Key results visualization (charts or comparisons)
4. Use English labels, concise and easy to understand
5. Style: Clean, academic but accessible, like a science magazine illustration
6. Colors: Bright and clear, well-coordinated palette
7. Layout: Well-organized with clear sections

Generate a complete infographic.`;

            // Gemini Image Call (gemini-3-pro-image)
            const result = await AIService.generateImage({
                service: 'gemini',
                prompt: prompt
            });

            if (result.success && result.content) {
                console.log('[handleGenerateVis] AI generation successful, content length:', result.content.length);

                // Save to Backend
                console.log('[handleGenerateVis] Saving to backend...');
                const saveSuccess = await saveVisualization(paper.id, result.content);

                if (saveSuccess) {
                    console.log('[handleGenerateVis] Save successful, updating local state');
                    // Update Local State
                    setVisualizationUrl(result.content);
                    onUpdatePaper({ ...paper, visualizationUrl: result.content });
                    setVisStatus('idle');
                } else {
                    console.error('[handleGenerateVis] Save failed');
                    throw new Error('保存可视化图到服务器失败');
                }
            } else {
                console.error('[handleGenerateVis] AI generation failed:', result.error);
                throw new Error(result.error || '生成失败');
            }
        } catch (e: any) {
            setVisStatus('error');
            setErrorMsg(e.message || '生成出错');
        } finally {
            setLoadingAI(false);
        }
    };

    if (visualizationUrl) {
        return (
            <div className="flex flex-col mt-4 animate-fade-in px-6 pb-2 items-center">
                <div className="relative rounded-2xl overflow-hidden shadow-2xl border border-white/10 w-full aspect-square md:aspect-video md:max-h-[60vh] bg-black">
                    <img src={visualizationUrl} alt="AI Visualization" className="w-full h-full object-cover" />
                    <div className="absolute bottom-4 left-4 right-4"><span className="text-xs font-mono text-orange-400 bg-orange-900/60 px-2 py-1 rounded backdrop-blur-md border border-orange-500/30">{ui.visualExp}</span></div>
                </div>
            </div>
        )
    }

    return (
        <div className="flex flex-col justify-center items-center mt-8 px-8 animate-fade-in text-center h-full pb-2">
            <div className="mb-6 bg-orange-500/10 p-6 rounded-full border border-orange-500/30"><ImageIcon size={48} className="text-orange-500" /></div>

            {visStatus === 'idle' || visStatus === 'error' ? (
                <div className="space-y-6">
                    <h2 className={`text-xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>{ui.generateVis}</h2>
                    <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>暂无可视化图。可使用 AI 生成。</p>
                    {visStatus === 'error' && <div className="bg-red-500/10 border border-red-500/30 text-red-500 px-4 py-2 rounded-lg text-xs font-bold">{errorMsg}</div>}
                    <button onClick={(e) => { e.stopPropagation(); setVisStatus('confirm'); }} className={`${isDark ? 'bg-white text-black' : 'bg-gray-900 text-white'} font-bold py-3 px-8 rounded-full hover:scale-105 transition-transform shadow-lg`}>{ui.startGen}</button>
                </div>
            ) : visStatus === 'confirm' ? (
                <div className={`backdrop-blur-md p-6 rounded-2xl border w-full max-w-sm animate-fade-in ${isDark ? 'bg-gray-800/80 border-yellow-500/30' : 'bg-white/90 border-yellow-500/50 shadow-lg'}`}>
                    <div className="flex justify-center mb-4 text-yellow-500"><AlertTriangle size={32} /></div>
                    <h3 className={`text-lg font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>{ui.highCost}</h3>
                    <div className={`text-left p-4 rounded-lg mb-6 space-y-2 text-sm ${isDark ? 'bg-black/40' : 'bg-gray-100'}`}>
                        <div className="flex justify-between"><span className="text-gray-500">{ui.estCost}:</span><span className="text-yellow-600 font-mono font-bold">$0.134</span></div>
                        <div className="flex justify-between"><span className="text-gray-500">模型:</span><span className={`${isDark ? 'text-white' : 'text-gray-900'} font-mono`}>gemini-3-pro-image</span></div>
                        <div className="flex justify-between"><span className="text-gray-500">{ui.estTime}:</span><span className={`${isDark ? 'text-white' : 'text-gray-900'} font-mono`}>30-60s</span></div>
                        <p className="text-xs text-red-400 mt-2 font-bold">耗资不菲, 请谨慎操作</p>
                    </div>
                    <div className="flex gap-3">
                        <button onClick={(e) => { e.stopPropagation(); setVisStatus('idle'); }} className="flex-1 py-3 rounded-xl font-bold text-gray-500 hover:bg-black/5">{ui.cancel}</button>
                        <button onClick={(e) => { e.stopPropagation(); handleGenerateVis(); }} className="flex-1 bg-yellow-500 text-black py-3 rounded-xl font-bold hover:bg-yellow-400 shadow-lg">{ui.confirm}</button>
                    </div>
                </div>
            ) : (
                <div className="space-y-6 animate-pulse w-full max-w-sm">
                    <h3 className={`text-xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>{ui.generating}</h3>
                    <div className="w-full bg-gray-200 h-2 rounded-full overflow-hidden"><div className="h-full bg-orange-500 w-2/3 animate-[shimmer_2s_infinite_linear]" /></div>
                </div>
            )}
        </div>
    );
};

export default PaperCardVisualization;
