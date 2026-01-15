/**
 * 论文内容生成组件 - 集成到现有PaperCard中
 * 提供按需内容生成功能
 */

import React, { useState, useEffect } from 'react';
import { Sparkles, Clock, DollarSign, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import {
  generateContent,
  getTaskStatus,
  estimateGenerationCost,
  type ContentGenerationRequest,
  type TaskStatus
} from '../../services/contentService';
import { getConfiguredServices } from '../../services/apiKeyService';

interface PaperContentGeneratorProps {
  paperId: string;
  paperTitle: string;
  contentType: 'translation' | 'infographic' | 'visualization' | 'summary' | 'tts';
  existingContent?: any;
  onContentGenerated?: (content: any) => void;
  theme?: 'dark' | 'light';
}

const PaperContentGenerator: React.FC<PaperContentGeneratorProps> = ({
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
  const [estimatedCost, setEstimatedCost] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const isDark = theme === 'dark';

  const contentTypeNames = {
    translation: '中文翻译',
    infographic: '信息图',
    visualization: '可视化',
    summary: '简洁摘要',
    tts: '语音文本'
  };

  const contentTypeIcons = {
    translation: '🌐',
    infographic: '📊',
    visualization: '🎨',
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

      // 估算成本
      const costResult = await estimateGenerationCost({
        paper_id: paperId,
        content_type: contentType,
        model_name: 'deepseek-chat'
      });
      setEstimatedCost(costResult.estimated_cost_cny);

      // 开始生成
      const result = await generateContent({
        paper_id: paperId,
        content_type: contentType,
        model_name: 'deepseek-chat'
      });

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
      setError(error.response?.data?.detail || '生成失败，请重试');
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
            <span className="font-medium">{contentTypeNames[contentType]}</span>
          </div>
          <div className="flex items-center text-sm text-blue-500">
            <Loader2 className="w-3 h-3 animate-spin mr-1" />
            生成中
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
          {estimatedCost && <span>预估: ¥{estimatedCost.toFixed(4)}</span>}
        </div>
      </div>
    );
  }

  // 显示生成按钮
  return (
    <div className={`p-3 rounded-lg border ${isDark ? 'bg-gray-700 border-gray-600' : 'bg-gray-50 border-gray-200'}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center">
          <span className="text-lg mr-2">{contentTypeIcons[contentType]}</span>
          <span className="font-medium">{contentTypeNames[contentType]}</span>
        </div>
        
        {!hasApiKeys && (
          <div className="flex items-center text-xs text-yellow-500">
            <AlertCircle className="w-3 h-3 mr-1" />
            需配置密钥
          </div>
        )}
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
            {hasApiKeys ? '生成内容' : '需要API密钥'}
          </>
        )}
      </button>

      {hasApiKeys && estimatedCost && (
        <div className="text-xs text-gray-500 mt-1 text-center">
          预估成本: ¥{estimatedCost.toFixed(4)}
        </div>
      )}
    </div>
  );
};

export default PaperContentGenerator;
