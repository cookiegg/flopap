/**
 * AI内容生成服务 - 支持完整的客户端生成（包括可视化）
 */

import axios from 'axios';
import { getApiBaseUrl } from './backendService';
import { APIKeyService } from './apiKeyService';
import ErrorHandler from './errorHandler';

const api = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 120000,
});

// 添加请求拦截器
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface GenerationRequest {
  paper_id: string;
  content_type: 'translation' | 'infographic' | 'visualization' | 'summary' | 'tts';
  model_name: string;
  custom_prompt?: string;
}

export interface TaskStatus {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  error_message?: string;
  generation_mode: string;
  estimated_cost: number;
  actual_cost: number;
  created_at: string;
  completed_at?: string;
}

export interface GenerationResult {
  message: string;
  task_id?: string;
  generation_mode?: string;
  estimated_time?: string;
  existing_content?: any;
  notice?: string;
}

export async function getConfiguredServices() {
  const keys = await APIKeyService.getAllAPIKeys();
  const services = [];

  if (keys.deepseek) {
    services.push({
      name: 'DeepSeek',
      apiKey: keys.deepseek,
      model: 'deepseek-chat'
    });
  }

  if (keys.gemini) {
    services.push({
      name: 'Gemini',
      apiKey: keys.gemini,
      model: 'gemini-2.5-flash'
    });
  }

  return services;
}

/**
 * 生成内容 - 用户端仅客户端模式
 */
export const generateContent = async (
  paperId: string,
  contentType: string,
  modelName: string = 'deepseek-chat',
  customPrompt?: string
): Promise<GenerationResult> => {
  
  return ErrorHandler.retryWithBackoff(async () => {
    // 检查用户是否配置了API密钥
    const configuredServices = await getConfiguredServices();
    if (configuredServices.length === 0) {
      const error = new Error('API_KEY_MISSING');
      error.name = 'API_KEY_MISSING';
      throw error;
    }
    
    const request: GenerationRequest = {
      paper_id: paperId,
      content_type: contentType as any,
      model_name: modelName,
      custom_prompt: customPrompt
    };
    
    try {
      // 创建用户任务（仅客户端模式）
      const response = await api.post('/v2/user/content/generate', request);
      const result = response.data;
      
      // 立即启动客户端生成
      if (result.task_id) {
        setTimeout(() => {
          startClientGeneration(result.task_id, paperId, contentType, modelName, customPrompt);
        }, 500);
      }
      
      return result;
    } catch (error: any) {
      ErrorHandler.showUserFriendlyError(error);
      throw error;
    }
  });
};

/**
 * 客户端生成流程
 */
const startClientGeneration = async (
  taskId: string,
  paperId: string,
  contentType: string,
  modelName: string,
  customPrompt?: string
) => {
  try {
    console.log(`开始客户端生成: ${contentType} for paper ${paperId}`);
    
    // 更新任务状态为处理中
    await updateTaskProgress(taskId, 10, 'processing');
    
    // 获取用户API密钥
    const services = await getConfiguredServices();
    if (services.length === 0) {
      throw new Error('未配置API密钥');
    }
    
    // 根据内容类型调用对应的生成函数
    let contentData: any;
    
    switch (contentType) {
      case 'translation':
        contentData = await generateTranslationClient(paperId, modelName, services[0], taskId);
        break;
      case 'infographic':
        contentData = await generateInfographicClient(paperId, modelName, services[0], customPrompt, taskId);
        break;
      case 'visualization':
        contentData = await generateVisualizationClient(paperId, modelName, services[0], taskId);
        break;
      case 'summary':
        contentData = await generateSummaryClient(paperId, modelName, services[0], taskId);
        break;
      case 'tts':
        contentData = await generateTTSClient(paperId, modelName, services[0], taskId);
        break;
      default:
        throw new Error(`不支持的内容类型: ${contentType}`);
    }
    
    // 上传生成结果
    await uploadClientContent(taskId, contentData);
    
    console.log(`客户端生成完成: ${taskId}`);
    
  } catch (error) {
    console.error('客户端生成失败:', error);
    await updateTaskProgress(taskId, 0, 'failed', error.message);
  }
};

/**
 * 客户端可视化生成 - 使用Gemini API
 */
const generateVisualizationClient = async (
  paperId: string,
  modelName: string,
  apiService: any,
  taskId: string
): Promise<any> => {
  
  // 获取论文信息
  const paperResponse = await api.get(`/papers/${paperId}`);
  const paper = paperResponse.data;
  
  // 检查是否为Gemini API服务
  if (!apiService.baseUrl.includes('generativelanguage.googleapis.com')) {
    throw new Error('可视化生成需要配置Gemini API密钥');
  }
  
  await updateTaskProgress(taskId, 30, 'processing');
  
  // 使用Gemini API生成图像
  const geminiApi = axios.create({
    baseURL: 'https://generativelanguage.googleapis.com/v1beta',
    headers: {
      'Content-Type': 'application/json'
    }
  });
  
  const prompt = `Create an educational infographic to explain this academic paper in simple terms:

Paper Title: ${paper.title}

Paper Abstract: ${paper.summary.substring(0, 600)}

Requirements:
1. Simple diagrams showing core concepts
2. Clear method/approach flowchart with step-by-step process
3. Key results visualization (charts or comparisons)
4. Use English labels, concise and easy to understand
5. Style: Clean, academic but accessible, like a science magazine illustration
6. Colors: Bright and clear, well-coordinated palette
7. Layout: Well-organized with clear sections

Generate a complete infographic.`;

  await updateTaskProgress(taskId, 50, 'processing');
  
  try {
    const response = await geminiApi.post(`/models/gemini-pro-vision:generateContent?key=${apiService.apiKey}`, {
      contents: [{
        parts: [{
          text: prompt
        }]
      }],
      generationConfig: {
        temperature: 0.7,
        maxOutputTokens: 2048
      }
    });
    
    await updateTaskProgress(taskId, 70, 'processing');
    
    // 注意：实际的Gemini API响应格式可能不同
    // 这里需要根据实际API文档调整
    const imageData = response.data.candidates?.[0]?.content?.parts?.[0]?.inlineData;
    
    if (!imageData) {
      throw new Error('Gemini API未返回图像数据');
    }
    
    await updateTaskProgress(taskId, 90, 'processing');
    
    // 转换为base64 data URL
    const dataUrl = `data:${imageData.mimeType};base64,${imageData.data}`;
    
    return {
      image_data: dataUrl,
      model_used: 'gemini-pro-vision'
    };
    
  } catch (error) {
    console.error('Gemini API调用失败:', error);
    throw new Error(`可视化生成失败: ${error.response?.data?.error?.message || error.message}`);
  }
};

/**
 * 更新任务进度
 */
const updateTaskProgress = async (
  taskId: string, 
  progress: number, 
  status: string, 
  errorMessage?: string
) => {
  try {
    await api.patch(`/v2/content/task/${taskId}`, {
      progress,
      status,
      error_message: errorMessage
    });
  } catch (error) {
    console.error('更新任务进度失败:', error);
  }
};

/**
 * 客户端翻译生成
 */
const generateTranslationClient = async (
  paperId: string,
  modelName: string,
  apiService: any,
  taskId: string
): Promise<any> => {
  
  // 获取论文信息
  const paperResponse = await api.get(`/papers/${paperId}`);
  const paper = paperResponse.data;
  
  const translationApi = axios.create({
    baseURL: apiService.baseUrl,
    headers: {
      'Authorization': `Bearer ${apiService.apiKey}`,
      'Content-Type': 'application/json'
    }
  });
  
  // 翻译标题
  await updateTaskProgress(taskId, 30, 'processing');
  const titleResponse = await translationApi.post('/chat/completions', {
    model: modelName,
    messages: [
      { role: 'system', content: '你是专业的学术论文翻译助手。' },
      { role: 'user', content: `请将以下英文标题翻译成中文：${paper.title}` }
    ],
    max_tokens: 200,
    temperature: 0.3
  });
  
  const titleZh = titleResponse.data.choices[0].message.content.trim();
  
  // 翻译摘要
  await updateTaskProgress(taskId, 50, 'processing');
  const summaryResponse = await translationApi.post('/chat/completions', {
    model: modelName,
    messages: [
      { role: 'system', content: '你是专业的学术论文翻译助手。' },
      { role: 'user', content: `请将以下英文摘要翻译成中文：${paper.summary}` }
    ],
    max_tokens: 1000,
    temperature: 0.3
  });
  
  const summaryZh = summaryResponse.data.choices[0].message.content.trim();
  
  // 生成AI解读
  await updateTaskProgress(taskId, 70, 'processing');
  const interpretationPrompt = `请对以下学术论文进行深度解读分析：

标题: ${paper.title}
摘要: ${paper.summary}

请提供全面的论文解读，包括：
1. 研究背景与动机
2. 核心创新点与贡献  
3. 技术方法详解
4. 实验结果分析
5. 学术价值与影响
6. 未来研究方向

要求：
- 用通俗易懂的中文表达
- 每个部分内容充实完整
- 总字数控制在800-1200字
- 使用纯文本格式`;

  const interpretationResponse = await translationApi.post('/chat/completions', {
    model: modelName,
    messages: [
      { role: 'system', content: '你是专业的学术论文解读助手，用清晰的中文提供完整的论文分析。' },
      { role: 'user', content: interpretationPrompt }
    ],
    max_tokens: 2000,
    temperature: 0.7
  });
  
  const aiInterpretation = interpretationResponse.data.choices[0].message.content.trim();
  
  await updateTaskProgress(taskId, 90, 'processing');
  
  return {
    title_zh: titleZh,
    summary_zh: summaryZh,
    ai_interpretation: aiInterpretation,
    model_used: modelName
  };
};

/**
 * 客户端信息图生成
 */
const generateInfographicClient = async (
  paperId: string,
  modelName: string,
  apiService: any,
  customPrompt?: string,
  taskId?: string
): Promise<any> => {
  
  const paperResponse = await api.get(`/papers/${paperId}`);
  const paper = paperResponse.data;
  
  const infographicApi = axios.create({
    baseURL: apiService.baseUrl,
    headers: {
      'Authorization': `Bearer ${apiService.apiKey}`,
      'Content-Type': 'application/json'
    }
  });
  
  const prompt = customPrompt || `你是一个专业的学术信息可视化专家。请根据以下论文信息，生成一个视觉化的信息图网页。

论文标题：${paper.title}
论文摘要：${paper.summary}

要求：
1. **结构**：按照"问题→方法→结果"三段式组织
2. **技术**：使用纯 HTML + 内联 CSS，不依赖外部库
3. **风格**：
   - 深色主题（背景 #0f172a）
   - 使用渐变色和图标（Unicode emoji 或 CSS 绘制）
   - 卡片式布局，圆角阴影
4. **内容**：
   - 用简洁的中文描述（每段不超过 50 字）
   - 多用视觉元素：流程图、对比图、数据可视化
   - 关键数字和术语用醒目颜色标注
5. **移动端优化**：
   - viewport 设置为 width=device-width, initial-scale=1.0
   - 默认宽度 100%，最大宽度 600px，居中显示
   - 字体大小适合手机阅读（16px 基准）
   - 内边距使用 16-20px，适合手指触控
   - 垂直滚动，总高度约 1000-1400px（适配主流手机屏幕比例）
6. **布局**：优先为竖屏手机设计（9:16 或 9:19.5 比例）

直接输出完整的 HTML 代码，不要有任何解释文字。代码要完整可运行。`;
  
  if (taskId) await updateTaskProgress(taskId, 50, 'processing');
  
  const response = await infographicApi.post('/chat/completions', {
    model: modelName,
    messages: [
      { role: 'user', content: prompt }
    ],
    max_tokens: 4000,
    temperature: 0.7
  });
  
  const htmlContent = response.data.choices[0].message.content.trim();
  
  if (taskId) await updateTaskProgress(taskId, 90, 'processing');
  
  return {
    html_content: htmlContent,
    model_used: modelName
  };
};

/**
 * 客户端摘要生成
 */
const generateSummaryClient = async (
  paperId: string,
  modelName: string,
  apiService: any,
  taskId: string
): Promise<any> => {
  
  const paperResponse = await api.get(`/papers/${paperId}`);
  const paper = paperResponse.data;
  
  const summaryApi = axios.create({
    baseURL: apiService.baseUrl,
    headers: {
      'Authorization': `Bearer ${apiService.apiKey}`,
      'Content-Type': 'application/json'
    }
  });
  
  const prompt = `请为以下学术论文生成一个200字以内的中文摘要，要求简洁明了，突出核心贡献：

标题: ${paper.title}
摘要: ${paper.summary}

要求：
1. 200字以内
2. 突出核心创新点
3. 用通俗易懂的中文表达
4. 结构清晰，逻辑性强`;
  
  await updateTaskProgress(taskId, 50, 'processing');
  
  const response = await summaryApi.post('/chat/completions', {
    model: modelName,
    messages: [
      { role: 'system', content: '你是专业的学术论文摘要生成助手。' },
      { role: 'user', content: prompt }
    ],
    max_tokens: 500,
    temperature: 0.3
  });
  
  const summary = response.data.choices[0].message.content.trim();
  
  await updateTaskProgress(taskId, 90, 'processing');
  
  return {
    summary: summary,
    word_count: summary.length,
    model_used: modelName
  };
};

/**
 * 客户端TTS文本生成
 */
const generateTTSClient = async (
  paperId: string,
  modelName: string,
  apiService: any,
  taskId: string
): Promise<any> => {
  
  const paperResponse = await api.get(`/papers/${paperId}`);
  const paper = paperResponse.data;
  
  const ttsApi = axios.create({
    baseURL: apiService.baseUrl,
    headers: {
      'Authorization': `Bearer ${apiService.apiKey}`,
      'Content-Type': 'application/json'
    }
  });
  
  const prompt = `请将以下学术论文转换为适合语音播报的中文文本：

标题: ${paper.title}
摘要: ${paper.summary}

要求：
1. 用自然流畅的中文表达
2. 适合语音播报的节奏和停顿
3. 专业术语要有简单解释
4. 控制在300字以内
5. 包含标题、背景、方法、结果四个部分`;
  
  await updateTaskProgress(taskId, 50, 'processing');
  
  const response = await ttsApi.post('/chat/completions', {
    model: modelName,
    messages: [
      { role: 'system', content: '你是专业的语音文本转换助手。' },
      { role: 'user', content: prompt }
    ],
    max_tokens: 800,
    temperature: 0.5
  });
  
  const ttsText = response.data.choices[0].message.content.trim();
  
  await updateTaskProgress(taskId, 90, 'processing');
  
  return {
    tts_text: ttsText,
    estimated_duration: ttsText.length * 0.5,
    model_used: modelName
  };
};

/**
 * 上传客户端生成的内容
 */
export const uploadClientContent = async (taskId: string, contentData: any): Promise<void> => {
  await api.post('/v2/content/upload', {
    task_id: taskId,
    content_data: contentData
  });
};

/**
 * 查询任务状态
 */
export const getTaskStatus = async (taskId: string): Promise<TaskStatus> => {
  const response = await api.get(`/v2/content/task/${taskId}`);
  return response.data;
};

/**
 * 获取支持的内容类型
 */
export const getSupportedContentTypes = async (): Promise<any> => {
  const response = await api.get('/v2/content/supported-types');
  return response.data;
};
