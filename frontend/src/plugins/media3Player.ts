import { registerPlugin } from '@capacitor/core';

export interface Media3PlayerPlugin {
  playAudio(options: { url: string; title?: string; artist?: string }): Promise<void>;
  pause(): Promise<void>;
  stop(): Promise<void>;
  isPlaying(): Promise<{ isPlaying: boolean }>;
  addListener(eventName: string, listenerFunc: () => void): Promise<void>;
}

const Media3Player = registerPlugin<Media3PlayerPlugin>('Media3Player');

export default Media3Player;
