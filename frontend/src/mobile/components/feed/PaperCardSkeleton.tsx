import React from 'react';
import { AppTheme } from '../../../types';

interface PaperCardSkeletonProps {
    theme: AppTheme;
}

const PaperCardSkeleton: React.FC<PaperCardSkeletonProps> = ({ theme }) => {
    const isDark = theme === 'dark';
    const bgBase = isDark ? 'bg-gray-800' : 'bg-gray-200';
    const bgHighlight = isDark ? 'bg-gray-700' : 'bg-gray-300';

    return (
        <div className={`snap-start w-full h-full relative flex flex-col shrink-0 overflow-hidden ${isDark ? 'bg-gray-900' : 'bg-white'}`}>
            {/* Header Skeleton */}
            <div className="pt-24 px-6 pb-4 shrink-0 animate-pulse">
                {/* Categories */}
                <div className="flex gap-2 mb-3">
                    <div className={`h-4 w-16 rounded-full ${bgBase}`}></div>
                    <div className={`h-4 w-12 rounded-full ${bgBase}`}></div>
                </div>

                {/* Title */}
                <div className={`h-8 w-3/4 rounded mb-2 ${bgHighlight}`}></div>
                <div className={`h-6 w-1/2 rounded mb-4 ${bgBase}`}></div>

                {/* Author */}
                <div className={`h-3 w-1/3 rounded ${bgBase}`}></div>

                <div className={`w-full h-px mt-4 ${isDark ? 'bg-white/5' : 'bg-gray-100'}`} />
            </div>

            {/* Body Skeleton */}
            <div className="flex-1 px-6 pt-4 animate-pulse">
                <div className={`h-4 w-full rounded mb-3 ${bgBase}`}></div>
                <div className={`h-4 w-full rounded mb-3 ${bgBase}`}></div>
                <div className={`h-4 w-5/6 rounded mb-3 ${bgBase}`}></div>
                <div className={`h-4 w-full rounded mb-3 ${bgBase}`}></div>
                <div className={`h-4 w-4/5 rounded mb-3 ${bgBase}`}></div>
                <div className={`h-4 w-11/12 rounded mb-3 ${bgBase}`}></div>
            </div>

            {/* Index Counter Skeleton */}
            <div className="pb-4 flex justify-center animate-pulse">
                <div className={`h-4 w-12 rounded ${bgBase}`}></div>
            </div>
        </div>
    );
};

export default PaperCardSkeleton;
