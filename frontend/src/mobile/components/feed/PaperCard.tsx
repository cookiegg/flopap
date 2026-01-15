import React, { useRef, useState } from 'react';
import { Paper, ViewMode, AppLanguage, AppTheme } from '../../../types';
import { Heart, Loader2 } from 'lucide-react';
import { UI_STRINGS } from '../../../constants';
import PaperCardHeader from './parts/PaperCardHeader';
import PaperCardInfographic from './parts/PaperCardInfographic';
import PaperCardVisualization from './parts/PaperCardVisualization';
import PaperCardTextContent from './parts/PaperCardTextContent';

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
  const ui = UI_STRINGS[language];
  const isDark = theme === 'dark';

  // Double Tap & Swipe State
  const lastTapRef = useRef<number>(0);
  const [showBigHeart, setShowBigHeart] = useState(false);
  const touchStartRef = useRef<{ x: number, y: number } | null>(null);

  const bgSeed = paper.id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  const hue = bgSeed % 360;

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

  const handleDoubleTap = (e: React.MouseEvent) => {
    const now = Date.now();
    if (now - lastTapRef.current < 300) {
      if (!isLiked) onToggleLike();
      setShowBigHeart(true);
      setTimeout(() => setShowBigHeart(false), 1000);
    }
    lastTapRef.current = now;
  };


  const renderBodyContent = () => {
    if (viewMode === ViewMode.INFOGRAPHIC) {
      return (
        <PaperCardInfographic
          paper={paper}
          language={language}
          theme={theme}
          isActive={isActive}
          onUpdatePaper={onUpdatePaper}
          onInfographicHtmlChange={onInfographicHtmlChange}
          onSwipe={onSwipe}
        />
      );
    }

    if (viewMode === ViewMode.VISUALIZATION) {
      return (
        <PaperCardVisualization
          paper={paper}
          language={language}
          theme={theme}
          onUpdatePaper={onUpdatePaper}
        />
      );
    }

    return (
      <PaperCardTextContent
        paper={paper}
        language={language}
        theme={theme}
        viewMode={viewMode}
      />
    );
  };

  return (
    <div className={`snap-start w-full h-full relative flex flex-col overflow-hidden shrink-0 ${isDark ? 'bg-gray-900' : 'bg-white'}`} onTouchStart={handleTouchStart} onTouchEnd={handleTouchEnd}>
      <div className="absolute inset-0 opacity-20 pointer-events-none transition-colors duration-1000" style={{ background: `radial-gradient(circle at 80% 20%, hsl(${hue}, 70%, 20%), ${isDark ? '#000000' : '#ffffff'})` }} />
      <div className={`absolute inset-0 pointer-events-none z-0 ${isDark ? 'bg-gradient-to-b from-black/80 via-black/50 to-black' : 'bg-gradient-to-b from-white/90 via-white/60 to-white'}`} />

      {showBigHeart && (
        <div className="absolute inset-0 z-50 flex items-center justify-center pointer-events-none animate-bounce">
          <Heart className="w-32 h-32 text-red-500 fill-current drop-shadow-2xl animate-pulse" />
        </div>
      )}

      <div className="relative z-10 w-full h-full flex flex-col" onClick={handleDoubleTap}>
        <PaperCardHeader
          paper={paper}
          viewMode={viewMode}
          language={language}
          theme={theme}
        />

        <div className="flex-1 overflow-y-auto overscroll-auto no-scrollbar scroll-smooth relative" onTouchStart={handleTouchStart} onTouchEnd={handleTouchEnd}>
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
