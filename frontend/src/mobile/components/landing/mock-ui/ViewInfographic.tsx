import React from 'react';
import { TrendingUp, Clock, Award } from 'lucide-react';

const ViewInfographic: React.FC = () => {
    const data = [
        { name: 'GNMT', score: 24.6, color: 'bg-gray-700' },
        { name: 'ConvS2S', score: 25.2, color: 'bg-gray-600' },
        { name: 'MoE', score: 26.0, color: 'bg-gray-500' },
        { name: 'Transformer Base', score: 27.3, color: 'bg-blue-500' },
        { name: 'Transformer Big', score: 28.4, color: 'bg-indigo-500' },
    ];

    const maxScore = 30;

    return (
        <div className="px-5 pb-32 animate-fade-in">
            <div className="mt-6 mb-4 flex items-center gap-2">
                <TrendingUp size={18} className="text-pink-400" />
                <div>
                    <h3 className="text-white font-bold text-lg leading-none">关键指标可视化</h3>
                    <p className="text-gray-400 text-[10px] mt-1">Key Performance Metrics</p>
                </div>
            </div>

            {/* Chart Card */}
            <div className="bg-[#13141b] p-5 rounded-xl border border-gray-800/60 shadow-lg relative overflow-hidden">
                <div className="absolute top-0 right-0 w-20 h-20 bg-blue-500/5 rounded-full blur-2xl"></div>

                <h4 className="text-gray-300 text-xs font-semibold mb-4 flex items-center gap-2">
                    <Award size={12} className="text-yellow-500" />
                    BLEU Score (English-to-German)
                </h4>

                <div className="space-y-4">
                    {data.map((item) => (
                        <div key={item.name} className="relative group">
                            <div className="flex justify-between text-[11px] mb-1.5">
                                <span className="text-gray-400 font-medium group-hover:text-gray-200 transition-colors">{item.name}</span>
                                <span className="text-white font-mono">{item.score}</span>
                            </div>
                            <div className="w-full h-2 bg-gray-800/50 rounded-full overflow-hidden">
                                <div
                                    className={`h-full rounded-full ${item.color} shadow-[0_0_10px_rgba(0,0,0,0.3)]`}
                                    style={{ width: `${(item.score / maxScore) * 100}%` }}
                                ></div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Training Cost Visualization */}
            <div className="mt-6">
                <h4 className="text-gray-300 text-xs font-semibold mb-3 flex items-center gap-2">
                    <Clock size={12} className="text-green-400" />
                    Training Efficiency (FLOPs)
                </h4>

                <div className="grid grid-cols-2 gap-3">
                    <div className="bg-[#1e1e24] p-3 rounded-lg border border-gray-800 relative overflow-hidden group hover:border-red-500/30 transition-colors">
                        <div className="text-[10px] text-gray-500 mb-1">ConvS2S (Prev Best)</div>
                        <div className="text-lg font-bold text-red-400 font-mono">1.5e20</div>
                        <div className="text-[9px] text-gray-600 mt-1">High Cost</div>
                    </div>

                    <div className="bg-[#1e1e24] p-3 rounded-lg border border-gray-800 relative overflow-hidden group hover:border-green-500/30 transition-colors">
                        <div className="absolute inset-0 bg-green-500/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                        <div className="text-[10px] text-gray-500 mb-1">Transformer Base</div>
                        <div className="text-lg font-bold text-green-400 font-mono">2.5e19</div>
                        <div className="text-[9px] text-green-500/70 mt-1 flex items-center gap-1">
                            <span>▼ 83%</span> Cost
                        </div>
                    </div>
                </div>
            </div>

        </div>
    );
};

export default ViewInfographic;
