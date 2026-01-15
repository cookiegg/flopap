/**
 * Framework V2 内容生成服务
 */

import axios from 'axios';
import { getApiBaseUrl } from './backendService';

const api = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 60000, // 内容生成可能需要更长时间
});

// 添加请求拦截器
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface UserGeneratedContent {
  id: string;
  paper_id: string;
  content_type: string;
  content_data: any;
  model_used: string;
  created_at: string;
  is_shared: boolean;
}

/**
 * 获取用户生成的内容
 */
export const getUserGeneratedContent = async (paperId?: string): Promise<UserGeneratedContent[]> => {
  try {
    const url = paperId ? `/v2/content/user?paper_id=${paperId}` : '/v2/content/user';
    const response = await api.get(url);
    return response.data;
  } catch (error) {
    console.error('获取用户生成内容失败:', error);
    return [];
  }
};

export interface ContentGenerationRequest {
  paper_id: string;
  content_type: 'translation' | 'infographic' | 'visualization' | 'summary' | 'tts';
  model_name: string;
}

export interface CostEstimationRequest {
  paper_id: string;
  content_type: string;
  model_name: string;
}

export interface TaskStatus {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  error_message?: string;
  estimated_cost?: number;
  actual_cost?: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface ContentResponse {
  source: 'user_generated' | 'admin_pushed' | 'shared_content';
  content: any;
  model_used?: string;
  created_at: string;
  quality_score?: number;
}

export interface UserGeneratedContent {
  id: string;
  paper_id: string;
  paper_title: string;
  arxiv_id: string;
  content_type: string;
  model_used: string;
  generation_cost?: number;
  quality_score?: number;
  usage_count: number;
  created_at: string;
}

/**
 * 生成内容
 */
export const generateContent = async (request: ContentGenerationRequest): Promise<{
  message: string;
  task_id?: string;
  existing_content?: ContentResponse;
  estimated_time?: string;
}> => {
  const response = await api.post('/v2/content/generate', request);
  return response.data;
};

/**
 * 查询任务状态
 */
export const getTaskStatus = async (taskId: string): Promise<TaskStatus> => {
  const response = await api.get(`/v2/content/task/${taskId}`);
  return response.data;
};

/**
 * 获取论文的所有内容
 */
export const getPaperContent = async (paperId: string): Promise<{
  paper_id: string;
  available_content: Record<string, ContentResponse>;
  content_count: number;
}> => {
  const response = await api.get(`/v2/content/paper/${paperId}`);
  return response.data;
};

/**
 * 估算生成成本
 */
export const estimateGenerationCost = async (request: CostEstimationRequest): Promise<{
  paper_id: string;
  content_type: string;
  model_name: string;
  estimated_cost_usd: number;
  estimated_cost_cny: number;
}> => {
  const response = await api.post('/v2/content/estimate-cost', request);
  return response.data;
};

/**
 * 获取用户生成的内容列表（分页）
 */
export const getUserGeneratedContentList = async (limit: number = 20): Promise<{
  content_list: UserGeneratedContent[];
  total_count: number;
}> => {
  const response = await api.get(`/v2/content/user-generated?limit=${limit}`);
  return response.data;
};

/**
 * 删除用户内容
 */
export const deleteUserContent = async (contentId: string): Promise<void> => {
  await api.delete(`/v2/content/${contentId}`);
};

/**
 * 获取支持的内容类型
 */
export const getSupportedContentTypes = async (): Promise<{
  content_types: Record<string, {
    name: string;
    description: string;
    estimated_time: string;
  }>;
}> => {
  const response = await api.get('/v2/content/supported-types');
  return response.data;
};
