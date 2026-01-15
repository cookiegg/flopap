/**
 * Framework V2 测试页面
 */

import React, { useState } from 'react';
import { Key, Settings, Sparkles, BarChart3, ArrowLeft } from 'lucide-react';
import APIKeyManager from './APIKeyManager';
import ContentGenerationHub from './ContentGenerationHub';
import RecommendationSettings from './RecommendationSettings';
import UserDashboard from './UserDashboard';

interface FrameworkV2TestProps {
  theme?: 'dark' | 'light';
  onBack?: () => void;
}

const FrameworkV2Test: React.FC<FrameworkV2TestProps> = ({ theme = 'dark', onBack }) => {
  const [activeTab, setActiveTab] = useState<'api-keys' | 'content' | 'settings' | 'dashboard'>('api-keys');
  
  const isDark = theme === 'dark';

  return (
    <div className={`w-full h-full flex flex-col ${isDark ? 'bg-gray-900 text-white' : 'bg-gray-50 text-gray-900'}`}>
      {/* 标题栏 */}
      <div className={`flex items-center justify-between p-4 border-b ${isDark ? 'border-gray-700' : 'border-gray-200'}`}>
        <button
          onClick={onBack}
          className={`flex items-center px-3 py-2 rounded-lg transition-colors ${
            isDark ? 'text-gray-400 hover:text-white hover:bg-gray-800' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
          }`}
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          返回
        </button>
        <h1 className="text-lg font-bold">Framework V2 AI助手</h1>
        <div className="w-16"></div>
      </div>

      {/* 标签页导航 */}
      <div className={`flex border-b ${isDark ? 'border-gray-700' : 'border-gray-200'}`}>
        {[
          { key: 'api-keys', label: 'API密钥', icon: Key, color: 'blue' },
          { key: 'content', label: '内容生成', icon: Sparkles, color: 'purple' },
          { key: 'settings', label: '推荐设置', icon: Settings, color: 'green' },
          { key: 'dashboard', label: '数据统计', icon: BarChart3, color: 'orange' }
        ].map(({ key, label, icon: Icon, color }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key as any)}
            className={`flex-1 flex items-center justify-center px-4 py-3 transition-colors ${
              activeTab === key
                ? `text-${color}-500 border-b-2 border-${color}-500`
                : isDark
                  ? 'text-gray-400 hover:text-white'
                  : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Icon className="w-4 h-4 mr-2" />
            <span className="text-sm font-medium">{label}</span>
          </button>
        ))}
      </div>

      {/* 内容区域 */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'api-keys' && (
          <APIKeyManager 
            theme={theme}
            onKeysUpdated={() => {
              console.log('API keys updated');
            }}
          />
        )}
        
        {activeTab === 'content' && (
          <ContentGenerationHub
            paperId="test-paper-id"
            paperTitle="测试论文标题"
            theme={theme}
            onContentGenerated={(contentType, content) => {
              console.log('Content generated:', contentType, content);
            }}
          />
        )}
        
        {activeTab === 'settings' && (
          <RecommendationSettings
            theme={theme}
            onSettingsUpdated={(settings) => {
              console.log('Recommendation settings updated:', settings);
            }}
          />
        )}
        
        {activeTab === 'dashboard' && (
          <UserDashboard theme={theme} />
        )}
      </div>
    </div>
  );
};

export default FrameworkV2Test;
