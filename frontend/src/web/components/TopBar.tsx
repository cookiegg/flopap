import React, { useState } from 'react';
import { Menu, Search, Play, Square, FileText, Sparkles, Languages, Image as ImageIcon, BarChart3, ArrowLeft, EyeOff, Music, Repeat, Loader2 } from 'lucide-react';
import { ViewMode } from '../../types';

interface TopBarProps {
    isDark: boolean;
    sidebarOpen: boolean;
    setSidebarOpen: (open: boolean) => void;
    activeTab: 'feed' | 'profile';
    viewMode: ViewMode;
    setViewMode: (mode: ViewMode) => void;
    isSpeaking: boolean;
    isLoadingAudio?: boolean;
    audioError: string | null;
    toggleSpeech: () => void;
    autoPlayMode: boolean;
    setAutoPlayMode: (auto: boolean) => void;
    onSearchOpen: () => void;
    viewingCollection: boolean;
    onBackFromCollection: () => void;
    isSearching: boolean;
    searchPhrase: string;
    onClearSearch: () => void;
}

const TopBar: React.FC<TopBarProps> = ({
    isDark,
    setSidebarOpen,
    activeTab,
    viewMode,
    setViewMode,
    isSpeaking,
    isLoadingAudio = false,
    audioError,
    toggleSpeech,
    autoPlayMode,
    setAutoPlayMode,
    onSearchOpen,
    viewingCollection,
    onBackFromCollection,
    isSearching,
    searchPhrase,
    onClearSearch
}) => {
    const [showAudioMenu, setShowAudioMenu] = useState(false);

    const handleAudioButtonClick = () => {
        if (isSpeaking) {
            // If playing, stop
            toggleSpeech();
        } else {
            // If not playing, show dropdown
            setShowAudioMenu(!showAudioMenu);
        }
    };

    return (
        <>
            <div className={`absolute top-0 left-0 right-0 z-30 pt-[calc(0.75rem+env(safe-area-inset-top))] px-4 pb-3 flex items-center justify-between pointer-events-none ${isDark ? 'bg-gradient-to-b from-black/90 to-transparent' : 'bg-gradient-to-b from-white/90 to-transparent'}`}>

                {/* Left: Menu/Back */}
                <div className="pointer-events-auto">
                    {viewingCollection ? (
                        <button onClick={onBackFromCollection} className={`p-2 rounded-full backdrop-blur-md border ${isDark ? 'bg-black/40 text-white border-white/10' : 'bg-white/40 text-gray-900 border-black/10'}`}>
                            <ArrowLeft size={20} />
                        </button>
                    ) : (
                        <button onClick={() => setSidebarOpen(true)} className={`md:hidden p-2 rounded-full transition-colors ${isDark ? 'text-white/80 hover:bg-white/10' : 'text-black/80 hover:bg-black/5'}`}>
                            <Menu size={24} />
                        </button>
                    )}
                </div>

                {/* Center: View Toggles & TTS (Only in Feed) */}
                {activeTab === 'feed' && (
                    <div className={`pointer-events-auto flex items-center gap-1 backdrop-blur-xl rounded-full p-1 border shadow-lg ${isDark ? 'bg-black/40 border-white/10' : 'bg-white/60 border-black/5'}`}>
                        <button
                            onClick={() => setViewMode(ViewMode.ORIGINAL)}
                            className={`p-2 rounded-full transition-all ${viewMode === ViewMode.ORIGINAL ? (isDark ? 'bg-white/20 text-white' : 'bg-black/10 text-black') : 'text-gray-400'}`}
                        >
                            <FileText size={18} />
                        </button>
                        <button
                            onClick={() => setViewMode(ViewMode.TRANSLATION)}
                            className={`p-2 rounded-full transition-all ${viewMode === ViewMode.TRANSLATION ? 'bg-blue-500/20 text-blue-500' : 'text-gray-400'}`}
                        >
                            <Languages size={18} />
                        </button>
                        <button
                            onClick={() => setViewMode(ViewMode.AI_INSIGHT)}
                            className={`p-2 rounded-full transition-all ${viewMode === ViewMode.AI_INSIGHT ? 'bg-purple-500/20 text-purple-500' : 'text-gray-400'}`}
                        >
                            <Sparkles size={18} />
                        </button>
                        <button
                            onClick={() => setViewMode(ViewMode.INFOGRAPHIC)}
                            className={`p-2 rounded-full transition-all ${viewMode === ViewMode.INFOGRAPHIC ? 'bg-emerald-500/20 text-emerald-500' : 'text-gray-400'}`}
                        >
                            <BarChart3 size={18} />
                        </button>
                        <button
                            onClick={() => setViewMode(ViewMode.VISUALIZATION)}
                            className={`p-2 rounded-full transition-all ${viewMode === ViewMode.VISUALIZATION ? 'bg-orange-500/20 text-orange-500' : 'text-gray-400'}`}
                        >
                            <ImageIcon size={18} />
                        </button>
                        <div className={`w-px h-4 mx-1 ${isDark ? 'bg-white/20' : 'bg-black/10'}`}></div>

                        {/* Audio Button with Dropdown */}
                        <div className="relative">
                            <button
                                onClick={handleAudioButtonClick}
                                className={`p-2 rounded-full transition-all ${isSpeaking
                                    ? 'bg-green-500/20 text-green-500 animate-pulse'
                                    : isLoadingAudio
                                        ? 'bg-yellow-500/20 text-yellow-500'
                                        : audioError
                                            ? 'bg-red-500/20 text-red-500'
                                            : 'text-gray-400 hover:text-green-500'
                                    }`}
                                title={audioError || (isSpeaking ? '停止播放' : '选择播放模式')}
                            >
                                {isLoadingAudio ? (
                                    <Loader2 size={18} className="animate-spin" />
                                ) : isSpeaking ? (
                                    <Square size={14} fill="currentColor" />
                                ) : (
                                    <Play size={18} />
                                )}
                            </button>

                            {/* Dropdown Menu */}
                            {showAudioMenu && !isSpeaking && (
                                <div className={`absolute top-full mt-2 right-0 w-40 rounded-xl backdrop-blur-xl border shadow-2xl p-1 overflow-hidden z-50 ${isDark ? 'bg-zinc-900/95 border-white/10 text-white' : 'bg-white/95 border-black/10 text-black'}`}>
                                    <div className={`px-3 py-2 text-[10px] uppercase font-bold tracking-wider opacity-50 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                                        Select Mode
                                    </div>
                                    <button
                                        onClick={() => {
                                            setAutoPlayMode(false);
                                            toggleSpeech();
                                            setShowAudioMenu(false);
                                        }}
                                        className={`w-full px-3 py-3 text-sm flex items-center gap-3 rounded-lg transition-colors ${isDark ? 'hover:bg-white/10' : 'hover:bg-black/5'}`}
                                    >
                                        <div className="p-1.5 rounded-md bg-blue-500/20 text-blue-500">
                                            <Music size={16} />
                                        </div>
                                        <span>Single Play</span>
                                    </button>
                                    <button
                                        onClick={() => {
                                            setAutoPlayMode(true);
                                            toggleSpeech();
                                            setShowAudioMenu(false);
                                        }}
                                        className={`w-full px-3 py-3 text-sm flex items-center gap-3 rounded-lg transition-colors ${isDark ? 'hover:bg-white/10' : 'hover:bg-black/5'}`}
                                    >
                                        <div className="p-1.5 rounded-md bg-green-500/20 text-green-500">
                                            <Repeat size={16} />
                                        </div>
                                        <span>Auto Play</span>
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Right: Search Only */}
                <div className="pointer-events-auto flex gap-3">
                    {activeTab === 'feed' && (
                        <button onClick={onSearchOpen} className={`p-2 rounded-full transition-colors ${isDark ? 'text-white/80 hover:bg-white/10' : 'text-black/80 hover:bg-black/5'}`}>
                            <Search size={24} />
                        </button>
                    )}
                </div>
            </div>

            {/* HEADER: Search Context */}
            {isSearching && activeTab === 'feed' && (
                <div className="absolute top-16 left-0 right-0 z-20 flex justify-center pointer-events-none">
                    <div className="bg-blue-600/90 backdrop-blur text-white px-4 py-1 rounded-full text-xs font-bold flex items-center gap-2 pointer-events-auto shadow-lg">
                        <span>Search: "{searchPhrase}"</span>
                        <button onClick={onClearSearch}><EyeOff size={12} /></button>
                    </div>
                </div>
            )}

            {/* HEADER: Viewing Collection Context */}
            {viewingCollection && (
                <div className="absolute top-16 left-0 right-0 z-20 flex justify-center pointer-events-none">
                    <div className="bg-purple-600/90 backdrop-blur text-white px-4 py-1 rounded-full text-xs font-bold shadow-lg">
                        Viewing Collection
                    </div>
                </div>
            )}
        </>
    );
};

export default TopBar;
