import { create } from 'zustand';
import { UserInteractions } from '../types';
import * as StorageService from '../services/storageService';
import { getUserInteractions, submitFeedback } from '../services/backendService';

interface InteractionState extends UserInteractions {
    // Actions
    setInteractions: (interactions: UserInteractions) => void;
    fetchInteractions: () => Promise<void>;
    toggleLike: (paperId: string) => void;
    toggleBookmark: (paperId: string) => void;
    addNotInterested: (paperId: string) => void;
}

export const useInteractionStore = create<InteractionState>((set, get) => ({
    likedPaperIds: [],
    bookmarkedPaperIds: [],
    notInterestedPaperIds: [],

    setInteractions: (interactions) => set(interactions),

    fetchInteractions: async () => {
        const token = localStorage.getItem('token');
        let inters: UserInteractions;

        if (token) {
            inters = await getUserInteractions();
            await StorageService.saveInteractions(inters);
        } else {
            inters = await StorageService.getInteractions();
        }
        set(inters);
    },

    toggleLike: (paperId: string) => set((state) => {
        const isLiked = state.likedPaperIds.includes(paperId);
        const newLiked = isLiked
            ? state.likedPaperIds.filter(id => id !== paperId)
            : [...state.likedPaperIds, paperId];

        // Call backend API
        submitFeedback(paperId, 'like', !isLiked).catch(console.error);

        const newState = { ...state, likedPaperIds: newLiked };
        // Sanitize: only save data
        StorageService.saveInteractions({
            likedPaperIds: newState.likedPaperIds,
            bookmarkedPaperIds: newState.bookmarkedPaperIds,
            notInterestedPaperIds: newState.notInterestedPaperIds
        });
        return newState;
    }),

    toggleBookmark: (paperId: string) => set((state) => {
        const isBookmarked = state.bookmarkedPaperIds.includes(paperId);
        const newBookmarked = isBookmarked
            ? state.bookmarkedPaperIds.filter(id => id !== paperId)
            : [...state.bookmarkedPaperIds, paperId];

        // Call backend API
        submitFeedback(paperId, 'bookmark', !isBookmarked).catch(console.error);

        const newState = { ...state, bookmarkedPaperIds: newBookmarked };
        // Sanitize: only save data
        StorageService.saveInteractions({
            likedPaperIds: newState.likedPaperIds,
            bookmarkedPaperIds: newState.bookmarkedPaperIds,
            notInterestedPaperIds: newState.notInterestedPaperIds
        });
        return newState;
    }),

    addNotInterested: (paperId: string) => set((state) => {
        if (state.notInterestedPaperIds.includes(paperId)) return state;
        const newNotInterested = [...state.notInterestedPaperIds, paperId];

        // Call backend API
        submitFeedback(paperId, 'dislike', true, true).catch(console.error);

        const newState = { ...state, notInterestedPaperIds: newNotInterested };
        // Sanitize: only save data
        StorageService.saveInteractions({
            likedPaperIds: newState.likedPaperIds,
            bookmarkedPaperIds: newState.bookmarkedPaperIds,
            notInterestedPaperIds: newState.notInterestedPaperIds
        });
        return newState;
    })
}));

