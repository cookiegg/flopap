/**
 * 统一错误处理服务
 */

export interface ErrorInfo {
  code: string;
  message: string;
  solution?: string;
  retryable: boolean;
}

export class ErrorHandler {
  private static readonly ERROR_MESSAGES: Record<string, ErrorInfo> = {
    'API_KEY_MISSING': {
      code: 'API_KEY_MISSING',
      message: '请先配置API密钥',
      solution: '前往设置页面添加您的AI服务API密钥',
      retryable: false
    },
    'API_KEY_INVALID': {
      code: 'API_KEY_INVALID',
      message: 'API密钥无效',
      solution: '请检查API密钥格式是否正确',
      retryable: false
    },
    'NETWORK_ERROR': {
      code: 'NETWORK_ERROR',
      message: '网络连接失败',
      solution: '请检查网络连接后重试',
      retryable: true
    },
    'RATE_LIMIT': {
      code: 'RATE_LIMIT',
      message: 'API调用频率过高',
      solution: '请稍后再试',
      retryable: true
    },
    'QUOTA_EXCEEDED': {
      code: 'QUOTA_EXCEEDED',
      message: 'API配额已用完',
      solution: '请检查您的API账户余额',
      retryable: false
    },
    'GENERATION_FAILED': {
      code: 'GENERATION_FAILED',
      message: '内容生成失败',
      solution: '请重试或更换AI模型',
      retryable: true
    }
  };

  static handleError(error: any): ErrorInfo {
    // 网络错误
    if (error.code === 'NETWORK_ERROR' || !navigator.onLine) {
      return this.ERROR_MESSAGES.NETWORK_ERROR;
    }

    // HTTP状态码错误
    if (error.response?.status) {
      const status = error.response.status;
      if (status === 401) return this.ERROR_MESSAGES.API_KEY_INVALID;
      if (status === 429) return this.ERROR_MESSAGES.RATE_LIMIT;
      if (status === 402) return this.ERROR_MESSAGES.QUOTA_EXCEEDED;
    }

    // API错误消息
    const message = error.response?.data?.error?.message || error.message || '';
    if (message.includes('API key')) return this.ERROR_MESSAGES.API_KEY_INVALID;
    if (message.includes('rate limit')) return this.ERROR_MESSAGES.RATE_LIMIT;
    if (message.includes('quota')) return this.ERROR_MESSAGES.QUOTA_EXCEEDED;

    // 默认错误
    return this.ERROR_MESSAGES.GENERATION_FAILED;
  }

  static async retryWithBackoff<T>(
    fn: () => Promise<T>,
    maxRetries: number = 3,
    baseDelay: number = 1000
  ): Promise<T> {
    let lastError: any;
    
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error;
        const errorInfo = this.handleError(error);
        
        if (!errorInfo.retryable || attempt === maxRetries) {
          throw error;
        }
        
        const delay = baseDelay * Math.pow(2, attempt);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
    
    throw lastError;
  }

  static showUserFriendlyError(error: any): void {
    const errorInfo = this.handleError(error);
    
    // 这里可以集成toast通知或其他UI组件
    console.error('User-friendly error:', {
      message: errorInfo.message,
      solution: errorInfo.solution,
      retryable: errorInfo.retryable
    });
    
    // 可以触发全局错误状态更新
    window.dispatchEvent(new CustomEvent('app-error', {
      detail: errorInfo
    }));
  }
}

export default ErrorHandler;
