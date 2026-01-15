import React from 'react';
import { Paper, ViewMode, AppLanguage, AppTheme } from '../../types';
import PaperCard from './PaperCard';
import { UI_STRINGS } from '../../constants';

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
    onScroll
}) => {
    const ui = UI_STRINGS[language];
    const isDark = theme === 'dark';

    // Get the currently active paper
    const activePaper = papers[activeIndex];

    return (
        <div
            ref={containerRef}
            className="w-full h-full overflow-hidden no-scrollbar md:pr-36"
        >
            {papers.length === 0 && !loading && (
                <div className="h-full flex flex-col items-center justify-center text-gray-500">
                    <p>{ui.noPapers}</p>
                    {isSearching && <button onClick={onClearSearch} className="mt-4 text-blue-400">Clear Search</button>}
                </div>
            )}

            {/* Render only the active paper card for keyboard-only navigation */}
            {activePaper && (
                <PaperCard
                    key={activePaper.id}
                    paper={activePaper}
                    viewMode={viewMode}
                    isActive={true}
                    isLiked={activePaper.liked || false}
                    isBookmarked={activePaper.bookmarked || false}
                    onUpdatePaper={onUpdatePaper}
                    onToggleLike={() => onToggleLike(activePaper)}
                    onToggleBookmark={() => onToggleBookmark(activePaper)}
                    onNotInterested={() => onNotInterested(activePaper)}
                    language={language}
                    onSwipe={onSwipeView}
                    theme={theme}
                    onInfographicHtmlChange={onInfographicHtmlChange}
                    index={activeIndex + 1}
                    total={totalPapers}
                />
            )}

            {loading && (
                <div className={`w-full h-full flex items-center justify-center ${isDark ? 'bg-black' : 'bg-white'}`}>
                    <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
                </div>
            )}
        </div>
    );
};

export default FeedScrollContainer;
