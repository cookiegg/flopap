import React, { useState, useCallback } from 'react';
import { Play, Square } from 'lucide-react';
import { ttsAudioService } from '../../services/ttsAudioService';
import { Paper } from '../../types';

interface TTSPlayerProps {
  paper: Paper | null;
  isDark: boolean;
  onPlayStart?: () => void;
  onPlayEnd?: () => void;
  onError?: (error: string) => void;
}

const TTSPlayer: React.FC<TTSPlayerProps> = ({
  paper,
  isDark,
  onPlayStart,
  onPlayEnd,
  onError
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentAudio, setCurrentAudio] = useState<HTMLAudioElement | null>(null);
  const [error, setError] = useState<string | null>(null);

  const stopPlayback = useCallback(() => {
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.currentTime = 0;
      currentAudio.onended = null;
      currentAudio.onerror = null;
      setCurrentAudio(null);
    }
    setIsPlaying(false);
    setError(null);
    onPlayEnd?.();
  }, [currentAudio, onPlayEnd]);

  const startPlayback = useCallback(async () => {
    if (!paper) return;

    try {
      setError(null);
      setIsPlaying(true);
      onPlayStart?.();

      // 停止之前的播放
      if (currentAudio) {
        currentAudio.pause();
        currentAudio.onended = null;
        currentAudio.onerror = null;
      }

      await ttsAudioService.play(paper.id);
      setIsPlaying(true);
      // Note: Native audio doesn't return HTMLAudioElement
      // We'll handle events through the native plugin callbacks

    } catch (error) {
      const errorMsg = '播放失败';
      setError(errorMsg);
      setIsPlaying(false);
      setCurrentAudio(null);
      onError?.(errorMsg);
    }
  }, [paper.id, currentAudio, onPlayStart, onPlayEnd, onError]);

  const togglePlayback = useCallback(() => {
    if (!paper) return;

    if (isPlaying) {
      stopPlayback();
    } else {
      startPlayback();
    }
  }, [paper, isPlaying, stopPlayback, startPlayback]);

  return (
    <button
      onClick={togglePlayback}
      disabled={!paper}
      className={`p-2 rounded-full transition-all ${!paper
          ? 'text-gray-300 cursor-not-allowed'
          : isPlaying
            ? 'bg-green-500/20 text-green-500 animate-pulse'
            : error
              ? 'bg-red-500/20 text-red-500'
              : 'text-gray-400 hover:text-green-500'
        }`}
      title={!paper ? '无论文' : error || (isPlaying ? '停止播放' : '播放AI解读')}
    >
      {isPlaying ? <Square size={14} fill="currentColor" /> : <Play size={18} />}
    </button>
  );
};

export default TTSPlayer;
