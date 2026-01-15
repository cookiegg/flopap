/**
 * API密钥配置提示组件
 */

import React from 'react';
import { Key, ExternalLink, Shield, DollarSign } from 'lucide-react';

interface ApiKeyPromptProps {
  theme?: 'dark' | 'light';
  onConfigureClick?: () => void;
}

const ApiKeyPrompt: React.FC<ApiKeyPromptProps> = ({
  theme = 'dark',
  onConfigureClick
}) => {
  const isDark = theme === 'dark';

  return (
    <div className={`p-4 rounded-lg border ${isDark ? 'bg-gray-800 border-gray-600' : 'bg-blue-50 border-blue-200'}`}>
      <div className="flex items-start">
        <div className={`p-2 rounded-lg ${isDark ? 'bg-blue-900' : 'bg-blue-100'} mr-3`}>
          <Key className={`w-5 h-5 ${isDark ? 'text-blue-400' : 'text-blue-600'}`} />
        </div>
        
        <div className="flex-1">
          <h3 className={`font-medium mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            需要配置API密钥
          </h3>
          
          <p className={`text-sm mb-3 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
            为了生成AI内容，您需要配置自己的DeepSeek API密钥。这样可以确保：
          </p>
          
          <div className="space-y-2 mb-4">
            <div className="flex items-center text-sm">
              <DollarSign className={`w-4 h-4 mr-2 ${isDark ? 'text-green-400' : 'text-green-600'}`} />
              <span className={isDark ? 'text-gray-300' : 'text-gray-600'}>
                成本可控 - 您只为自己使用的内容付费
              </span>
            </div>
            
            <div className="flex items-center text-sm">
              <Shield className={`w-4 h-4 mr-2 ${isDark ? 'text-blue-400' : 'text-blue-600'}`} />
              <span className={isDark ? 'text-gray-300' : 'text-gray-600'}>
                隐私保护 - 您的数据直接发送到DeepSeek，不经过我们的服务器
              </span>
            </div>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-2">
            <button
              onClick={onConfigureClick}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
            >
              配置API密钥
            </button>
            
            <a
              href="https://platform.deepseek.com/api_keys"
              target="_blank"
              rel="noopener noreferrer"
              className={`px-4 py-2 border rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium flex items-center justify-center ${
                isDark 
                  ? 'border-gray-600 text-gray-300 hover:bg-gray-700' 
                  : 'border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              获取API密钥
              <ExternalLink className="w-3 h-3 ml-1" />
            </a>
          </div>
          
          <div className={`mt-3 p-2 rounded text-xs ${isDark ? 'bg-gray-700 text-gray-400' : 'bg-gray-100 text-gray-500'}`}>
            💡 DeepSeek API价格非常便宜，生成一篇论文的所有内容通常只需要几分钱
          </div>
        </div>
      </div>
    </div>
  );
};

export default ApiKeyPrompt;
