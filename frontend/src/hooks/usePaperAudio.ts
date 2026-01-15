import { useState, useCallback, useEffect, useRef } from 'react';
import { Paper } from '../types';
import { ttsAudioService } from '../services/ttsAudioService';

export const usePaperAudio = ({ currentList, activeIndex, onNavigate }: {
    currentList: Paper[];
    activeIndex: number;
    onNavigate: (index: number, isAutoPlay?: boolean) => void;
}) => {
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [audioError, setAudioError] = useState<string | null>(null);
    const [autoPlayMode, setAutoPlayMode] = useState(true);
    const [isLoadingAudio, setIsLoadingAudio] = useState(false);
    const prevListLength = useRef(currentList.length);

    // 1. Sync Queue (Append Logic)
    useEffect(() => {
        if (currentList.length > prevListLength.current) {
            const newItems = currentList.slice(prevListLength.current);
            console.log(`[usePaperAudio] Appending ${newItems.length} items to AudioService`);
            ttsAudioService.appendQueue(newItems);
        } else if (currentList.length < prevListLength.current && currentList.length > 0) {
            // List refreshed?
            console.log(`[usePaperAudio] List reset/refresh detected`);
            // Ideally we don't reset queue unless user prompts, but if feed refreshes, maybe?
            // For now do nothing until user clicks play.
        }
        prevListLength.current = currentList.length;
    }, [currentList]);

    // 2. Listen to Service Events
    useEffect(() => {
        const unsubState = ttsAudioService.onPlaybackStateChanged((playing) => {
            setIsSpeaking(playing);
            setIsLoadingAudio(false); // If state changes, loading is done
        });

        const unsubTrack = ttsAudioService.onCurrentItemChanged((id) => {
            console.log(`[usePaperAudio] Current Item Changed: ${id}`);
            const index = currentList.findIndex(p => p.id === id);
            if (index !== -1 && index !== activeIndex) {
                console.log(`[usePaperAudio] Syncing UI to index ${index}`);
                onNavigate(index, true);
            }
        });

        return () => {
            unsubState();
            unsubTrack();
        };
    }, [currentList, activeIndex, onNavigate]);

    // 3. Auto Play Mode Sync
    useEffect(() => {
        ttsAudioService.setAutoPlay(autoPlayMode);
    }, [autoPlayMode]);

    // 4. Controls
    const startPlayback = useCallback(async (paper: Paper) => {
        try {
            console.log('Starting playback for:', paper.id);
            setAudioError(null);
            setIsLoadingAudio(true);

            // Ensure queue is set if we are starting fresh or random jump?
            // Actually play(id) in Service handles "not in native queue" by forcing setQueue.
            // But we should ensure the Service knows about the *current* list context.
            // Just in case we play item #0 which might trigger a reset.

            // Actually, best practice: If we are clicking a specific card, 
            // we want to ensure the queue matches "currentList" starting from this card (or full list).
            // But doing setQueue(currentList) every time is heavy.

            // Since we sync via useEffect append, Service *should* have the list.
            await ttsAudioService.play(paper.id);
            // State update comes via listener
        } catch (error) {
            console.error('Playback failed:', error);
            setAudioError('播放失败');
            setIsLoadingAudio(false);
        }
    }, [currentList]);

    const stopSpeech = useCallback(async () => {
        await ttsAudioService.pause(); // User intention is pause/stop
    }, []);

    const toggleSpeech = useCallback(async () => {
        if (isSpeaking) {
            await stopSpeech();
        } else {
            const paper = currentList[activeIndex];
            if (paper) {
                try {
                    // Set loading state immediately when user clicks play
                    setIsLoadingAudio(true);
                    setAudioError(null);

                    await ttsAudioService.setQueue(currentList, paper.id);
                    // State will be updated to playing via onPlaybackStateChanged listener
                } catch (error) {
                    console.error('Failed to start playback:', error);
                    setAudioError('播放失败');
                    setIsLoadingAudio(false);
                }
            }
        }
    }, [isSpeaking, currentList, activeIndex, stopSpeech]);

    return {
        isSpeaking,
        isLoadingAudio,
        audioError,
        autoPlayMode,
        setAutoPlayMode,
        startPlayback,
        stopSpeech,
        toggleSpeech,
        cleanMarkdownForTTS: (t: string) => t
    };
};
