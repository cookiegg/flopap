/**
 * Framework V2 内容生成中心组件
 */

import React, { useState, useEffect } from 'react';
import { Sparkles, Clock, DollarSign, CheckCircle, XCircle, Loader2, Play, Eye, Download } from 'lucide-react';
import {
  generateContent,
  getTaskStatus,
  getPaperContent,
  estimateGenerationCost,
  getSupportedContentTypes,
  type ContentGenerationRequest,
  type TaskStatus,
  type ContentResponse
} from '../../services/contentService';

interface ContentGenerationHubProps {
  paperId: string;
  paperTitle: string;
  onContentGenerated?: (contentType: string, content: any) => void;
  theme?: 'dark' | 'light';
}

interface ContentTypeInfo {
  name: string;
  description: string;
  estimated_time: string;
  icon: React.ReactNode;
}

interface GenerationTask {
  taskId: string;
  contentType: string;
  modelName: string;
  status: TaskStatus;
}

const ContentGenerationHub: React.FC<ContentGenerationHubProps> = ({
  paperId,
  paperTitle,
  onContentGenerated,
  theme = 'dark'
}) => {
  const [contentTypes, setContentTypes] = useState<Record<string, ContentTypeInfo>>({});
  const [existingContent, setExistingContent] = useState<Record<string, ContentResponse>>({});
  const [activeTasks, setActiveTasks] = useState<GenerationTask[]>([]);
  const [selectedType, setSelectedType] = useState<string>('');
  const [selectedModel, setSelectedModel] = useState<string>('deepseek-chat');
  const [estimatedCost, setEstimatedCost] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  const isDark = theme === 'dark';

  // 内容类型图标映射
  const typeIcons: Record<string, React.ReactNode> = {
    translation: <Sparkles className="w-5 h-5" />,
    infographic: <Eye className="w-5 h-5" />,
    visualization: <Eye className="w-5 h-5" />,
    summary: <Download className="w-5 h-5" />,
    tts: <Play className="w-5 h-5" />
  };

  useEffect(() => {
    loadData();
  }, [paperId]);

  useEffect(() => {
    // 轮询活跃任务状态
    if (activeTasks.length > 0) {
      const interval = setInterval(updateTaskStatuses, 2000);
      return () => clearInterval(interval);
    }
  }, [activeTasks]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [typesData, contentData] = await Promise.all([
        getSupportedContentTypes(),
        getPaperContent(paperId)
      ]);

      // 添加图标到内容类型
      const typesWithIcons: Record<string, ContentTypeInfo> = {};
      Object.entries(typesData.content_types).forEach(([type, info]) => {
        typesWithIcons[type] = {
          ...info,
          icon: typeIcons[type] || <Sparkles className="w-5 h-5" />
        };
      });

      setContentTypes(typesWithIcons);
      setExistingContent(contentData.available_content);
    } catch (error) {
      console.error('加载数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateTaskStatuses = async () => {
    const updatedTasks = await Promise.all(
      activeTasks.map(async (task) => {
        try {
          const status = await getTaskStatus(task.taskId);
          return { ...task, status };
        } catch (error) {
          return task;
        }
      })
    );

    // 移除已完成或失败的任务
    const stillActiveTasks = updatedTasks.filter(
      task => task.status.status === 'pending' || task.status.status === 'processing'
    );

    // 检查是否有新完成的任务
    const completedTasks = updatedTasks.filter(
      task => task.status.status === 'completed' && 
      !activeTasks.find(t => t.taskId === task.taskId && t.status.status === 'completed')
    );

    if (completedTasks.length > 0) {
      // 重新加载内容
      await loadData();
      
      // 通知父组件
      completedTasks.forEach(task => {
        onContentGenerated?.(task.contentType, existingContent[task.contentType]);
      });
    }

    setActiveTasks(stillActiveTasks);
  };

  const handleEstimateCost = async (contentType: string, modelName: string) => {
    try {
      const result = await estimateGenerationCost({
        paper_id: paperId,
        content_type: contentType,
        model_name: modelName
      });
      setEstimatedCost(result.estimated_cost_cny);
    } catch (error) {
      console.error('成本估算失败:', error);
      setEstimatedCost(null);
    }
  };

  const handleGenerate = async () => {
    if (!selectedType || !selectedModel) return;

    try {
      setGenerating(true);
      
      const result = await generateContent({
        paper_id: paperId,
        content_type: selectedType as any,
        model_name: selectedModel
      });

      if (result.existing_content) {
        // 内容已存在
        onContentGenerated?.(selectedType, result.existing_content.content);
      } else if (result.task_id) {
        // 创建了新任务
        const newTask: GenerationTask = {
          taskId: result.task_id,
          contentType: selectedType,
          modelName: selectedModel,
          status: {
            id: result.task_id,
            status: 'pending',
            progress: 0,
            created_at: new Date().toISOString()
          }
        };
        setActiveTasks(prev => [...prev, newTask]);
      }

      setSelectedType('');
      setEstimatedCost(null);
    } catch (error) {
      console.error('生成失败:', error);
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className={`p-6 rounded-lg ${isDark ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin mr-2" />
          <span>加载中...</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`p-6 rounded-lg ${isDark ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
      {/* 标题 */}
      <div className="flex items-center mb-6">
        <Sparkles className="w-6 h-6 mr-2 text-purple-500" />
        <div>
          <h2 className="text-xl font-bold">内容生成中心</h2>
          <p className="text-sm text-gray-500 mt-1">{paperTitle}</p>
        </div>
      </div>

      {/* 现有内容 */}
      {Object.keys(existingContent).length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-medium mb-3">已有内容</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {Object.entries(existingContent).map(([type, content]) => (
              <div
                key={type}
                className={`p-3 rounded-lg border ${
                  isDark ? 'bg-gray-700 border-gray-600' : 'bg-gray-50 border-gray-200'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    {typeIcons[type]}
                    <span className="ml-2 font-medium">{contentTypes[type]?.name || type}</span>
                  </div>
                  <div className="flex items-center text-sm text-gray-500">
                    <CheckCircle className="w-4 h-4 text-green-500 mr-1" />
                    {content.source === 'user_generated' ? '自己生成' : 
                     content.source === 'admin_pushed' ? '官方推送' : '共享内容'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 活跃任务 */}
      {activeTasks.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-medium mb-3">生成中</h3>
          <div className="space-y-3">
            {activeTasks.map((task) => (
              <div
                key={task.taskId}
                className={`p-4 rounded-lg border ${
                  isDark ? 'bg-gray-700 border-gray-600' : 'bg-gray-50 border-gray-200'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center">
                    {typeIcons[task.contentType]}
                    <span className="ml-2 font-medium">
                      {contentTypes[task.contentType]?.name || task.contentType}
                    </span>
                  </div>
                  <div className="flex items-center text-sm">
                    {task.status.status === 'processing' ? (
                      <Loader2 className="w-4 h-4 animate-spin mr-1" />
                    ) : (
                      <Clock className="w-4 h-4 mr-1" />
                    )}
                    {task.status.status === 'pending' ? '等待中' : '生成中'}
                  </div>
                </div>
                
                {/* 进度条 */}
                <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${task.status.progress}%` }}
                  />
                </div>
                
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>模型: {task.modelName}</span>
                  <span>{task.status.progress}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 生成新内容 */}
      <div>
        <h3 className="text-lg font-medium mb-3">生成新内容</h3>
        
        {/* 内容类型选择 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
          {Object.entries(contentTypes)
            .filter(([type]) => !existingContent[type] && !activeTasks.some(t => t.contentType === type))
            .map(([type, info]) => (
              <button
                key={type}
                onClick={() => {
                  setSelectedType(type);
                  handleEstimateCost(type, selectedModel);
                }}
                className={`p-4 rounded-lg border text-left transition-colors ${
                  selectedType === type
                    ? 'border-blue-500 bg-blue-500/10'
                    : isDark 
                      ? 'border-gray-600 hover:border-gray-500 bg-gray-700'
                      : 'border-gray-200 hover:border-gray-300 bg-gray-50'
                }`}
              >
                <div className="flex items-center mb-2">
                  {info.icon}
                  <span className="ml-2 font-medium">{info.name}</span>
                </div>
                <p className="text-sm text-gray-500 mb-1">{info.description}</p>
                <div className="flex items-center text-xs text-gray-400">
                  <Clock className="w-3 h-3 mr-1" />
                  {info.estimated_time}
                </div>
              </button>
            ))}
        </div>

        {/* 模型选择和成本估算 */}
        {selectedType && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">选择模型</label>
              <select
                value={selectedModel}
                onChange={(e) => {
                  setSelectedModel(e.target.value);
                  handleEstimateCost(selectedType, e.target.value);
                }}
                className={`w-full p-3 rounded-lg border ${
                  isDark ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'
                } focus:ring-2 focus:ring-blue-500`}
              >
                <option value="deepseek-chat">DeepSeek Chat (推荐)</option>
                <option value="deepseek-reasoner">DeepSeek Reasoner (高质量)</option>
                <option value="qwen-turbo">通义千问 Turbo</option>
                <option value="qwen-plus">通义千问 Plus</option>
              </select>
            </div>

            {/* 成本显示 */}
            {estimatedCost !== null && (
              <div className={`p-3 rounded-lg ${isDark ? 'bg-blue-900/20' : 'bg-blue-50'}`}>
                <div className="flex items-center text-blue-600 dark:text-blue-400">
                  <DollarSign className="w-4 h-4 mr-1" />
                  <span className="text-sm">
                    预估成本: ¥{estimatedCost.toFixed(4)} | 
                    预计时间: {contentTypes[selectedType]?.estimated_time}
                  </span>
                </div>
              </div>
            )}

            {/* 生成按钮 */}
            <button
              onClick={handleGenerate}
              disabled={generating || !selectedModel}
              className="w-full px-4 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {generating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  生成中...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-2" />
                  开始生成
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ContentGenerationHub;
