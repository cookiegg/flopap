import { registerPlugin, PluginListenerHandle } from '@capacitor/core';

export interface AudioItem {
    id: string;
    url: string;
    title?: string;
    artist?: string;
    artwork?: string;
}

export interface PaperAudioPlugin {
    setPlaylist(options: { items: AudioItem[], startId?: string }): Promise<void>;
    appendItems(options: { items: AudioItem[] }): Promise<void>;
    playId(options: { id: string }): Promise<void>;
    removeItem(options: { id: string }): Promise<void>;
    pause(): Promise<void>;
    resume(): Promise<void>;
    seek(options: { time: number }): Promise<void>;
    setAutoPlay(options: { autoPlay: boolean }): Promise<void>;
    getCurrentState(): Promise<{ id: string | null; isPlaying: boolean }>;

    // Listeners
    addListener(eventName: 'onCurrentItemChanged', listenerFunc: (data: { id: string }) => void): Promise<PluginListenerHandle>;
    addListener(eventName: 'onPlaybackStateChanged', listenerFunc: (data: { isPlaying: boolean }) => void): Promise<PluginListenerHandle>;
}

const PaperAudio = registerPlugin<PaperAudioPlugin>('PaperAudio');

export default PaperAudio;
