import React, { useEffect, useState, useCallback, useRef } from 'react';
import { Paper, ViewMode, AppLanguage, AppTheme } from '../../types';
import { AIService } from '../../services/aiService';
import { APIKeyService } from '../../services/apiKeyService';
import { saveInfographic, saveVisualization, checkInfographicStatus, getInfographic } from '../../services/backendService';
import { Heart, Loader2, Sparkles, Image as ImageIcon, AlertTriangle, Globe, BarChart2, FileCode } from 'lucide-react';
import { UI_STRINGS } from '../../constants';
import PaperInfographicReal from './PaperInfographicReal';

// 全局并发控制
const infographicCheckQueue = new Map<string, Promise<any>>();
const MAX_CONCURRENT_CHECKS = 5;
let activeChecks = 0;

interface PaperCardProps {
  paper: Paper;
  viewMode: ViewMode;
  isActive: boolean;
  isLiked: boolean;
  isBookmarked: boolean;
  onUpdatePaper: (paper: Paper) => void;
  onToggleLike: () => void;
  onToggleBookmark: () => void;
  onNotInterested: () => void;
  language: AppLanguage;
  onSwipe?: (direction: 'left' | 'right') => void;
  theme: AppTheme;
  onInfographicHtmlChange?: (html: string) => void;
  index?: number;
  total?: number;
}

const PaperCard: React.FC<PaperCardProps> = ({
  paper,
  viewMode,
  isActive,
  isLiked,
  onUpdatePaper,
  onToggleLike,
  language,
  onSwipe,
  theme,
  onInfographicHtmlChange,
  index,
  total
}) => {
  const [loadingAI, setLoadingAI] = useState(false);
  const ui = UI_STRINGS[language];
  const isDark = theme === 'dark';

  // Status Machine: 'idle' | 'confirm' | 'generating' | 'error'
  const [visStatus, setVisStatus] = useState<'idle' | 'confirm' | 'generating' | 'error'>('idle');
  const [infoStatus, setInfoStatus] = useState<'idle' | 'confirm' | 'generating' | 'error'>('idle');
  const [errorMsg, setErrorMsg] = useState('');

  // Double Tap & Swipe State
  const lastTapRef = useRef<number>(0);
  const [showBigHeart, setShowBigHeart] = useState(false);
  const touchStartRef = useRef<{ x: number, y: number } | null>(null);

  // Infographic state - 直接使用paper中的数据
  const [infographicHtml, setInfographicHtml] = useState<string>(paper.infographicHtml || '');
  const [hasInfographic, setHasInfographic] = useState<boolean>(!!paper.infographicHtml);
  const [checkingInfographic, setCheckingInfographic] = useState<boolean>(false);

  // Visualization state - 优先使用visual_html，回退到visualizationUrl
  const [visualizationUrl, setVisualizationUrl] = useState<string>(paper.visual_html || paper.visualizationUrl || '');
  const [hasVisualization, setHasVisualization] = useState<boolean>(!!paper.visual_html || !!paper.visualizationUrl);

  useEffect(() => {
    // 直接使用feed中的信息图数据
    setInfographicHtml(paper.infographicHtml || '');
    setHasInfographic(!!paper.infographicHtml);
  }, [paper.id, paper.infographicHtml]);

  useEffect(() => {
    // 优先使用feed中的visual_html数据，回退到visualizationUrl
    const visualData = paper.visual_html || paper.visualizationUrl || '';
    setVisualizationUrl(visualData);
    setHasVisualization(!!visualData);
  }, [paper.id, paper.visual_html, paper.visualizationUrl]);

  const handleInfographicLoaded = (html: string) => {
    setInfographicHtml(html);
    if (isActive) {
      onInfographicHtmlChange?.(html);
    }
  };

  const bgSeed = paper.id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  const hue = bgSeed % 360;

  useEffect(() => {
    setVisStatus('idle');
    setInfoStatus('idle');
    setErrorMsg('');
  }, [paper.id]);

  // --- GENERATION HANDLERS ---

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

        // Clean up Markdown code blocks if present
        let cleanContent = result.content;
        if (cleanContent.includes('```')) {
          cleanContent = cleanContent
            .replace(/^```html\s*/i, '') // Remove start ```html
            .replace(/^```\s*/, '')      // Remove start ``` (if no html tag)
            .replace(/```\s*$/, '');     // Remove end ```
          console.log('[handleGenerateInfographic] Cleaned markdown artifacts from content');
        }

        // Save to Backend
        console.log('[handleGenerateInfographic] Saving to backend...');
        const saveSuccess = await saveInfographic(paper.id, cleanContent);

        if (saveSuccess) {
          console.log('[handleGenerateInfographic] Save successful, updating local state');
          // Update Local State
          setInfographicHtml(cleanContent);
          setHasInfographic(true);
          onUpdatePaper({ ...paper, infographicHtml: cleanContent });
          setInfoStatus('idle');

          // Refresh status to ensure consistency
          setTimeout(async () => {
            try {
              const status = await checkInfographicStatus(paper.id);
              setHasInfographic(status.has_infographic);
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
          setHasVisualization(true);
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

  // ... (Touch/Swipe handlers) ...
  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartRef.current = { x: e.touches[0].clientX, y: e.touches[0].clientY };
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    if (!touchStartRef.current || !onSwipe) return;
    const deltaX = e.changedTouches[0].clientX - touchStartRef.current.x;
    const deltaY = e.changedTouches[0].clientY - touchStartRef.current.y;
    const MIN_SWIPE_DISTANCE = 80;
    const horizontalRatio = 3.0;
    if (Math.abs(deltaX) > MIN_SWIPE_DISTANCE && Math.abs(deltaX) > Math.abs(deltaY) * horizontalRatio) {
      if (deltaX > 0) onSwipe('right');
      else onSwipe('left');
    }
    touchStartRef.current = null;
  };

  // Prevent scroll chaining: stop wheel events from propagating to snap-scroll parent
  const handleWheel = (e: React.WheelEvent<HTMLDivElement>) => {
    const target = e.currentTarget;
    const { scrollTop, scrollHeight, clientHeight } = target;
    const atTop = scrollTop <= 0;
    const atBottom = scrollTop + clientHeight >= scrollHeight - 1;

    // If scrolling up at top, or down at bottom, allow propagation (so user can navigate cards)
    // Otherwise, stop propagation to keep scroll within the card
    if ((e.deltaY < 0 && atTop) || (e.deltaY > 0 && atBottom)) {
      // At boundary, allow default behavior (card navigation)
      return;
    }
    // Not at boundary, stop propagation to prevent card snap
    e.stopPropagation();
  };

  const handleDoubleTap = (e: React.MouseEvent) => {
    const now = Date.now();
    if (now - lastTapRef.current < 300) {
      if (!isLiked) onToggleLike();
      setShowBigHeart(true);
      setTimeout(() => setShowBigHeart(false), 1000);
    }
    lastTapRef.current = now;
  };

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
      // 备用方案 - 可以添加提示或禁用按钮
      console.warn('No external link available for this paper');
    }
  };

  // ... (Render Header) ...
  const renderHeader = () => {
    const showBilingualTitle = viewMode === ViewMode.TRANSLATION || language === 'zh';
    const titleColor = isDark ? 'text-white' : 'text-gray-900';
    const subTitleColor = isDark ? 'text-gray-400' : 'text-gray-600';
    const authorColor = isDark ? 'text-gray-400' : 'text-gray-500';
    const bgHeader = isDark ? 'bg-gradient-to-b from-transparent to-black/10' : 'bg-transparent';

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
            <button onClick={handleOpenWeb} className={`${subTitleColor} hover:text-blue-500 transition-colors`}><Globe size={16} /></button>
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

  const renderBodyContent = () => {
    // 1. INFOGRAPHIC VIEW
    if (viewMode === ViewMode.INFOGRAPHIC) {
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
            </div>
          ) : infoStatus === 'confirm' ? (
            <div className={`backdrop-blur-md p-6 rounded-2xl border w-full max-w-sm animate-fade-in ${isDark ? 'bg-gray-800/80 border-blue-500/30' : 'bg-white/90 border-blue-500/50 shadow-lg'}`}>
              <div className="flex justify-center mb-4 text-blue-500"><FileCode size={32} /></div>
              <h3 className={`text-lg font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>确认生成?</h3>
              <div className={`text-left p-4 rounded-lg mb-6 space-y-2 text-sm ${isDark ? 'bg-black/40' : 'bg-white border border-gray-100'}`}>
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
    }

    // 2. VISUALIZATION VIEW
    if (viewMode === ViewMode.VISUALIZATION) {
      const visualData = paper.visual_html || paper.visualizationUrl;
      if (visualData) {
        return (
          <div className="flex flex-col mt-4 animate-fade-in px-6 pb-2 items-center">
            <div className="relative rounded-2xl overflow-hidden shadow-2xl border border-white/10 w-full aspect-square md:aspect-video md:max-h-[60vh] bg-black">
              <img src={visualData} alt="AI Visualization" className="w-full h-full object-cover" />
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
              <div className={`text-left p-4 rounded-lg mb-6 space-y-2 text-sm ${isDark ? 'bg-black/40' : 'bg-white border border-gray-100'}`}>
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
    }

    // 3. TRANSLATION VIEW
    if (viewMode === ViewMode.TRANSLATION) {
      return (
        <div className="mt-4 animate-fade-in px-6 pb-2">
          <div className={`p-4 rounded-xl border mb-4 ${isDark ? 'bg-white/5 border-white/5' : 'bg-white border-gray-200'}`}>
            <p className="text-xs text-green-500 font-mono mb-3 uppercase tracking-wider font-bold">{language === 'en' ? 'Translated Abstract' : '中文摘要'}</p>
            <p className={`text-base leading-relaxed whitespace-pre-wrap font-sans text-justify md:text-lg ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
              {paper.translatedAbstract || (language === 'en' ? "Translating..." : "正在翻译...")}
            </p>
          </div>
          <div className="flex justify-end opacity-50"><span className="text-[10px] font-mono text-gray-500">{ui.translatedBy}</span></div>
        </div>
      );
    }

    // 4. AI INSIGHTS VIEW
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

      // 定义内联样式渲染函数
      const renderInlineStyles = (text: string) => {
        const parts = text.split(/(\*\*[^*]+\*\*)/g);
        return parts.map((part, i) => {
          if (part.startsWith('**') && part.endsWith('**')) {
            return <strong key={i} className={isDark ? 'text-purple-300' : 'text-purple-700'}>{part.slice(2, -2)}</strong>;
          }
          return part;
        });
      };

      // 处理AI解读显示
      let aiContent;
      if (Array.isArray(aiInsights)) {
        // 如果是数组格式（JSON解析成功的情况）
        aiContent = aiInsights.map((item, idx) => (
          <div key={idx} className="mb-4">
            {item.zh && <p className="mb-1 text-justify"><span className="font-bold">{item.zh.split('：')[0]}：</span>{item.zh.split('：')[1] || ''}</p>}
            {item.en && <p className="text-sm opacity-70 text-justify">{item.en}</p>}
          </div>
        ));
      } else if (typeof aiInsights === 'string') {
        // 如果是字符串格式（纯文本），可以选择markdown渲染
        // 选择1：简单的markdown渲染
        const renderMarkdown = (text: string) => {
          return text
            .replace(/### (.*)/g, '<h3 class="text-base font-bold mt-4 mb-2">$1</h3>')
            .replace(/## (.*)/g, '<h2 class="text-lg font-bold mt-5 mb-2">$1</h2>')
            .replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-purple-300">$1</strong>')
            .replace(/- (.*)/g, '<li class="ml-4 mb-1">$1</li>')
            .replace(/\n/g, '<br/>');
        };

        aiContent = (
          <div
            className="prose prose-sm max-w-none"
            dangerouslySetInnerHTML={{ __html: renderMarkdown(aiInsights) }}
          />
        );

        // 选择2：保持原有的逐行渲染（注释掉上面的代码，取消注释下面的代码）
        /*
        aiContent = aiInsights.split('\n').map((line, idx) => {
          const trimmed = line.trim();
          if (!trimmed) return <div key={idx} className="h-2" />;
          if (trimmed.startsWith('### ')) return <h3 key={idx} className={`text-base font-bold mt-4 mb-2 ${isDark ? 'text-purple-300' : 'text-purple-700'}`}>{trimmed.replace(/^###\s+/, '')}</h3>;
          if (trimmed.startsWith('## ')) return <h2 key={idx} className={`text-lg font-bold mt-5 mb-2 ${isDark ? 'text-purple-200' : 'text-purple-800'}`}>{trimmed.replace(/^##\s+/, '')}</h2>;
          if (trimmed.startsWith('- ')) return <div key={idx} className="flex gap-2 ml-4 mb-1"><span className="text-purple-500 mt-1.5 w-1.5 h-1.5 rounded-full bg-purple-500 shrink-0 block" /><p className="flex-1 leading-relaxed">{trimmed.replace(/^- /, '')}</p></div>;
          return <p key={idx} className="mb-2 leading-relaxed whitespace-pre-wrap">{renderInlineStyles(trimmed)}</p>;
        });
        */
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

    // 5. ORIGINAL VIEW (Abstract)
    const renderAbstractMarkdown = (text: string) => {
      return text
        .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold">$1</strong>')
        .replace(/\*(.*?)\*/g, '<em class="italic">$1</em>')
        .replace(/`(.*?)`/g, '<code class="bg-gray-100 px-1 rounded text-sm font-mono">$1</code>')
        .replace(/\n\n/g, '</p><p class="mb-4">')
        .replace(/\n/g, '<br/>');
    };

    return (
      <div className="mt-4 animate-fade-in px-6 pb-2">
        <div
          className={`text-base leading-relaxed font-serif tracking-wide text-justify opacity-90 md:text-lg ${isDark ? 'text-gray-200' : 'text-gray-900'}`}
          dangerouslySetInnerHTML={{ __html: `<p>${renderAbstractMarkdown(paper.abstract)}</p>` }}
        />
        <div className={`text-xs mt-8 font-mono border-t pt-4 ${isDark ? 'text-gray-600 border-gray-800' : 'text-gray-400 border-gray-200'}`}>{ui.published}: {paper.publishedDate}</div>
      </div>
    );
  };

  return (
    <div className={`snap-start w-full h-full relative flex flex-col overflow-hidden shrink-0 ${isDark ? 'bg-black' : 'bg-white'}`} onTouchStart={handleTouchStart} onTouchEnd={handleTouchEnd}>
      <div className={`absolute inset-0 transition-colors duration-1000 pointer-events-none ${isDark ? 'opacity-20' : 'opacity-0'}`} style={{ background: `radial-gradient(circle at 80% 20%, hsl(${hue}, 70%, 20%), ${isDark ? '#000000' : '#ffffff'})` }} />
      <div className={`absolute inset-0 pointer-events-none z-0 ${isDark ? 'bg-gradient-to-b from-black/80 via-black/50 to-black' : 'bg-white'}`} />

      {showBigHeart && (
        <div className="absolute inset-0 z-50 flex items-center justify-center pointer-events-none animate-bounce">
          <Heart className="w-32 h-32 text-red-500 fill-current drop-shadow-2xl animate-pulse" />
        </div>
      )}

      {loadingAI && (
        <div className="absolute top-24 right-4 z-50 animate-fade-in">
          <div className="bg-blue-600/90 backdrop-blur-md text-white text-xs px-3 py-1.5 rounded-full flex items-center gap-2 shadow-lg border border-blue-400/30">
            <Loader2 size={12} className="animate-spin" />
            <span className="font-medium">{ui.generating}</span>
          </div>
        </div>
      )}

      <div className="relative z-10 w-full h-full flex flex-col" onClick={handleDoubleTap}>
        {renderHeader()}
        <div className="flex-1 overflow-y-auto overscroll-contain no-scrollbar scroll-smooth relative" onTouchStart={handleTouchStart} onTouchEnd={handleTouchEnd}>
          {renderBodyContent()}
        </div>
        {total !== undefined && total > 0 && index !== undefined && (
          <div className={`pb-4 text-sm font-mono font-bold text-center select-none transition-colors duration-300 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <span className="opacity-60">{index}</span><span className="mx-1 opacity-40">/</span><span className="opacity-60">{total}</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default PaperCard;
