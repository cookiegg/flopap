/**
 * 仅客户端内容生成组件
 */

import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  Clock, 
  Loader2, 
  CheckCircle, 
  AlertCircle, 
  Smartphone,
  Key,
  Settings
} from 'lucide-react';
import {
  generateContent,
  getTaskStatus,
  type TaskStatus
} from '../../services/aiGenerationService';
import { getConfiguredServices } from '../../services/apiKeyService';

interface ClientOnlyContentGeneratorProps {
  paperId: string;
  paperTitle: string;
  contentType: 'translation' | 'infographic' | 'summary' | 'tts';
  existingContent?: any;
  onContentGenerated?: (content: any) => void;
  theme?: 'dark' | 'light';
}

const ClientOnlyContentGenerator: React.FC<ClientOnlyContentGeneratorProps> = ({
  paperId,
  paperTitle,
  contentType,
  existingContent,
  onContentGenerated,
  theme = 'dark'
}) => {
  const [hasApiKeys, setHasApiKeys] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  const isDark = theme === 'dark';

  const contentTypeNames = {
    translation: '中文翻译',
    infographic: '信息图',
    summary: '简洁摘要',
    tts: '语音文本'
  };

  const contentTypeIcons = {
    translation: '🌐',
    infographic: '📊',
    summary: '📝',
    tts: '🔊'
  };

  useEffect(() => {
    checkApiKeys();
  }, []);

  useEffect(() => {
    if (taskId && generating) {
      const interval = setInterval(checkTaskStatus, 2000);
      return () => clearInterval(interval);
    }
  }, [taskId, generating]);

  const checkApiKeys = async () => {
    try {
      const services = await getConfiguredServices();
      setHasApiKeys(services.length > 0);
    } catch (error) {
      console.error('检查API密钥失败:', error);
    }
  };

  const checkTaskStatus = async () => {
    if (!taskId) return;

    try {
      const status = await getTaskStatus(taskId);
      setTaskStatus(status);

      if (status.status === 'completed') {
        setGenerating(false);
        onContentGenerated?.(status);
      } else if (status.status === 'failed') {
        setGenerating(false);
        setError(status.error_message || '生成失败');
      }
    } catch (error) {
      console.error('检查任务状态失败:', error);
    }
  };

  const handleGenerate = async () => {
    if (!hasApiKeys) {
      setError('请先在用户设置中配置API密钥');
      return;
    }

    try {
      setGenerating(true);
      setError(null);

      const result = await generateContent(
        paperId,
        contentType,
        'deepseek-chat'
      );

      if (result.existing_content) {
        // 内容已存在
        setGenerating(false);
        onContentGenerated?.(result.existing_content.content);
      } else if (result.task_id) {
        // 创建了新任务
        setTaskId(result.task_id);
      }
    } catch (error: any) {
      setGenerating(false);
      setError(error.message || '生成失败，请重试');
    }
  };

  // 如果已有内容，显示内容状态
  if (existingContent) {
    return (
      <div className={`p-3 rounded-lg border ${isDark ? 'bg-gray-700 border-gray-600' : 'bg-gray-50 border-gray-200'}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <span className="text-lg mr-2">{contentTypeIcons[contentType]}</span>
            <div>
              <span className="font-medium">{contentTypeNames[contentType]}</span>
              <div className="flex items-center text-sm text-gray-500 mt-1">
                <CheckCircle className="w-3 h-3 text-green-500 mr-1" />
                已生成
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 如果正在生成，显示进度
  if (generating && taskStatus) {
    return (
      <div className={`p-3 rounded-lg border ${isDark ? 'bg-gray-700 border-gray-600' : 'bg-gray-50 border-gray-200'}`}>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center">
            <span className="text-lg mr-2">{contentTypeIcons[contentType]}</span>
            <div>
              <span className="font-medium">{contentTypeNames[contentType]}</span>
              <div className="flex items-center text-sm text-blue-500 mt-1">
                <Smartphone className="w-3 h-3 mr-1" />
                使用您的API密钥生成中
              </div>
            </div>
          </div>
          <div className="flex items-center text-sm text-blue-500">
            <Loader2 className="w-3 h-3 animate-spin mr-1" />
            {taskStatus.progress}%
          </div>
        </div>
        
        {/* 进度条 */}
        <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2 mb-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${taskStatus.progress}%` }}
          />
        </div>
        
        <div className="flex justify-between text-xs text-gray-500">
          <span>{taskStatus.progress}% 完成</span>
          <span>成本由您承担</span>
        </div>
      </div>
    );
  }

  // 显示生成选项
  return (
    <div className={`p-3 rounded-lg border ${isDark ? 'bg-gray-700 border-gray-600' : 'bg-gray-50 border-gray-200'}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center">
          <span className="text-lg mr-2">{contentTypeIcons[contentType]}</span>
          <span className="font-medium">{contentTypeNames[contentType]}</span>
        </div>
      </div>

      {/* API密钥状态 */}
      <div className="mb-3">
        <div className={`p-2 rounded text-xs ${isDark ? 'bg-gray-600' : 'bg-gray-100'}`}>
          <div className="flex items-center mb-1">
            <Smartphone className="w-3 h-3 text-blue-500 mr-1" />
            <span className="font-medium">客户端生成模式</span>
          </div>
          <div className="text-gray-500">
            {hasApiKeys ? (
              <>
                <div className="flex items-center text-green-600">
                  <Key className="w-3 h-3 mr-1" />
                  API密钥已配置
                </div>
                <div className="text-xs mt-1">• 成本可控 • 无排队等待 • 数据隐私保护</div>
              </>
            ) : (
              <>
                <div className="flex items-center text-yellow-600">
                  <AlertCircle className="w-3 h-3 mr-1" />
                  需要配置API密钥
                </div>
                <div className="text-xs mt-1">请在用户设置中配置您的DeepSeek API密钥</div>
              </>
            )}
          </div>
        </div>
      </div>

      {error && (
        <div className="text-xs text-red-500 mb-2 flex items-center">
          <AlertCircle className="w-3 h-3 mr-1" />
          {error}
        </div>
      )}

      <button
        onClick={handleGenerate}
        disabled={generating || !hasApiKeys}
        className={`w-full px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
          hasApiKeys
            ? 'bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50'
            : 'bg-gray-400 text-gray-200 cursor-not-allowed'
        }`}
      >
        {generating ? (
          <>
            <Loader2 className="w-3 h-3 animate-spin mr-1" />
            生成中...
          </>
        ) : (
          <>
            <Sparkles className="w-3 h-3 mr-1" />
            {hasApiKeys ? '开始生成' : '需要API密钥'}
          </>
        )}
      </button>

      {/* 底部信息 */}
      <div className="mt-2 flex justify-between text-xs text-gray-500">
        <span className="flex items-center">
          <Clock className="w-3 h-3 mr-1" />
          {contentType === 'infographic' ? '2-3分钟' : '1-2分钟'}
        </span>
        {!hasApiKeys && (
          <button 
            className="flex items-center text-blue-500 hover:text-blue-400"
            onClick={() => {/* 跳转到设置页面 */}}
          >
            <Settings className="w-3 h-3 mr-1" />
            去配置
          </button>
        )}
      </div>
    </div>
  );
};

export default ClientOnlyContentGenerator;
