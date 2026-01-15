import React from 'react';
import { Home, ArrowLeft, EyeOff, Heart, Bookmark, Share2, UserCircle } from 'lucide-react';
import { UI_STRINGS } from '../../constants';
import { AppLanguage, Paper } from '../../types';

interface RightToolbarProps {
    isDark: boolean;
    language: AppLanguage;
    isLiked: boolean;
    isBookmarked: boolean;
    onHideClick: () => void;
    onToggleLike: () => void;
    onToggleBookmark: () => void;
    onShare: () => void;
    currentPaper?: Paper;
}

const RightToolbar: React.FC<RightToolbarProps> = ({
    isDark,
    language,
    isLiked,
    isBookmarked,
    onHideClick,
    onToggleLike,
    onToggleBookmark,
    onShare,
    currentPaper
}) => {
    const ui = UI_STRINGS[language];

    if (!currentPaper) return null;

    return (
        <div className={`hidden md:flex flex-col gap-4 p-4 rounded-xl fixed right-6 top-1/2 -translate-y-1/2 z-30 ${isDark ? 'bg-black border border-gray-800' : 'bg-white border border-gray-200 shadow-xl'}`}>
            <button
                onClick={onToggleLike}
                className={`flex flex-col items-center gap-1 p-3 rounded-lg transition-all hover:scale-105 ${isLiked ? 'text-red-500 bg-red-500/10' : isDark ? 'text-gray-400 hover:bg-gray-800' : 'text-gray-400 hover:bg-gray-100'}`}
                title={ui.like}
            >
                <Heart size={24} fill={isLiked ? "currentColor" : "none"} />
            </button>

            <button
                onClick={onToggleBookmark}
                className={`flex flex-col items-center gap-1 p-3 rounded-lg transition-all hover:scale-105 ${isBookmarked ? 'text-yellow-400 bg-yellow-400/10' : isDark ? 'text-gray-400 hover:bg-gray-800' : 'text-gray-400 hover:bg-gray-100'}`}
                title={ui.save}
            >
                <Bookmark size={24} fill={isBookmarked ? "currentColor" : "none"} />
            </button>

            <button
                onClick={onShare}
                className={`flex flex-col items-center gap-1 p-3 rounded-lg transition-all hover:scale-105 ${isDark ? 'text-gray-400 hover:bg-gray-800' : 'text-gray-600 hover:bg-gray-100'}`}
                title={ui.share}
            >
                <Share2 size={24} />
            </button>

            <div className={`h-px w-full my-1 ${isDark ? 'bg-gray-800' : 'bg-gray-200'}`} />

            <button
                onClick={onHideClick}
                className={`flex flex-col items-center gap-1 p-3 rounded-lg transition-all hover:scale-105 text-gray-400 hover:text-red-400 hover:bg-red-500/10`}
                title={ui.hide}
            >
                <EyeOff size={24} />
            </button>
        </div>
    );
};

export default RightToolbar;
