import React from 'react';

const ViewOriginal: React.FC = () => {
    return (
        <div className="px-5 pb-32 animate-fade-in">
            <div className="bg-[#0f1115] border border-gray-800 rounded-lg p-5 mt-4">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-blue-400 text-sm font-medium">Original Abstract</h3>
                    <span className="text-[10px] bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded border border-blue-500/20">English</span>
                </div>
                <p className="text-gray-300 text-[15px] leading-7 tracking-wide text-justify font-serif">
                    The dominant sequence transduction models are based on complex recurrent or convolutional neural networks in an encoder-decoder configuration. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. Experiments on two machine translation tasks show these models to be superior in quality while being more parallelizable and requiring significantly less time to train. Our model achieves 28.4 BLEU on the WMT 2014 English-to-German translation task, improving over the existing best results, including ensembles by over 2 BLEU. On the WMT 2014 English-to-French translation task, our model establishes a new single-model state-of-the-art BLEU score of 41.8 after training for 3.5 days on eight GPUs, a small fraction of the training costs of the best models from the literature. We show that the Transformer generalizes well to other tasks by applying it successfully to English constituency parsing both with large and limited training data.
                </p>
            </div>
        </div>
    );
};

export default ViewOriginal;
