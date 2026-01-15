import React from 'react';
import { Bot, Maximize2, Download } from 'lucide-react';
import demoVisualization from '../../../../assets/demo-visualization.jpeg';

const ViewVisualization: React.FC = () => {
    return (
        <div className="px-5 pb-32 animate-fade-in">
            <div className="mt-4 mb-2 flex justify-between items-end">
                <div>
                    <h3 className="text-white font-bold text-lg">AI 论文讲解图</h3>
                    <p className="text-gray-400 text-xs">Visualization Map</p>
                </div>
                <div className="flex gap-2">
                    <button className="p-1.5 rounded-full bg-gray-800 text-gray-400 hover:text-white transition-colors">
                        <Download size={16} />
                    </button>
                    <Bot size={20} className="text-orange-400 mb-1" />
                </div>
            </div>

            {/* Image Container */}
            <div className="relative w-full bg-[#1a1b26] rounded-xl overflow-hidden border border-gray-800 mt-4 group">
                <img
                    src={demoVisualization}
                    alt="Attention Is All You Need Visualization"
                    className="w-full h-auto object-contain"
                />

                {/* Overlay Gradient */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent pointer-events-none"></div>

                {/* Caption Overlay */}
                <div className="absolute bottom-0 left-0 right-0 p-4">
                    <span className="inline-block px-2 py-1 bg-orange-500/20 text-orange-400 text-[10px] font-bold rounded mb-1 border border-orange-500/30">
                        AI MAP
                    </span>
                    <p className="text-white text-sm font-medium leading-tight">
                        Attention Is All You Need
                    </p>
                </div>

                {/* Zoom Button */}
                <button className="absolute top-3 right-3 p-2 bg-black/50 hover:bg-black/70 rounded-full text-white backdrop-blur-sm transition-colors opacity-0 group-hover:opacity-100">
                    <Maximize2 size={16} />
                </button>
            </div>

            <div className="mt-4 p-4 bg-[#1e1e24] rounded-lg border border-gray-800">
                <div className="flex gap-3">
                    <div className="min-w-[3px] bg-orange-500 rounded-full"></div>
                    <p className="text-gray-400 text-xs italic leading-5">
                        "这张图直观地展示了 Transformer 的完整架构，包括多头注意力机制、前馈网络以及位置编码在编码器和解码器中的流动过程。"
                    </p>
                </div>
            </div>

        </div>
    );
};

export default ViewVisualization;
