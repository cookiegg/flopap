import axios, { AxiosError } from 'axios';
import { Paper, Insight } from '../types';
import { Capacitor } from '@capacitor/core';

// 数据验证工具函数
const validateUUID = (id: string): boolean => {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  return uuidRegex.test(id);
};

const validateHtmlContent = (html: string): boolean => {
  return html && html.trim().length > 0 && html.length <= 1024 * 1024; // 1MB limit
};

const validateImageData = (imageData: string): boolean => {
  return imageData && imageData.startsWith('data:image/') && imageData.length <= 10 * 1024 * 1024; // 10MB limit
};
const handleApiError = (error: unknown, context: string) => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError;
    console.error(`${context}:`, {
      status: axiosError.response?.status,
      message: axiosError.response?.data || axiosError.message,
      url: axiosError.config?.url
    });

    // 根据状态码返回不同错误信息
    switch (axiosError.response?.status) {
      case 401:
        // 清除过期token
        localStorage.removeItem('token');
        throw new Error('认证已过期，请重新登录');
      case 403:
        throw new Error('权限不足');
      case 404:
        throw new Error('资源不存在');
      case 422:
        throw new Error('请求参数格式错误');
      case 500:
        throw new Error('服务器内部错误');
      default:
        throw new Error((axiosError.response?.data as any)?.detail || '网络请求失败');
    }
  } else {
    console.error(`${context}:`, error);
    throw new Error('未知错误');
  }
};

// 根据平台和环境选择API地址
export const getApiBaseUrl = () => {
  if (Capacitor.isNativePlatform()) {
    // 原生应用：必须设置VITE_API_URL环境变量
    const apiUrl = import.meta.env.VITE_API_URL;
    if (!apiUrl) {
      console.error('VITE_API_URL not set for native app! Check .env configuration');
      // Standalone edition: no cloud fallback
      return '/api';
    }
    return apiUrl;
  }
  // Web：优先使用环境变量，否则使用相对路径
  return import.meta.env.VITE_API_URL || '/api';
};

const API_BASE_URL = getApiBaseUrl();

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  proxy: false,
});

// 添加请求拦截器，自动添加token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface FeedResponse {
  items: Array<{
    position: number;
    score: number;
    paper: {
      id: string;
      arxiv_id: string;
      title: string;
      summary: string;
      authors: Array<{ name: string; affiliation?: string }>; // 修正：匹配后端数据结构
      categories: string[];
      submitted_date: string;
      updated_date: string;
      pdf_url: string;
      html_url: string;
      comment?: string;
      doi?: string;
      primary_category: string;
      translation?: {
        title_zh?: string;
        summary_zh?: string;
        model_name?: string;
      };
      interpretation?: {
        interpretation?: string;
        language?: string;
        model_name?: string;
      };
    };
    liked: boolean;
    bookmarked: boolean;
    disliked: boolean;
  }>;
  next_cursor: number;
  total: number;
}

// 转换后端数据格式到前端格式
const convertToPaper = (item: FeedResponse['items'][0]): Paper => {
  const { paper, liked, bookmarked, disliked } = item;

  // 解析 AI insights
  let aiInsights: Insight[] | undefined;

  if (paper.interpretation?.interpretation) {
    // 直接使用纯文本，不再尝试JSON解析
    aiInsights = paper.interpretation.interpretation as any;
  }

  // 转换作者格式：从对象数组提取名字
  const authorNames = Array.isArray(paper.authors)
    ? paper.authors.map(author => typeof author === 'string' ? author : author.name)
    : [];

  return {
    id: paper.id,
    arxiv_id: paper.arxiv_id,
    title: paper.title,
    authors: authorNames,
    abstract: paper.summary,
    publishedDate: new Date(paper.submitted_date).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    }),
    pdfUrl: paper.pdf_url,
    categories: paper.categories,
    liked,
    bookmarked,
    disliked,
    translatedTitle: paper.translation?.title_zh,
    translatedAbstract: paper.translation?.summary_zh,
    aiInsights,
    visualizationUrl: undefined,
    visual_html: (paper as any).visual_html, // 使用feed中的可视化图数据
    translation: paper.translation,
    infographicHtml: (paper as any).infographic_html, // 使用feed中的信息图数据
  };
};

// 获取推荐论文
export const fetchFeedPapers = async (
  cursor: number = 0,
  limit: number = 10,
  source?: string,
  query?: string,
  sub?: string,  // 新增: arxiv 子池参数 (today/week)
): Promise<{ papers: Paper[]; nextCursor: number; total: number }> => {
  try {
    const params: any = { cursor, limit };
    if (source) {
      params.source = source;
    }
    if (query) {
      params.query = query;
    }
    if (sub) {
      params.sub = sub;
    }

    const response = await api.get<FeedResponse>('/v1/feed', { params });

    return {
      papers: response.data.items.map(convertToPaper),
      nextCursor: response.data.next_cursor,
      total: response.data.total
    };
  } catch (error) {
    handleApiError(error, 'Failed to fetch feed');
    return { papers: [], nextCursor: 0, total: 0 };
  }
};

// 提交反馈
export const submitFeedback = async (
  paperId: string,
  action: 'like' | 'dislike' | 'bookmark' | 'not_interested',
  value: boolean = true,
  confirmed: boolean = false
): Promise<void> => {
  try {
    await api.post('/v1/feed/feedback', {
      paper_id: paperId,
      action,
      value,
      confirmed
    });
  } catch (error) {
    handleApiError(error, 'Failed to submit feedback');
  }
};

// 获取用户资料
export const getUserProfile = async () => {
  try {
    const response = await api.get('/v1/user/profile');
    return response.data;
  } catch (error) {
    handleApiError(error, 'Failed to get user profile');
    return null;
  }
};

// 获取用户交互数据（点赞、收藏、不感兴趣）
export const getUserInteractions = async () => {
  try {
    const response = await api.get('/v1/user/summary');

    // 返回 ID 列表和统计数据
    return {
      likedPaperIds: response.data.liked?.map((p: any) => p.id) || [],
      bookmarkedPaperIds: response.data.bookmarked?.map((p: any) => p.id) || [],
      notInterestedPaperIds: response.data.disliked?.map((p: any) => p.id) || [],
      stats: response.data.stats || {
        liked_count: 0,
        bookmarked_count: 0,
        disliked_count: 0
      }
    };
  } catch (error) {
    console.error('Failed to get user interactions:', error);
    return {
      likedPaperIds: [],
      bookmarkedPaperIds: [],
      notInterestedPaperIds: [],
      stats: {
        liked_count: 0,
        bookmarked_count: 0,
        disliked_count: 0
      }
    };
  }
};

// 分页获取用户收藏的论文详情
export const getUserCollection = async (
  collectionType: 'liked' | 'bookmarked',
  limit: number = 20,
  offset: number = 0
) => {
  try {
    const response = await api.get(`/v1/user/summary`);

    // Create Sets of IDs for quick lookup
    const likedIds = new Set((response.data.liked || []).map((p: any) => p.id));
    const bookmarkedIds = new Set((response.data.bookmarked || []).map((p: any) => p.id));
    const dislikedIds = new Set((response.data.disliked || []).map((p: any) => p.id));

    // 从用户摘要中获取对应类型的论文
    const papers = (response.data[collectionType] || []).slice(offset, offset + limit).map((p: any) => {
      // 解析 AI insights
      let aiInsights;
      if (p.interpretation?.interpretation) {
        aiInsights = p.interpretation.interpretation;
      }

      // 转换作者格式
      const authorNames = Array.isArray(p.authors)
        ? p.authors.map((author: any) => typeof author === 'string' ? author : author.name)
        : [];

      return {
        // Inject interaction state
        liked: likedIds.has(p.id),
        bookmarked: bookmarkedIds.has(p.id),
        disliked: dislikedIds.has(p.id),

        id: p.id,
        arxiv_id: p.arxiv_id,
        title: p.title,
        authors: authorNames,
        abstract: p.summary,
        publishedDate: p.submitted_date ? new Date(p.submitted_date).toLocaleDateString('en-US', {
          weekday: 'long',
          year: 'numeric',
          month: 'long',
          day: 'numeric'
        }) : '',
        pdfUrl: p.pdf_url,
        categories: p.categories,
        translatedTitle: p.translation?.title_zh,
        translatedAbstract: p.translation?.summary_zh,
        aiInsights,
        translation: p.translation,
      };
    });

    const total = response.data[collectionType]?.length || 0;

    return {
      papers,
      total,
      hasMore: offset + limit < total
    };
  } catch (error) {
    console.error('Failed to get user collection:', error);
    return { papers: [], total: 0, hasMore: false };
  }
};

// 更新用户偏好
export const updateUserPreferences = async (preferences: {
  selectedCategories?: string[];
  keywords?: string[];
  name?: string;
}) => {
  try {
    // 数据验证
    if (preferences.selectedCategories && !Array.isArray(preferences.selectedCategories)) {
      throw new Error('Invalid categories format');
    }
    if (preferences.keywords && !Array.isArray(preferences.keywords)) {
      throw new Error('Invalid keywords format');
    }

    const payload = {
      interested_categories: preferences.selectedCategories,
      research_keywords: preferences.keywords,
      name: preferences.name
    };
    await api.put('/v1/user/preferences', payload);  // 修复：使用正确的路径
  } catch (error) {
    handleApiError(error, 'Failed to update preferences');
  }
};

export const completeOnboarding = async () => {
  try {
    await api.post('/v1/user/onboarding/complete');  // 修复：使用正确的路径
  } catch (error) {
    handleApiError(error, 'Failed to complete onboarding');
  }
};

// 检查用户名是否可用
export const checkUsername = async (username: string): Promise<{ available: boolean; message?: string }> => {
  try {
    if (!username || username.trim().length === 0) {
      return { available: false, message: '用户名不能为空' };
    }
    if (username.length < 2 || username.length > 20) {
      return { available: false, message: '用户名长度应在2-20字符之间' };
    }

    // 简单的用户名格式验证
    const usernameRegex = /^[a-zA-Z0-9_\u4e00-\u9fa5]+$/;
    if (!usernameRegex.test(username)) {
      return { available: false, message: '用户名只能包含字母、数字、下划线和中文' };
    }

    // 这里可以添加后端检查逻辑，目前先返回可用
    return { available: true };
  } catch (error) {
    handleApiError(error, 'Failed to check username');
    return { available: false, message: '检查用户名时出错' };
  }
};

// 发送短信验证码
export const sendSmsCode = async (phoneNumber: string): Promise<{ success: boolean; message: string }> => {
  try {
    await api.post('/v1/sms/send', { phone_number: phoneNumber });
    return { success: true, message: '验证码发送成功' };
  } catch (error: any) {
    return { success: false, message: error.response?.data?.detail || '发送失败' };
  }
};

// 短信验证码登录
export const loginWithSms = async (phoneNumber: string, code: string): Promise<{ success: boolean; message?: string; data?: any }> => {
  try {
    const response = await api.post('/v1/sms/login', { phone_number: phoneNumber, code });
    return { success: true, data: response.data };
  } catch (error: any) {
    return { success: false, message: error.response?.data?.detail || '验证失败' };
  }
};
// 保存生成的 Infographic (HTML)
export const saveInfographic = async (paperId: string, html: string): Promise<boolean> => {
  try {
    console.log('[saveInfographic] Starting save for paper:', paperId);
    console.log('[saveInfographic] HTML length:', html.length);

    // 数据验证
    if (!validateUUID(paperId)) {
      console.error('[saveInfographic] Invalid paper ID format:', paperId);
      throw new Error('Invalid paper ID format');
    }
    if (!validateHtmlContent(html)) {
      console.error('[saveInfographic] Invalid HTML content, length:', html.length);
      throw new Error('Invalid HTML content');
    }

    console.log('[saveInfographic] Sending request to backend...');
    const response = await api.post(`/v1/paper/${paperId}/infographic`, { html_content: html });
    console.log('[saveInfographic] Success:', response.data);
    return true;
  } catch (error) {
    console.error('[saveInfographic] Error occurred:', error);
    handleApiError(error, 'Failed to save infographic');
    return false;
  }
};

// 检查论文信息图状态
export const checkInfographicStatus = async (paperId: string): Promise<{ has_infographic: boolean, last_updated?: string }> => {
  try {
    if (!validateUUID(paperId)) {
      throw new Error('Invalid paper ID format');
    }

    const response = await api.get(`/v1/paper/${paperId}/infographic`);
    return { has_infographic: true, last_updated: response.data.updated_at };
  } catch (error: any) {
    if (axios.isAxiosError(error) && error.response?.status === 404) {
      return { has_infographic: false };
    }
    handleApiError(error, 'Failed to check infographic status');
    return { has_infographic: false };
  }
};

// 获取论文信息图 (HTML)
export const getInfographic = async (paperId: string): Promise<string | null> => {
  try {
    if (!validateUUID(paperId)) {
      throw new Error('Invalid paper ID format');
    }

    const response = await api.get(`/v1/paper/${paperId}/infographic`);
    return response.data.html_content || null;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 404) {
      return null; // 正常情况：信息图不存在
    }
    handleApiError(error, 'Failed to get infographic');
    return null;
  }
};

// 保存生成的 Visual (Base64 图像)
export const saveVisualization = async (paperId: string, imageData: string): Promise<boolean> => {
  try {
    // 数据验证
    if (!validateUUID(paperId)) {
      throw new Error('Invalid paper ID format');
    }
    if (!validateImageData(imageData)) {
      throw new Error('Invalid image data');
    }

    await api.post(`/v1/paper/${paperId}/visual`, { image_data: imageData });
    return true;
  } catch (error) {
    handleApiError(error, 'Failed to save visualization');
    return false;
  }
};

// 获取论文可视化图像 (Base64)
export const getVisualization = async (paperId: string): Promise<string | null> => {
  try {
    if (!validateUUID(paperId)) {
      throw new Error('Invalid paper ID format');
    }

    const response = await api.get(`/v1/paper/${paperId}/visual`);
    return response.data.image_data || null;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 404) {
      return null; // 正常情况：可视化图不存在
    }
    handleApiError(error, 'Failed to get visualization');
    return null;
  }
};
