import React, { useState, useEffect } from 'react';
import {
    Menu,
    Search,
    FileText,
    Languages,
    Sparkles,
    BarChart2,
    Image as ImageIcon,
    Globe
} from 'lucide-react';
import { ViewMode } from './mock-ui/types';
import Footer from './mock-ui/Footer';
import ViewOriginal from './mock-ui/ViewOriginal';
import ViewTranslation from './mock-ui/ViewTranslation';
import ViewAnalysis from './mock-ui/ViewAnalysis';
import ViewInfographic from './mock-ui/ViewInfographic';
import ViewVisualization from './mock-ui/ViewVisualization';

const MockAppUI: React.FC = () => {
    const [currentView, setCurrentView] = useState<ViewMode>(ViewMode.VISUALIZATION);
    const [isHovering, setIsHovering] = useState(false);

    // Auto-cycle logic
    useEffect(() => {
        let interval: NodeJS.Timeout;

        if (!isHovering) {
            interval = setInterval(() => {
                setCurrentView(prev => {
                    const views = [
                        ViewMode.VISUALIZATION,
                        ViewMode.ORIGINAL,
                        ViewMode.TRANSLATION,
                        ViewMode.ANALYSIS,
                        ViewMode.INFOGRAPHIC,
                    ];
                    const currentIndex = views.indexOf(prev);
                    const nextIndex = (currentIndex + 1) % views.length;
                    return views[nextIndex];
                });
            }, 3000); // Switch every 3 seconds
        }

        return () => clearInterval(interval);
    }, [isHovering]);

    const getToolbarIconColor = (view: ViewMode) => {
        if (view === currentView) {
            switch (view) {
                case ViewMode.ORIGINAL: return 'text-blue-400';
                case ViewMode.TRANSLATION: return 'text-emerald-400';
                case ViewMode.ANALYSIS: return 'text-purple-400';
                case ViewMode.INFOGRAPHIC: return 'text-pink-400';
                case ViewMode.VISUALIZATION: return 'text-orange-400';
                default: return 'text-white';
            }
        }
        return 'text-gray-500 hover:text-gray-300';
    };

    const renderContent = () => {
        switch (currentView) {
            case ViewMode.ORIGINAL:
                return <ViewOriginal />;
            case ViewMode.TRANSLATION:
                return <ViewTranslation />;
            case ViewMode.ANALYSIS:
                return <ViewAnalysis />;
            case ViewMode.INFOGRAPHIC:
                return <ViewInfographic />;
            case ViewMode.VISUALIZATION:
                return <ViewVisualization />;
            default:
                return <ViewOriginal />;
        }
    };

    return (
        <div
            className="h-full bg-[#050505] text-white flex flex-col relative overflow-hidden"
            onMouseEnter={() => setIsHovering(true)}
            onMouseLeave={() => setIsHovering(false)}
        >

            {/* Top Header Fixed */}
            <div className="sticky top-0 z-40 bg-[#050505]/95 backdrop-blur-md pt-2 pb-2">

                {/* Row 1: Menu - Toolbar - Search */}
                <div className="flex items-center justify-between px-4 mb-3">
                    <button className="p-2 text-gray-400 hover:text-white">
                        <Menu size={20} />
                    </button>

                    {/* Pill Toolbar - 5 Icons for 5 Views */}
                    <div className="bg-[#1a1d24] rounded-full px-4 py-1.5 flex items-center justify-between gap-3 shadow-lg border border-gray-800/50 scale-90 sm:scale-100">
                        <button
                            onClick={() => setCurrentView(ViewMode.ORIGINAL)}
                            className={`transition-colors duration-200 transform ${currentView === ViewMode.ORIGINAL ? 'scale-110' : ''} ${getToolbarIconColor(ViewMode.ORIGINAL)}`}
                            title="Original"
                        >
                            <FileText size={16} strokeWidth={currentView === ViewMode.ORIGINAL ? 2.5 : 2} />
                        </button>

                        <button
                            onClick={() => setCurrentView(ViewMode.TRANSLATION)}
                            className={`transition-colors duration-200 transform ${currentView === ViewMode.TRANSLATION ? 'scale-110' : ''} ${getToolbarIconColor(ViewMode.TRANSLATION)}`}
                            title="Translation"
                        >
                            <Languages size={18} strokeWidth={currentView === ViewMode.TRANSLATION ? 2.5 : 2} />
                        </button>

                        <button
                            onClick={() => setCurrentView(ViewMode.ANALYSIS)}
                            className={`transition-colors duration-200 transform ${currentView === ViewMode.ANALYSIS ? 'scale-110' : ''} ${getToolbarIconColor(ViewMode.ANALYSIS)}`}
                            title="AI Analysis"
                        >
                            <Sparkles size={16} strokeWidth={currentView === ViewMode.ANALYSIS ? 2.5 : 2} />
                        </button>

                        <button
                            onClick={() => setCurrentView(ViewMode.INFOGRAPHIC)}
                            className={`transition-colors duration-200 transform ${currentView === ViewMode.INFOGRAPHIC ? 'scale-110' : ''} ${getToolbarIconColor(ViewMode.INFOGRAPHIC)}`}
                            title="Infographic"
                        >
                            <BarChart2 size={16} strokeWidth={currentView === ViewMode.INFOGRAPHIC ? 2.5 : 2} />
                        </button>

                        <button
                            onClick={() => setCurrentView(ViewMode.VISUALIZATION)}
                            className={`transition-colors duration-200 transform ${currentView === ViewMode.VISUALIZATION ? 'scale-110' : ''} ${getToolbarIconColor(ViewMode.VISUALIZATION)}`}
                            title="Visualization"
                        >
                            <ImageIcon size={16} strokeWidth={currentView === ViewMode.VISUALIZATION ? 2.5 : 2} />
                        </button>
                    </div>

                    <button className="p-2 text-gray-400 hover:text-white">
                        <Search size={20} />
                    </button>
                </div>

            </div>

            {/* Main Scrollable Content */}
            <div className="flex-1 overflow-y-auto no-scrollbar pb-16">

                {/* Title Section (Common) */}
                <div className="px-5 pt-2">
                    {/* Tags Line */}
                    <div className="flex items-center justify-between text-xs mb-3">
                        <span className="bg-[#111f35] text-[#3b82f6] px-2 py-1 rounded-md font-medium border border-[#1e3a8a]/50">
                            neurips.cs.LG
                        </span>
                        <div className="flex items-center gap-2 text-gray-500">
                            <Globe size={12} />
                            <span className="font-mono text-[10px]">Google Brain</span>
                        </div>
                    </div>

                    {/* Main Title */}
                    <h1 className="text-[20px] font-bold leading-snug mb-2 tracking-tight text-white">
                        Attention Is All You Need
                    </h1>

                    {/* Subtitle / Chinese Title */}
                    <h2 className="text-gray-400 text-xs leading-relaxed mb-3">
                        只需要注意力机制：一种基于注意力机制的全新简单网络架构 Transformer
                    </h2>

                    {/* Authors */}
                    <p className="text-gray-500 text-[10px] mb-4 truncate">
                        Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit...
                    </p>

                    <div className="w-full h-[1px] bg-gray-800 mb-2"></div>
                </div>

                {/* Dynamic View Content */}
                {renderContent()}

            </div>

            <Footer />
        </div>
    );
};

export default MockAppUI;
