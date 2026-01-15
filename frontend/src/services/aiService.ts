/**
 * 客户端AI服务调用
 */

import { APIKeyService } from './apiKeyService';

export interface GenerationRequest {
  prompt: string;
  service: 'deepseek' | 'gemini' | 'openai' | 'dashscope';
  maxTokens?: number;
}

export interface GenerationResponse {
  content: string;
  success: boolean;
  error?: string;
}

export class AIService {

  /**
   * 生成AI内容
   */
  static async generateContent(request: GenerationRequest): Promise<GenerationResponse> {
    const apiKey = APIKeyService.getAPIKey(request.service);

    if (!apiKey) {
      return {
        content: '',
        success: false,
        error: `请先配置 ${request.service} API密钥`
      };
    }

    try {
      let result: GenerationResponse;

      switch (request.service) {
        case 'deepseek':
          // 对于验证请求，使用简单的测试
          if (request.prompt === 'test') {
            result = await this.callDeepSeekValidation(apiKey);
          } else {
            // 实际使用时使用deepseek-reasoner
            result = await this.callDeepSeek(apiKey, request.prompt, request.maxTokens, 'deepseek-reasoner');
          }
          break;
        case 'gemini':
          // For validation (prompt === 'test'), use fast text model to verify API key
          if (request.prompt === 'test') {
            result = await this.callGeminiValidation(apiKey);
          } else {
            // For text generation, use standard gemini model
            result = await this.callGemini(apiKey, request.prompt, request.maxTokens);
          }
          break;
        case 'openai':
          result = await this.callOpenAI(apiKey, request.prompt, request.maxTokens);
          break;
        case 'dashscope':
          result = await this.callDashScope(apiKey, request.prompt, request.maxTokens);
          break;
        default:
          return {
            content: '',
            success: false,
            error: '不支持的AI服务'
          };
      }

      // 如果调用成功，更新使用统计
      if (result.success) {
        APIKeyService.updateUsageStats(request.service);
      }

      return result;
    } catch (error) {
      return {
        content: '',
        success: false,
        error: `AI服务调用失败: ${error instanceof Error ? error.message : '未知错误'}`
      };
    }
  }

  /** 快速验证DeepSeek API密钥 */
  private static async callDeepSeekValidation(apiKey: string): Promise<GenerationResponse> {
    const response = await fetch('https://api.deepseek.com/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'deepseek-chat',
        messages: [{ role: 'user', content: 'Hi' }],
        max_tokens: 1,
        stream: false
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`DeepSeek API错误: ${response.status} - ${errorText}`);
    }

    return { content: 'DeepSeek API密钥验证成功', success: true };
  }

  private static async callDeepSeek(apiKey: string, prompt: string, maxTokens = 4000, model = 'deepseek-chat'): Promise<GenerationResponse> {
    const response = await fetch('https://api.deepseek.com/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: model,
        messages: [{ role: 'user', content: prompt }],
        max_tokens: maxTokens,
        stream: false
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`DeepSeek API错误: ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    let content = data.choices[0]?.message?.content || '';

    // Check for reasoning content if available (usually in separate field or inside <think>)
    // DeepSeek R1 returns <think> tags in content sometimes or reasoning_content field.
    // If <think> tags exist, we should probably strip them for the final output usage (Infographic HTML).
    content = content.replace(/<think>[\s\S]*?<\/think>/gi, '').trim();

    // Strip markdown code blocks (```html ... ``` or ``` ... ```)
    const codeBlockMatch = content.match(/```(?:html)?\s*([\s\S]*?)```/i);
    if (codeBlockMatch) {
      content = codeBlockMatch[1].trim();
    }

    return {
      content: content,
      success: true
    };
  }

  private static async callGemini(apiKey: string, prompt: string, maxTokens = 2000): Promise<GenerationResponse> {
    // Standard Gemini Text Generation
    const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key=${apiKey}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }], generationConfig: { maxOutputTokens: maxTokens } })
    });
    if (!response.ok) throw new Error(`Gemini API错误: ${response.status}`);
    const data = await response.json();
    return { content: data.candidates[0]?.content?.parts[0]?.text || '', success: true };
  }

  /** Fast validation using gemini-2.5-flash (responds in ~1 second) */
  private static async callGeminiValidation(apiKey: string): Promise<GenerationResponse> {
    const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${apiKey}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ parts: [{ text: 'Respond with OK' }] }],
        generationConfig: { maxOutputTokens: 10 }
      })
    });

    if (!response.ok) {
      const errText = await response.text();
      throw new Error(`Gemini API错误: ${response.status} - ${errText}`);
    }

    return { content: 'Gemini API密钥验证成功', success: true };
  }

  private static async callOpenAI(apiKey: string, prompt: string, maxTokens = 2000): Promise<GenerationResponse> {
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'gpt-3.5-turbo',
        messages: [{ role: 'user', content: prompt }],
        max_tokens: maxTokens
      })
    });

    if (!response.ok) {
      throw new Error(`OpenAI API错误: ${response.status}`);
    }

    const data = await response.json();
    return {
      content: data.choices[0]?.message?.content || '',
      success: true
    };
  }

  private static async callDashScope(apiKey: string, prompt: string, maxTokens = 2000): Promise<GenerationResponse> {
    const response = await fetch('https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'qwen-turbo',
        input: {
          messages: [{ role: 'user', content: prompt }]
        },
        parameters: {
          max_tokens: maxTokens
        }
      })
    });

    if (!response.ok) {
      throw new Error(`DashScope API错误: ${response.status}`);
    }

    const data = await response.json();
    return {
      content: data.output?.text || '',
      success: true
    };
  }
  /**
   * 生成图片 (可视化图)
   */
  static async generateImage(request: GenerationRequest): Promise<GenerationResponse> {
    const apiKey = APIKeyService.getAPIKey(request.service);
    if (!apiKey) return { content: '', success: false, error: `请先配置 ${request.service} API密钥` };

    try {
      if (request.service === 'gemini') {
        return await this.callGeminiImage(apiKey, request.prompt);
      }
      return { content: '', success: false, error: '该服务不支持图片生成' };
    } catch (error) {
      return { content: '', success: false, error: `图片生成失败: ${error instanceof Error ? error.message : '未知错误'}` };
    }
  }

  // ... (existing helper methods) ...

  // 添加 callGeminiImage
  private static async callGeminiImage(apiKey: string, prompt: string): Promise<GenerationResponse> {
    // Calling gemini-3-pro-image-preview
    // User docs show usage of @google/genai client, which uses new API version (v1beta or v1alpha).
    // The "gemini-3-pro-image-preview" model specifically supports image generation.
    // REST Endpoint: https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image-preview:generateContent

    const response = await fetch('https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image-preview:generateContent', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-goog-api-key': apiKey
      },
      body: JSON.stringify({
        contents: [{
          parts: [{ text: prompt }]
        }],
        tools: [{ googleSearch: {} }],
        generationConfig: {
          imageConfig: {
            aspectRatio: "16:9",
            imageSize: "1K"
          }
        }
      })
    });

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Gemini Image API Error: ${response.status} - ${err}`);
    }

    const data = await response.json();

    // Parse response for Image Data
    // SDK example: response.candidates[0].content.parts[n].inlineData.data
    const parts = data.candidates?.[0]?.content?.parts || [];
    let imageBase64 = null;
    let mimeType = 'image/png'; // default

    for (const part of parts) {
      if (part.inlineData) {
        imageBase64 = part.inlineData.data;
        mimeType = part.inlineData.mimeType || mimeType;
        break;
      }
    }

    if (imageBase64) {
      return {
        content: `data:${mimeType};base64,${imageBase64}`,
        success: true
      };
    } else {
      // Check for text error or rejection
      const text = parts.find((p: any) => p.text)?.text;
      if (text) return { content: '', success: false, error: `模型只返回了文本: ${text}` };
      return { content: '', success: false, error: '未生成图片数据' };
    }
  }
}
