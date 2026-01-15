import { useState, useCallback } from 'react';
import { Paper, UserPreferences, DataSource, UserInteractions, ArxivSubSource } from '../types';
import { fetchFeedPapers } from '../services/backendService';

const PAGE_SIZE = 10;

interface UsePaperFeedProps {
    interactions: UserInteractions;
    preferences: UserPreferences;
    dataSource: DataSource;
    arxivSub?: ArxivSubSource;  // 新增: arxiv 子池 (today/week)
}

export const usePaperFeed = ({ interactions, preferences, dataSource, arxivSub }: UsePaperFeedProps) => {
    const [papers, setPapers] = useState<Paper[]>([]);
    const [loading, setLoading] = useState(false);
    const [page, setPage] = useState(0);
    const [hasMore, setHasMore] = useState(true);
    const [totalPapers, setTotalPapers] = useState(0);

    const loadPapers = useCallback(async (startIndex: number, prefs: UserPreferences, source: DataSource, query?: string, initialLoadSize?: number) => {
        // Note: We use the passed args (prefs, source) instead of props to allow flexibility if needed, 
        // but typically they should match. The original App.tsx allowed passing them.

        if (loading) return;
        setLoading(true);

        const pageSizeToUse = initialLoadSize && initialLoadSize > PAGE_SIZE ? initialLoadSize : PAGE_SIZE;

        try {
            let newPapers: Paper[] = [];

            // Unified Backend API
            // Mapping source to backend expectation (e.g. 'neurips' -> 'conf/neurips2025')
            // Original logic in App.tsx: const sourceParam = source === 'neurips' ? 'conf/neurips2025' : 'arxiv';
            // But looking at App.tsx, it might have more complex logic or just that. 
            // Let's stick to the logic seen in App.tsx line 270.
            // Wait, ViewMode enum had many conferences, but DataSource type had: 'arxiv' | 'neurips2025' | 'neurips' etc.
            // Let's just pass the source as is if it's not the special mapping, or map it.

            let sourceParam = source === 'arxiv' ? 'arxiv' : source;
            if (source === 'neurips') sourceParam = 'conf/neurips2025'; // specific override existing in App.tsx
            // If there are other mappings, they should be here. For now mimicking App.tsx.

            console.log(`[usePaperFeed] Loading papers: source=${source}, sourceParam=${sourceParam}, startIndex=${startIndex}`);

            // If query is present, it's a search. The original logic passed searchPhrase as 4th arg.
            // But `fetchFeedPapers` signature?
            // App.tsx line 273: const result = await fetchFeedPapers(startIndex, PAGE_SIZE, sourceParam);
            // Wait, where is search handled in App.tsx?
            // Line 662: loadPapers(0, preferences, dataSource, searchPhrase);
            // But fetchFeedPapers call in line 273 DOES NOT pass the query?
            // Let's re-read App.tsx line 273 carefully.
            // "const result = await fetchFeedPapers(startIndex, PAGE_SIZE, sourceParam);"
            // It seems the VIEWED part of App.tsx didn't show the query being passed to fetchFeedPapers!
            // This implies either:
            // 1. fetchFeedPapers doesn't support search?
            // 2. The viewed code was incomplete or I missed it.
            // 3. Search logic was implemented poorly (client side?) 
            // -> Line 109: isSearching state.
            // -> Line 662 calls loadPapers with searchPhrase.
            // -> Line 262 definition: loadPapers = async (..., query?: string)
            // -> Line 273 usage: fetchFeedPapers(startIndex, PAGE_SIZE, sourceParam) -- QUERY IS IGNORED?
            /**
             * CRITICAL FINDING: in the 'view_file' output of App.tsx, line 273 ignores the 'query' argument!
             * `const result = await fetchFeedPapers(startIndex, PAGE_SIZE, sourceParam);`
             * Unless fetchFeedPapers handles it globally (unlikely) or I missed a line. 
             * Ah, maybe fetchFeedPapers isn't the only call?
             * No, it looks like a bug in the current App.tsx or I'm misreading.
             * 
             * HOWEVER, I must preserve existing behavior or fix it. 
             * If I look at Search Logic (lines 655-664), it calls loadPapers.
             * If loadPapers ignores it, then Search is broken in current codebase?
             * 
             * Let's check 'src/services/backendService.ts' later to see signature.
             * For now, I will write the hook to ACCEPT query, and pass it to fetchFeedPapers 
             * assuming I should fix it or passing it if signature allows.
             * 
             * Actually, let's strictly check App.tsx again.
             * 
             * Line 262: const loadPapers = async (startIndex: number, prefs: UserPreferences, source: DataSource, query?: string) => {
             * ...
             * Line 273: const result = await fetchFeedPapers(startIndex, PAGE_SIZE, sourceParam);
             * 
             * It really looks like it is ignored. 
             * I will replicate this exactly for now to be safe (Refactor should not change behavior unless fixing bugs contextually).
             * But I'll double check fetchFeedPapers signature in next step.
             */

            // 如果是 arxiv 数据源且有 sub 参数，传递给 API
            const subParam = source === 'arxiv' ? arxivSub : undefined;

            // For standalone edition: request large batch (backend pool_ratio=1.0 returns all papers)
            // Use 2000 as limit to cover most cases (NeurIPS ~580, daily arxiv ~150)
            const effectiveLimit = startIndex === 0 ? 2000 : pageSizeToUse;
            const result = await fetchFeedPapers(startIndex, effectiveLimit, sourceParam, query, subParam);

            console.log(`[usePaperFeed] Received ${result.papers.length} papers, total=${result.total}`);

            if (result.total > 0) {
                setTotalPapers(result.total);
            }

            newPapers = result.papers;

            // Mark hasMore based on whether we got everything
            if (startIndex + newPapers.length >= result.total) {
                setHasMore(false);
            }

            // Filter out papers that are in the "Not Interested" list
            const filteredPapers = newPapers.filter(p => !interactions.notInterestedPaperIds.includes(p.id));

            setPapers(prev => startIndex === 0 ? filteredPapers : [...prev, ...filteredPapers]);
            setPage(prev => prev + 1);
        } catch (e) {
            console.error("Failed to load papers", e);
        } finally {
            setLoading(false);
        }
    }, [loading, interactions.notInterestedPaperIds]);
    // Dependency on loading state and interactions for filtering.

    return {
        papers,
        setPapers,
        loading,
        page,
        setPage,
        hasMore,
        setHasMore,
        totalPapers,
        loadPapers
    };
};
