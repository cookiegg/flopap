import React from 'react';
import { Sparkles, Brain, Zap, Target } from 'lucide-react';

const ViewAnalysis: React.FC = () => {
    return (
        <div className="px-5 pb-32 animate-fade-in">

            <div className="flex items-center gap-2 mt-6 mb-4">
                <Sparkles size={16} className="text-purple-400" />
                <span className="text-white font-medium">AI 深度解读</span>
            </div>

            <div className="space-y-6">
                {/* Core Innovation */}
                <div className="bg-[#15151a] p-4 rounded-xl border border-gray-800/50">
                    <div className="flex items-center gap-2 mb-3">
                        <Brain size={16} className="text-pink-400" />
                        <h3 className="text-pink-400 font-medium text-[15px]">核心创新：Self-Attention</h3>
                    </div>
                    <p className="text-gray-300 text-[14px] leading-6 text-justify">
                        本文提出了 <strong>Transformer</strong> 架构，这是第一个完全抛弃 RNN 和 CNN 递归结构的序列转换模型。它完全依赖于 <strong>自注意力机制 (Self-Attention)</strong> 来计算输入和输出的表示。这一范式转变解决了长距离依赖问题，并允许极高程度的并行计算。
                    </p>
                </div>

                {/* Efficiency */}
                <div className="bg-[#15151a] p-4 rounded-xl border border-gray-800/50">
                    <div className="flex items-center gap-2 mb-3">
                        <Zap size={16} className="text-yellow-400" />
                        <h3 className="text-yellow-400 font-medium text-[15px]">效率突破</h3>
                    </div>
                    <p className="text-gray-300 text-[14px] leading-6 text-justify">
                        相比于 LSTM 和 GRU 需要按时间步顺序计算，Transformer 允许对整个序列进行并行处理。实验表明，在 8 个 P100 GPU 上仅需 3.5 天即可达到 SOTA 效果，而之前的最佳模型需要数周的计算时间。计算成本大幅降低。
                    </p>
                </div>

                {/* Impact */}
                <div className="bg-[#15151a] p-4 rounded-xl border border-gray-800/50">
                    <div className="flex items-center gap-2 mb-3">
                        <Target size={16} className="text-cyan-400" />
                        <h3 className="text-cyan-400 font-medium text-[15px]">深远影响</h3>
                    </div>
                    <p className="text-gray-300 text-[14px] leading-6 text-justify">
                        该论文是现代大语言模型（如 BERT, GPT 系列）的奠基之作。其提出的 "Multi-Head Attention" 和 "Positional Encoding" 等技术已成为自然语言处理领域的标准组件，彻底改变了 NLP 的发展轨迹。
                    </p>
                </div>
            </div>
        </div>
    );
};

export default ViewAnalysis;
