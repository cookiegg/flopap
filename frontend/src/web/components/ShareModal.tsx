import React, { useRef } from 'react';
import { X, FileImage, Loader2, Download, Share2, FileText, Languages, Lightbulb } from 'lucide-react';
import { Paper, ViewMode } from '../../types';
import { useShare } from '../../hooks/useShare';
import SimplifiedShareCard from './SimplifiedShareCard';
import OriginalShareCard from './OriginalShareCard';
import TranslationShareCard from './TranslationShareCard';

interface ShareModalProps {
  paper: Paper;
  isOpen: boolean;
  onClose: () => void;
  isDark: boolean;
  currentViewMode: ViewMode;  // 当前视图模式
  infographicHtml?: string;
}

const ShareModal: React.FC<ShareModalProps> = ({ 
  paper, 
  isOpen, 
  onClose, 
  isDark,
  currentViewMode,
  infographicHtml 
}) => {
  const { share, isGenerating } = useShare();
  const containerRef = useRef<HTMLDivElement>(null);

  if (!isOpen) return null;
  
  // 根据当前视图模式确定分享内容
  const getShareConfig = () => {
    switch (currentViewMode) {
      case ViewMode.ORIGINAL:
        return {
          title: '原文视图',
          description: '论文英文原文 + 二维码',
          icon: FileText,
        };
      case ViewMode.TRANSLATION:
        return {
          title: '翻译视图',
          description: '论文中文翻译 + 二维码',
          icon: Languages,
        };
      case ViewMode.AI_INSIGHT:
        return {
          title: 'AI 解读视图',
          description: 'AI 核心解读 + 二维码',
          icon: Lightbulb,
        };
      case ViewMode.INFOGRAPHIC:
        return {
          title: '信息图视图',
          description: '完整可视化内容 + 二维码',
          icon: FileImage,
        };
      default:
        return {
          title: '当前视图',
          description: '当前内容 + 二维码',
          icon: FileText,
        };
    }
  };
  
  const shareConfig = getShareConfig();

  const handleShare = async (action: 'save' | 'share') => {
    if (!containerRef.current) return;
    
    const targetElement = containerRef.current.querySelector(
      '[data-share-card="current"]'
    ) as HTMLElement;
    
    if (!targetElement) return;

    // 等待渲染完成（不显示给用户）
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    const success = await share(targetElement, paper.title, action);
    
    if (success) {
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80">
      <div className={`${isDark ? 'bg-slate-800' : 'bg-white'} rounded-2xl max-w-md w-full max-h-[90vh] overflow-y-auto`}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <h3 className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>
            分享论文
          </h3>
          <button onClick={onClose} className={`p-2 hover:bg-slate-700 rounded-lg ${isDark ? 'text-white' : 'text-slate-900'}`}>
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* View Info */}
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 bg-blue-500/20 rounded-xl">
              <shareConfig.icon size={32} className="text-blue-400" />
            </div>
            <div className="flex-1">
              <div className="text-lg font-semibold text-white">{shareConfig.title}</div>
              <div className="text-sm text-slate-400">{shareConfig.description}</div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3">
            <button
              onClick={() => handleShare('save')}
              disabled={isGenerating}
              className="flex-1 py-3 px-4 bg-blue-600 hover:bg-blue-700 rounded-xl text-white font-medium disabled:opacity-50 flex items-center justify-center gap-2 transition-colors"
            >
              <Download size={20} />
              保存图片
            </button>
            <button
              onClick={() => handleShare('share')}
              disabled={isGenerating}
              className="flex-1 py-3 px-4 bg-emerald-600 hover:bg-emerald-700 rounded-xl text-white font-medium disabled:opacity-50 flex items-center justify-center gap-2 transition-colors"
            >
              <Share2 size={20} />
              分享
            </button>
          </div>

          {/* Loading State */}
          {isGenerating && (
            <div className="mt-4 flex items-center justify-center gap-2 text-blue-400 text-sm">
              <Loader2 size={16} className="animate-spin" />
              生成中...
            </div>
          )}
        </div>
      </div>

      {/* Hidden render container - 完全不可见 */}
      <div 
        ref={containerRef}
        className="fixed pointer-events-none"
        style={{ 
          top: '-10000px',
          left: '0',
          width: '400px',
          opacity: 1,
          zIndex: -1
        }}
      >
        {/* Current View Card */}
        <div data-share-card="current">
          {currentViewMode === ViewMode.ORIGINAL && <OriginalShareCard paper={paper} />}
          {currentViewMode === ViewMode.TRANSLATION && <TranslationShareCard paper={paper} />}
          {currentViewMode === ViewMode.AI_INSIGHT && <SimplifiedShareCard paper={paper} />}
          {currentViewMode === ViewMode.INFOGRAPHIC && infographicHtml && (
            <div dangerouslySetInnerHTML={{ __html: infographicHtml }} />
          )}
        </div>
      </div>
    </div>
  );
};

export default ShareModal;
