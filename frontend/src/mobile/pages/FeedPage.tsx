import React from 'react';
import { usePaperFeed } from '../../hooks/usePaperFeed';
import { usePaperInteractions } from '../../hooks/usePaperInteractions';
import FeedScrollContainer from '../components/feed/FeedScrollContainer';
import { useUserStore } from '../../stores/useUserStore';
import { useInteractionStore } from '../../stores/useInteractionStore';
import { DataSource, ViewMode, AppLanguage, AppTheme, Paper } from '../../types';
import { ttsAudioService } from '../../services/ttsAudioService';

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

    const lastUserInteraction = React.useRef(0);

    const onScroll = () => {
        if (isAutoScrolling.current) return;
        if (!containerRef.current) return;

        const { scrollTop, clientHeight, scrollHeight } = containerRef.current;
        const index = Math.round(scrollTop / clientHeight);

        if (index !== activeIndex) {
            // Check if this is a result of recent user interaction
            const now = Date.now();
            if (now - lastUserInteraction.current < 4000) {
                console.log('Manual scroll detected: changing activeIndex to', index);
                setActiveIndex(index);

                // User Requirement: Stop audio on manual scroll
                ttsAudioService.pause();

            } else {
                console.log('Ignoring ghost scroll event (auto-scroll tail?)', index);
            }
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
            onTouchStart={() => {
                lastUserInteraction.current = Date.now();
                isAutoScrolling.current = false;
            }}
        />
    );
};

export default FeedPage;
