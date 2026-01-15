import React from 'react';
import { Home, ArrowLeft, EyeOff, Heart, Bookmark, Share2, UserCircle } from 'lucide-react';
import { UI_STRINGS } from '../../constants';
import { AppLanguage } from '../../types';

interface BottomBarProps {
    isDark: boolean;
    activeTab: 'feed' | 'profile';
    setActiveTab: (tab: 'feed' | 'profile') => void;
    language: AppLanguage;
    isLiked: boolean;
    isBookmarked: boolean;
    onHideClick: () => void;
    onToggleLike: () => void;
    onToggleBookmark: () => void;
    onShare: () => void;
}

const BottomBar: React.FC<BottomBarProps> = ({
    isDark,
    activeTab,
    setActiveTab,
    language,
    isLiked,
    isBookmarked,
    onHideClick,
    onToggleLike,
    onToggleBookmark,
    onShare
}) => {
    const ui = UI_STRINGS[language];

    // TODO: When integrating router, `setActiveTab` might be replaced by `navigate`.
    // For now keeping interface compatible with current App.tsx logic, or preparing for Router?
    // Let's keep it abstract enough.

    return (
        <div className={`min-h-[4rem] h-auto border-t flex items-center justify-around px-2 pb-[env(safe-area-inset-bottom)] z-30 shrink-0 ${isDark ? 'bg-black border-white/10' : 'bg-white border-gray-100 shadow-up'}`}>
            {activeTab === 'profile' ? (
                // Profile Navigation
                <>
                    <button
                        onClick={() => setActiveTab('feed')}
                        className={`flex flex-col items-center gap-1 px-6 py-2 rounded-xl transition-colors ${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}
                    >
                        <ArrowLeft size={22} />
                        <span className="text-[10px] font-bold">{ui.back}</span>
                    </button>
                    <button
                        onClick={() => setActiveTab('feed')}
                        className="flex flex-col items-center gap-1 px-6 py-2 rounded-xl text-blue-500 hover:text-blue-400 transition-colors"
                    >
                        <Home size={22} />
                        <span className="text-[10px] font-bold">{ui.home}</span>
                    </button>
                </>
            ) : (
                // Paper Actions (Like Feed) - Order: Hide -> Like -> Save -> Share -> Me
                <>
                    <button onClick={onHideClick} className="flex flex-col items-center gap-1 p-2 text-gray-400 hover:text-red-400 transition-colors active:scale-90">
                        <EyeOff size={22} />
                        <span className="text-[10px] font-medium">{ui.hide}</span>
                    </button>

                    <button onClick={onToggleLike} className={`flex flex-col items-center gap-1 p-2 transition-transform active:scale-90 ${isLiked ? 'text-red-500' : 'text-gray-400'}`}>
                        <Heart size={22} fill={isLiked ? "currentColor" : "none"} />
                        <span className="text-[10px] font-medium">{ui.like}</span>
                    </button>

                    <button onClick={onToggleBookmark} className={`flex flex-col items-center gap-1 p-2 transition-transform active:scale-90 ${isBookmarked ? 'text-yellow-400' : 'text-gray-400'}`}>
                        <Bookmark size={22} fill={isBookmarked ? "currentColor" : "none"} />
                        <span className="text-[10px] font-medium">{ui.save}</span>
                    </button>

                    <button onClick={onShare} className={`flex flex-col items-center gap-1 p-2 transition-colors active:scale-90 ${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-400 hover:text-gray-900'}`}>
                        <Share2 size={22} />
                        <span className="text-[10px] font-medium">{ui.share}</span>
                    </button>

                    <button onClick={() => setActiveTab('profile')} className={`flex flex-col items-center gap-1 p-2 transition-colors active:scale-90 ${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-400 hover:text-gray-900'}`}>
                        <UserCircle size={22} />
                        <span className="text-[10px] font-medium">{ui.profile}</span>
                    </button>
                </>
            )}
        </div>
    );
};

export default BottomBar;
