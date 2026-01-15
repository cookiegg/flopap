import React, { useRef, useEffect } from 'react';
import { Paper, ViewMode, AppLanguage, AppTheme } from '../../../types';
import PaperCard from './PaperCard';
import PaperCardSkeleton from './PaperCardSkeleton';
import { UI_STRINGS } from '../../../constants';

interface FeedScrollContainerProps {
    papers: Paper[];
    loading: boolean;
    hasMore: boolean;
    activeIndex: number;
    setActiveIndex: (index: number) => void;
    viewMode: ViewMode;
    language: AppLanguage;
    theme: AppTheme;
    totalPapers: number;
    isSearching: boolean;

    // Actions passed down or from stores?
    // We can pass them as props to keep this component "dumb" regarding logic source,
    // or connect it to stores directly. Let's keep it semi-smart but use callbacks for specific item actions to allow reuse (e.g. in Profile view) if needed.
    // Actually, App.tsx used 'usePaperInteractions' hook.

    onLoadMore: () => void;
    onClearSearch: () => void;
    onUpdatePaper: (paper: Paper) => void;
    onToggleLike: (paper: Paper) => void;
    onToggleBookmark: (paper: Paper) => void;
    onNotInterested: (paper: Paper) => void;
    onSwipeView: (direction: 'left' | 'right') => void;
    onInfographicHtmlChange: (html: string) => void;

    // Refs
    containerRef: React.RefObject<HTMLDivElement>;
    isAutoScrolling: React.MutableRefObject<boolean>;
    onScroll: () => void;
    onTouchStart?: () => void;
}

const FeedScrollContainer: React.FC<FeedScrollContainerProps> = ({
    papers,
    loading,
    hasMore,
    activeIndex,
    viewMode,
    language,
    theme,
    totalPapers,
    isSearching,
    onLoadMore,
    onClearSearch,
    onUpdatePaper,
    onToggleLike,
    onToggleBookmark,
    onNotInterested,
    onSwipeView,
    onInfographicHtmlChange,
    containerRef,
    onScroll,
    onTouchStart
}) => {
    const ui = UI_STRINGS[language];
    const isDark = theme === 'dark';

    return (
        <div
            ref={containerRef}
            className="w-full h-full overflow-y-scroll snap-y snap-mandatory no-scrollbar"
            onScroll={onScroll}
            onTouchStart={onTouchStart}
        >
            {/* Initial Loading or Pagination Loading */}
            {loading && (
                <div className="snap-start w-full h-full flex items-center justify-center">
                    <PaperCardSkeleton theme={theme} />
                </div>
            )}

            {papers.length === 0 && !loading && (
                <div className="h-full flex flex-col items-center justify-center text-gray-500">
                    <p>{ui.noPapers}</p>
                    {isSearching && <button onClick={onClearSearch} className="mt-4 text-blue-400">Clear Search</button>}
                </div>
            )}

            {papers.map((paper, index) => (
                <PaperCard
                    key={paper.id}
                    paper={paper}
                    viewMode={viewMode}
                    isActive={index === activeIndex}
                    isLiked={paper.liked || false}
                    isBookmarked={paper.bookmarked || false}
                    onUpdatePaper={onUpdatePaper}
                    onToggleLike={() => onToggleLike(paper)}
                    onToggleBookmark={() => onToggleBookmark(paper)}
                    onNotInterested={() => onNotInterested(paper)}
                    language={language}
                    onSwipe={onSwipeView}
                    theme={theme}
                    onInfographicHtmlChange={onInfographicHtmlChange}
                    index={index + 1}
                    total={totalPapers}
                />
            ))}
        </div>
    );
};

export default FeedScrollContainer;
