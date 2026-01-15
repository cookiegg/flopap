import React from 'react';

const ViewTranslation: React.FC = () => {
    return (
        <div className="px-5 pb-32 animate-fade-in">
            <div className="bg-[#0f1115] border border-gray-800 rounded-lg p-5 mt-4">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-emerald-400 text-sm font-medium">中文翻译</h3>
                    <span className="text-[10px] bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded border border-emerald-500/20">Chinese</span>
                </div>
                <p className="text-gray-300 text-[15px] leading-7 tracking-wide text-justify">
                    主流的序列转导模型通常基于编码器-解码器配置中的复杂循环神经网络（RNN）或卷积神经网络（CNN）。表现最好的模型还通过注意力机制连接编码器和解码器。我们提出了一种新的简单网络架构——Transformer，它完全基于注意力机制，彻底摒弃了循环和卷积。
                    <br /><br />
                    在两个机器翻译任务上的实验表明，这些模型在质量上更优，同时更易于并行化，训练所需时间也显著减少。我们的模型在 WMT 2014 英德翻译任务上达到了 28.4 BLEU，比现有的最佳结果（包括集成模型）提高了超过 2 个 BLEU。
                    <br /><br />
                    在 WMT 2014 英法翻译任务中，我们的模型在 8 个 GPU 上训练 3.5 天后，建立了新的单模型最先进 BLEU 分数 41.8，这仅是文献中最佳模型训练成本的一小部分。我们还表明，Transformer 通过成功应用于具有大量和有限训练数据的英语成分句法分析，能够很好地泛化到其他任务。
                </p>
            </div>
        </div>
    );
};

export default ViewTranslation;
