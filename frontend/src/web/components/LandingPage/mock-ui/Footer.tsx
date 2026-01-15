import React from 'react';
import { EyeOff, Heart, Bookmark, Share2, User } from 'lucide-react';

const Footer: React.FC = () => {
    return (
        <div className="absolute bottom-0 left-0 right-0 bg-black/90 backdrop-blur-md border-t border-gray-800 pb-6 pt-3 px-6 z-50">
            <div className="flex justify-between items-center text-xs text-gray-400">

                <div className="flex flex-col items-center gap-1 cursor-pointer hover:text-white transition-colors">
                    <EyeOff size={22} strokeWidth={1.5} />
                    <span>不感兴趣</span>
                </div>

                <div className="flex flex-col items-center gap-1 cursor-pointer hover:text-white transition-colors">
                    <Heart size={22} strokeWidth={1.5} />
                    <span>点赞</span>
                </div>

                <div className="flex flex-col items-center gap-1 cursor-pointer text-white">
                    <Bookmark size={22} strokeWidth={2} fill="white" />
                    <span>收藏</span>
                </div>

                <div className="flex flex-col items-center gap-1 cursor-pointer hover:text-white transition-colors">
                    <Share2 size={22} strokeWidth={1.5} />
                    <span>分享</span>
                </div>

                <div className="flex flex-col items-center gap-1 cursor-pointer hover:text-white transition-colors">
                    <User size={22} strokeWidth={1.5} />
                    <span>个人主页</span>
                </div>

            </div>
        </div>
    );
};

export default Footer;
