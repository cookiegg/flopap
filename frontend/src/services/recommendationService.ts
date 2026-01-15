/**
 * Framework V2 推荐系统服务
 */

import axios from 'axios';
import { getApiBaseUrl } from './backendService';

const api = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 30000,
});

// 添加请求拦截器
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface RecommendationStats {
  total_recommendations: number;
  arxiv_count: number;
  conference_count: number;
  last_updated: string;
}

/**
 * 获取推荐统计数据
 */
export const getRecommendationStats = async (): Promise<RecommendationStats> => {
  try {
    const response = await api.get('/v2/recommendation/stats');
    return response.data;
  } catch (error) {
    // 返回默认数据
    return {
      total_recommendations: 0,
      arxiv_count: 0,
      conference_count: 0,
      last_updated: new Date().toISOString()
    };
  }
};

export interface RecommendationSettings {
  arxiv_ratio: number; // 1-50
  conference_ratio: number; // 1-50
  max_pool_size: number; // 10-200
  enable_auto_generation: boolean;
  preferred_models: string[];
}

export interface RecommendationSettingsResponse extends RecommendationSettings {
  user_id: string;
  updated_at: string;
}

export interface RecommendationFeedback {
  paper_id: string;
  feedback_type: 'like' | 'dislike' | 'bookmark';
  reason?: string;
}

export interface PersonalizedPaper {
  id: string;
  arxiv_id: string;
  title: string;
  summary: string;
  authors: any[];
  categories: string[];
  submitted_date: string;
  score: number;
}

export interface AdminPushedContent {
  id: string;
  paper_id: string;
  content_type: string;
  content_data: any;
  priority: number;
  created_by: string;
  created_at: string;
}

export interface DetailedRecommendationStats {
  feedback_stats: Record<string, number>;
  content_stats: Record<string, {
    count: number;
    total_cost: number;
  }>;
  total_generation_cost: number;
  total_feedback_count: number;
  total_content_count: number;
}

export interface AvailableModel {
  name: string;
  provider: string;
  description: string;
  cost_per_1k_tokens: number;
}

/**
 * 获取个性化推荐池
 */
export const getPersonalizedPool = async (): Promise<{
  user_id: string;
  pool_size: number;
  papers: PersonalizedPaper[];
  generated_at: string;
}> => {
  const response = await api.get('/v1/recommendation/pool');
  return response.data;
};

/**
 * 获取推荐设置
 */
export const getRecommendationSettings = async (): Promise<RecommendationSettingsResponse> => {
  const response = await api.get('/v1/recommendation/settings');
  return response.data;
};

/**
 * 更新推荐设置
 */
export const updateRecommendationSettings = async (settings: RecommendationSettings): Promise<{
  message: string;
  settings: RecommendationSettings;
}> => {
  const response = await api.put('/v1/recommendation/settings', settings);
  return response.data;
};

/**
 * 提交推荐反馈
 */
export const submitRecommendationFeedback = async (feedback: RecommendationFeedback): Promise<{
  message: string;
  paper_id: string;
  feedback_type: string;
}> => {
  const response = await api.post('/v1/recommendation/feedback', feedback);
  return response.data;
};

/**
 * 获取管理员推送内容
 */
export const getAdminPushedContent = async (): Promise<{
  user_id: string;
  pushed_content: AdminPushedContent[];
  count: number;
}> => {
  const response = await api.get('/v1/recommendation/admin-pushed');
  return response.data;
};

/**
 * 获取推荐效果统计（详细）
 */
export const getDetailedRecommendationStats = async (): Promise<{
  user_id: string;
  stats: DetailedRecommendationStats;
  generated_at: string;
}> => {
  const response = await api.get('/v1/recommendation/stats');
  return response.data;
};

/**
 * 获取可用的AI模型列表
 */
export const getAvailableModels = async (): Promise<{
  models: Record<string, AvailableModel>;
}> => {
  try {
    const response = await api.get('/v1/recommendation/available-models');
    return response.data;
  } catch (error) {
    // API might not exist in standalone edition, return empty models
    console.warn('Available models API not available:', error);
    return { models: {} };
  }
};
