import { useState, useCallback } from 'react';
import { Paper, UserInteractions } from '../types';
import { submitFeedback } from '../services/backendService';
import { ttsAudioService } from '../services/ttsAudioService';

interface ViewingCollectionState {
    active: boolean;
    papers: Paper[];
    startIndex: number;
}

interface UsePaperInteractionsProps {
    papers: Paper[];
    setPapers: React.Dispatch<React.SetStateAction<Paper[]>>;
    viewingCollection: ViewingCollectionState;
    setViewingCollection: React.Dispatch<React.SetStateAction<ViewingCollectionState>>;
    interactions: UserInteractions;
    setInteractions: React.Dispatch<React.SetStateAction<UserInteractions>>;
    activeIndex: number;
    setActiveIndex: (index: number) => void;
}

export const usePaperInteractions = ({
    papers, setPapers,
    viewingCollection, setViewingCollection,
    interactions, setInteractions,
    activeIndex, setActiveIndex
}: UsePaperInteractionsProps) => {

    const [showHideConfirm, setShowHideConfirm] = useState(false);

    const getCurrentPaperId = () => {
        const list = viewingCollection.active ? viewingCollection.papers : papers;
        if (!list[activeIndex]) return null;
        return list[activeIndex].id;
    };

    const getCurrentPaper = () => {
        const list = viewingCollection.active ? viewingCollection.papers : papers;
        return list[activeIndex];
    };

    const toggleLike = useCallback(() => {
        const currentId = getCurrentPaperId();
        if (!currentId) return;

        const currentPaper = getCurrentPaper();
        const wasLiked = currentPaper?.liked || false;

        setInteractions(prev => {
            const exists = prev.likedPaperIds.includes(currentId);
            const newLiked = exists
                ? prev.likedPaperIds.filter(id => id !== currentId)
                : [...prev.likedPaperIds, currentId];

            submitFeedback(currentId, 'like', !exists).catch(console.error);

            return {
                ...prev,
                likedPaperIds: newLiked
            };
        });

        if (viewingCollection.active && wasLiked) {
            setViewingCollection(prev => {
                const newPapers = prev.papers.filter(p => p.id !== currentId);
                if (activeIndex >= newPapers.length) {
                    setActiveIndex(Math.max(0, newPapers.length - 1));
                }
                return {
                    ...prev,
                    papers: newPapers
                };
            });
        } else {
            setPapers(prev => prev.map(p =>
                p.id === currentId ? { ...p, liked: !p.liked } : p
            ));

            if (viewingCollection.active) {
                setViewingCollection(prev => ({
                    ...prev,
                    papers: prev.papers.map(p =>
                        p.id === currentId ? { ...p, liked: !p.liked } : p
                    )
                }));
            }
        }
    }, [activeIndex, papers, viewingCollection, setActiveIndex, setInteractions, setPapers, setViewingCollection]);

    const toggleBookmark = useCallback(() => {
        const currentId = getCurrentPaperId();
        if (!currentId) return;

        const currentPaper = getCurrentPaper();
        const wasBookmarked = currentPaper?.bookmarked || false;

        setInteractions(prev => {
            const exists = prev.bookmarkedPaperIds.includes(currentId);
            const newBookmarked = exists
                ? prev.bookmarkedPaperIds.filter(id => id !== currentId)
                : [...prev.bookmarkedPaperIds, currentId];

            submitFeedback(currentId, 'bookmark', !exists).catch(console.error);

            return {
                ...prev,
                bookmarkedPaperIds: newBookmarked
            };
        });

        if (viewingCollection.active && wasBookmarked) {
            setViewingCollection(prev => {
                const newPapers = prev.papers.filter(p => p.id !== currentId);
                if (activeIndex >= newPapers.length) {
                    setActiveIndex(Math.max(0, newPapers.length - 1));
                }
                return {
                    ...prev,
                    papers: newPapers
                };
            });
        } else {
            setPapers(prev => prev.map(p =>
                p.id === currentId ? { ...p, bookmarked: !p.bookmarked } : p
            ));

            if (viewingCollection.active) {
                setViewingCollection(prev => ({
                    ...prev,
                    papers: prev.papers.map(p =>
                        p.id === currentId ? { ...p, bookmarked: !p.bookmarked } : p
                    )
                }));
            }
        }
    }, [activeIndex, papers, viewingCollection, setActiveIndex, setInteractions, setPapers, setViewingCollection]);

    const confirmHide = useCallback(() => {
        setShowHideConfirm(false);
        const currentId = getCurrentPaperId();
        if (!currentId) return;

        submitFeedback(currentId, 'dislike', true, true).catch(console.error);

        // Sync with Native Playlist
        ttsAudioService.removeItem(currentId);

        setInteractions(prev => ({
            ...prev,
            notInterestedPaperIds: [...prev.notInterestedPaperIds, currentId]
        }));

        if (viewingCollection.active) {
            setViewingCollection(prev => ({
                ...prev,
                papers: prev.papers.filter(p => p.id !== currentId)
            }));
        } else {
            setPapers(prev => {
                const newPapers = prev.filter(p => p.id !== currentId);
                if (activeIndex >= newPapers.length) {
                    setActiveIndex(Math.max(0, newPapers.length - 1));
                }
                return newPapers;
            });
        }
    }, [activeIndex, papers, viewingCollection, setActiveIndex, setInteractions, setPapers, setViewingCollection]);

    return {
        toggleLike,
        toggleBookmark,
        handleHideClick: () => setShowHideConfirm(true),
        confirmHide,
        showHideConfirm,
        setShowHideConfirm
    };
};
