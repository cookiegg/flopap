import { Capacitor } from '@capacitor/core';
import { getApiBaseUrl } from './backendService';
import { Paper } from '../types';
import PaperAudio, { AudioItem } from '../mobile/plugins/PaperAudio';

class TTSAudioService {
  private queue: Paper[] = [];
  private resolvedCount = 0;
  private isAutoPlay = true;
  private currentId: string | null = null;
  private urlCache = new Map<string, string>();
  private resolvingPromises = new Map<string, Promise<string>>();

  // Web Audio Fallback
  private webAudio: HTMLAudioElement | null = null;

  // Listeners
  private onCurrentItemChangedCallbacks: Set<(id: string) => void> = new Set();
  private onPlaybackStateChangedCallbacks: Set<(isPlaying: boolean) => void> = new Set();
  private onProgressCallbacks: Set<(position: number, duration: number) => void> = new Set(); // Added for completeness

  constructor() {
    this.setupListeners();
  }

  private async setupListeners() {
    if (Capacitor.isNativePlatform()) {
      PaperAudio.addListener('onCurrentItemChanged', (data) => {
        console.log(`[TTS] Track changed to: ${data.id}`);
        this.currentId = data.id;
        this.notifyCurrentItemChanged(data.id);
        this.checkAndBufferMore();
      });

      PaperAudio.addListener('onPlaybackStateChanged', (data) => {
        this.notifyPlaybackStateChanged(data.isPlaying);
      });
    } else {
      // Web Initialization
      this.webAudio = new Audio();

      this.webAudio.addEventListener('ended', () => {
        console.log('[TTS-Web] Audio ended');
        if (this.isAutoPlay) {
          this.playNextWeb();
        } else {
          this.notifyPlaybackStateChanged(false);
        }
      });

      this.webAudio.addEventListener('play', () => this.notifyPlaybackStateChanged(true));
      this.webAudio.addEventListener('pause', () => this.notifyPlaybackStateChanged(false));
      this.webAudio.addEventListener('error', (e) => {
        console.error('[TTS-Web] Audio error:', e);
        this.notifyPlaybackStateChanged(false);
      });
      this.webAudio.addEventListener('timeupdate', () => {
        // Optional: notify progress
      });
    }
  }

  // --- Public API ---

  async setQueue(papers: Paper[], startId?: string) {
    this.queue = papers;
    this.resolvedCount = 0;

    // Determine start index
    let startIndex = 0;
    if (startId) {
      startIndex = this.queue.findIndex(p => p.id === startId);
      if (startIndex === -1) startIndex = 0;
    }

    console.log(`[TTS] Setting queue with ${papers.length} items, starting at ${startIndex}`);

    if (Capacitor.isNativePlatform()) {
      // ... Original Native Logic ...
      const effectiveQueue = this.queue.slice(startIndex);
      this.queue = effectiveQueue;

      const initialBatchSize = Math.min(this.queue.length, 100);
      console.log(`[TTS] Preloading ${initialBatchSize} items (queue size: ${this.queue.length})`);
      const initialBatch = await this.resolveBatch(0, initialBatchSize);

      await PaperAudio.setPlaylist({
        items: initialBatch,
        startId: startId
      });

      this.resolvedCount = initialBatch.length;
      this.currentId = startId || (initialBatch[0]?.id) || null;
      this.checkAndBufferMore();

    } else {
      // ... Web Logic ...
      this.queue = papers.slice(startIndex); // Keep simple slicing logic same as native for now
      this.currentId = startId || (this.queue[0]?.id) || null;

      if (this.currentId) {
        await this.playWeb(this.currentId);
      }
    }
  }

  async appendQueue(newPapers: Paper[]) {
    this.queue.push(...newPapers);
    console.log(`[TTS] Appended ${newPapers.length} papers. Total: ${this.queue.length}`);
    if (Capacitor.isNativePlatform()) {
      this.checkAndBufferMore();
    }
  }

  async play(paperId: string) {
    if (Capacitor.isNativePlatform()) {
      const indexInQueue = this.queue.findIndex(p => p.id === paperId);
      if (indexInQueue === -1) {
        console.warn(`[TTS] play(${paperId}) called but item not in queue.`);
        return;
      }

      if (indexInQueue < this.resolvedCount) {
        await PaperAudio.playId({ id: paperId });
      } else {
        const newQueue = this.queue;
        await this.setQueue(newQueue, paperId);
      }
    } else {
      // Web Play
      await this.playWeb(paperId);
    }
  }

  async pause() {
    if (Capacitor.isNativePlatform()) {
      await PaperAudio.pause();
    } else {
      this.webAudio?.pause();
    }
  }

  async resume() {
    if (Capacitor.isNativePlatform()) {
      await PaperAudio.resume();
    } else {
      this.webAudio?.play();
    }
  }

  async removeItem(id: string) {
    this.queue = this.queue.filter(p => p.id !== id);
    if (Capacitor.isNativePlatform()) {
      await PaperAudio.removeItem({ id });
    }
    this.urlCache.delete(id);
  }

  async setAutoPlay(auto: boolean) {
    this.isAutoPlay = auto;
    if (Capacitor.isNativePlatform()) {
      await PaperAudio.setAutoPlay({ autoPlay: auto });
    }
  }

  // --- Internal Logic (Web) ---

  private async playWeb(paperId: string) {
    if (!this.webAudio) return;

    try {
      // Verify paper is in queue
      const paper = this.queue.find(p => p.id === paperId);
      if (!paper) {
        console.warn(`[TTS-Web] Paper ${paperId} not in queue`);
        return;
      }

      const url = await this.getTTSAudioUrl(paperId);
      // Convert relative API URL to absolute if needed (usually browser handles relative to host)
      // But getTTSAudioUrl returns /api/v1/..., browser is fine.

      this.currentId = paperId;
      this.notifyCurrentItemChanged(paperId);

      // Force reload src
      this.webAudio.src = url;
      this.webAudio.load();

      try {
        await this.webAudio.play();
      } catch (e) {
        console.warn("[TTS-Web] Auto-play prevented or failed", e);
        this.notifyPlaybackStateChanged(false);
      }

    } catch (e) {
      console.error(`[TTS-Web] Failed to play ${paperId}`, e);
      this.notifyPlaybackStateChanged(false);
      // Auto skip?
      if (this.isAutoPlay) {
        setTimeout(() => this.playNextWeb(), 1000);
      }
    }
  }

  private playNextWeb() {
    if (!this.currentId) return;
    const idx = this.queue.findIndex(p => p.id === this.currentId);
    if (idx !== -1 && idx < this.queue.length - 1) {
      const nextPaper = this.queue[idx + 1];
      this.playWeb(nextPaper.id);
    } else {
      console.log("[TTS-Web] End of queue");
      this.notifyPlaybackStateChanged(false);
    }
  }

  // --- Internal Logic (Native) ---

  private async checkAndBufferMore() {
    if (!Capacitor.isNativePlatform()) return;

    // If we are close to the end of resolved items, buffer more.
    if (!this.currentId) return;

    const currentIndex = this.queue.findIndex(p => p.id === this.currentId);
    if (currentIndex === -1) return;

    // Aggressive buffering for background playback support
    // Since JS pauses in background, we need to ensure we have enough content 
    // queued up in Native layer (PaperAudioService) to last a while.
    const bufferThreshold = 5; // Buffer if within 5 items of end

    if (this.resolvedCount - currentIndex <= bufferThreshold) {
      if (this.resolvedCount < this.queue.length) {
        console.log(`[TTS] Buffering more items (Aggressive)...`);

        // Load a large batch (30 items) to survive background JS pause
        const nextBatchSize = 30;
        const newItems = await this.resolveBatch(this.resolvedCount, nextBatchSize);
        if (newItems.length > 0) {
          await PaperAudio.appendItems({ items: newItems });
          this.resolvedCount += newItems.length;

          // Recursively continue buffering while we can (JS is in foreground)
          // This ensures we preload as much as possible before background pause
          this.checkAndBufferMore();
        }
      }
    }
  }

  private async resolveBatch(startIndex: number, count: number): Promise<AudioItem[]> {
    const papers = this.queue.slice(startIndex, startIndex + count);
    const items: AudioItem[] = [];

    // Resolve in parallel
    await Promise.all(papers.map(async (p) => {
      try {
        const url = await this.getTTSAudioUrl(p.id);
        items.push({
          id: p.id,
          url: url,
          title: p.title,
          artist: 'Flopap', // Can be dynamic
          artwork: p.infographicUrl || '' // Pass artwork
        });
      } catch (e) {
        console.warn(`[TTS] Failed to resolve audio for ${p.id}`, e);
        // Skip item? Or push placeholder? Skip for now.
      }
    }));

    // Maintain order
    const orderedItems: AudioItem[] = [];
    for (const p of papers) {
      const found = items.find(i => i.id === p.id);
      if (found) orderedItems.push(found);
    }

    return orderedItems;
  }

  private async getTTSAudioUrl(paperId: string): Promise<string> {
    if (this.urlCache.has(paperId)) return this.urlCache.get(paperId)!;
    if (this.resolvingPromises.has(paperId)) return this.resolvingPromises.get(paperId)!;

    const promise = this.getTTSAudioUrlWithRetry(paperId, 3);
    this.resolvingPromises.set(paperId, promise);
    return promise;
  }

  private async getTTSAudioUrlWithRetry(paperId: string, maxRetries: number): Promise<string> {
    let lastError: Error | null = null;

    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        const baseUrl = getApiBaseUrl();
        const response = await fetch(`${baseUrl}/v1/tts/audio/${paperId}`);

        // Specific handling for 404: audio not generated yet
        if (response.status === 404) {
          this.resolvingPromises.delete(paperId);
          throw new Error(`AUDIO_NOT_GENERATED:${paperId}`);
        }

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        const fullUrl = `${baseUrl}${data.audio_url}`; // Ensure absolute URL for web if needed
        // Note: data.audio_url from API is usually relative like /api/v1/tts/file/...
        // If on web, relative (starting with /) is fine. 
        // If on mobile, we need absolute.

        // Let's normalize it
        let finalUrl = data.audio_url;
        if (!finalUrl.startsWith('http')) {
          // If relative, prepend API base if not on same origin?
          // Actually, getApiBaseUrl() usually gives http://localhost:8000 (native) or /api (web proxy)
          // If web proxy, /api/v1/... is good.
          // But if running standalone web, we likely use relative.
          if (Capacitor.isNativePlatform()) {
            finalUrl = `${baseUrl.replace('/api', '')}${finalUrl}`;
          }
          // For web, simple relative path is best
        }

        this.urlCache.set(paperId, finalUrl);
        this.resolvingPromises.delete(paperId);
        return finalUrl;
      } catch (error) {
        lastError = error as Error;
        console.warn(`[TTS] Attempt ${attempt + 1}/${maxRetries} failed for ${paperId}:`, error);

        if (attempt < maxRetries - 1) {
          // Exponential backoff: 1s, 2s, 4s
          const delay = 1000 * Math.pow(2, attempt);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }

    this.resolvingPromises.delete(paperId);
    throw lastError || new Error(`Failed to get TTS URL for ${paperId}`);
  }

  // --- Events ---

  onCurrentItemChanged(callback: (id: string) => void) {
    this.onCurrentItemChangedCallbacks.add(callback);
    return () => this.onCurrentItemChangedCallbacks.delete(callback);
  }

  onPlaybackStateChanged(callback: (isPlaying: boolean) => void) {
    this.onPlaybackStateChangedCallbacks.add(callback);
    return () => this.onPlaybackStateChangedCallbacks.delete(callback);
  }

  private notifyCurrentItemChanged(id: string) {
    this.onCurrentItemChangedCallbacks.forEach(cb => cb(id));
  }

  private notifyPlaybackStateChanged(isPlaying: boolean) {
    this.onPlaybackStateChangedCallbacks.forEach(cb => cb(isPlaying));
  }
}

export const ttsAudioService = new TTSAudioService();
