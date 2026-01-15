import React from 'react';

interface ShareFooterProps {
  mode?: 'paper' | 'app';
}

const ShareFooter: React.FC<ShareFooterProps> = ({ mode = 'paper' }) => {
  return (
    <div className="bg-slate-900 p-6 text-center" style={{ width: '600px' }}>
      <div className="text-xl font-bold mb-4 text-white">
        📚 FloPap - AI 论文，像刷短视频一样简单
      </div>
      
      <div className="flex justify-center gap-8 mb-4">
        <div className="text-center">
          <div className="bg-white p-2 rounded-lg inline-block">
            {/* 使用简单的黑色方块代替二维码测试 */}
            <div style={{ 
              width: '100px', 
              height: '100px', 
              backgroundColor: '#000',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              fontSize: '12px'
            }}>
              GitHub
            </div>
          </div>
          <div className="mt-2 text-sm text-slate-300">GitHub 开源</div>
        </div>
        
        <div className="text-center">
          <div className="bg-white p-2 rounded-lg inline-block">
            <div style={{ 
              width: '100px', 
              height: '100px', 
              backgroundColor: '#000',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              fontSize: '12px'
            }}>
              Website
            </div>
          </div>
          <div className="mt-2 text-sm text-slate-300">在线体验</div>
        </div>
      </div>
      
      <div className="text-sm text-slate-400">
        {mode === 'paper' ? '扫码发现更多 AI 论文精华' : '扫码开始你的 AI 论文之旅'}
      </div>
    </div>
  );
};

export default ShareFooter;
