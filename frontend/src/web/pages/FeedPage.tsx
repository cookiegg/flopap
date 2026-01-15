import React from 'react';
import { usePaperFeed } from '../../hooks/usePaperFeed';
import { usePaperInteractions } from '../../hooks/usePaperInteractions';
import FeedScrollContainer from '../components/FeedScrollContainer';
import { useUserStore } from '../../stores/useUserStore';
import { useInteractionStore } from '../../stores/useInteractionStore';
import { DataSource, ViewMode, AppLanguage, AppTheme, Paper } from '../../types';

interface FeedPageProps {
    dataSource: DataSource;
    viewMode: ViewMode;
    language: AppLanguage;
    theme: AppTheme;
    isSearching: boolean;
    searchPhrase: string;
    onClearSearch: () => void;
    activeIndex: number;
    setActiveIndex: (index: number) => void;
    containerRef: React.RefObject<HTMLDivElement>;
    isAutoScrolling: React.MutableRefObject<boolean>;

    // Interactions passed from parent or internal?
    // Ideally, FeedPage manages its own feed state via hooks.
    // But common state like activeIndex is shared with Audio Player (TopBar in Layout).
    // So many props might still be needed if Audio Player remains global in Layout.

    // Passing these so Layout can control them (e.g. for Audio Player)
    papers: Paper[];
    setPapers: React.Dispatch<React.SetStateAction<Paper[]>>;
    loading: boolean;
    hasMore: boolean;
    loadPapers: (startIndex: number, prefs: any, source: any, query?: string) => Promise<void>;

    // New prop
    totalPapers: number;

    // Viewing collection mode?
    viewingCollection: { active: boolean; papers: Paper[]; startIndex: number };
    setViewingCollection: React.Dispatch<React.SetStateAction<{ active: boolean; papers: Paper[]; startIndex: number }>>;

    onSwipeView: (direction: 'left' | 'right') => void;
    onInfographicHtmlChange: (html: string) => void;
}

const FeedPage: React.FC<FeedPageProps> = ({
    dataSource,
    viewMode,
    language,
    theme,
    isSearching,
    searchPhrase,
    onClearSearch,
    activeIndex,
    setActiveIndex,
    containerRef,
    isAutoScrolling,
    papers,
    setPapers,
    loading,
    hasMore,
    loadPapers,
    totalPapers, // Destructure
    viewingCollection,
    setViewingCollection,
    onSwipeView,
    onInfographicHtmlChange
}) => {
    const interactions = useInteractionStore();
    const preferences = useUserStore((state) => state.preferences);

    // Interaction Logic Hook
    // We need to pass papers and setPapers to it.
    const {
        toggleLike,
        toggleBookmark,
        handleHideClick,
        // confirmHide, showHideConfirm, setShowHideConfirm -- These are modals handled in Layout usually? 
        // OR we handle them here but the Modal is in Layout?
        // Let's pass the interaction handlers.
        // Wait, confirmHide checks specific paper interaction.
    } = usePaperInteractions({
        papers,
        setPapers,
        // If we are viewing collection, interactions might differ slightly (remove from list?)
        viewingCollection,
        setViewingCollection,
        interactions, // passed full store object which matches interface?
        setInteractions: (valOrUpdater) => {
            // Zustand store expects value, but hook might pass updater function
            const current = interactions;
            const newVal = typeof valOrUpdater === 'function'
                ? (valOrUpdater as (prev: any) => any)(current)
                : valOrUpdater;
            interactions.setInteractions(newVal);
        },
        activeIndex,
        setActiveIndex
    });

    const onScroll = () => {
        if (isAutoScrolling.current) return;
        if (!containerRef.current) return;

        const { scrollTop, clientHeight, scrollHeight } = containerRef.current;
        const index = Math.round(scrollTop / clientHeight);

        if (index !== activeIndex) {
            console.log('Manual scroll detected: changing activeIndex from', activeIndex, 'to', index);
            setActiveIndex(index);
            // STOP SPEECH is handled in App/Layout typically or via a global event?
            // Ideally, the global Audio hook should listen to activeIndex changes or we call a callback.
            // We'll leave that side effect to the parent for now via setActiveIndex.
        }

        if (!viewingCollection.active && hasMore && !loading && (scrollHeight - scrollTop - clientHeight < clientHeight * 2)) {
            loadPapers(papers.length, preferences, dataSource, isSearching ? searchPhrase : undefined);
        }
    };

    const currentList = viewingCollection.active ? viewingCollection.papers : papers;

    return (
        <FeedScrollContainer
            papers={currentList}
            loading={loading}
            hasMore={hasMore}
            activeIndex={activeIndex}
            setActiveIndex={setActiveIndex}
            viewMode={viewMode}
            language={language}
            theme={theme}
            totalPapers={viewingCollection.active ? viewingCollection.papers.length : totalPapers}
            isSearching={isSearching}
            onLoadMore={() => { }}
            onClearSearch={onClearSearch}
            onUpdatePaper={(p) => setPapers(prev => prev.map(item => item.id === p.id ? p : item))}
            onToggleLike={toggleLike}
            onToggleBookmark={toggleBookmark}
            onNotInterested={handleHideClick}
            onSwipeView={onSwipeView}
            onInfographicHtmlChange={onInfographicHtmlChange}
            containerRef={containerRef}
            isAutoScrolling={isAutoScrolling}
            onScroll={onScroll}
        />
    );
};

export default FeedPage;
