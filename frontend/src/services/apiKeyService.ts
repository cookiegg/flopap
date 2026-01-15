/**
 * 客户端API密钥安全存储服务
 */

import SecureStorage from './secureStorage';

export interface APIKeyConfig {
  deepseek?: string;
  gemini?: string;
  openai?: string;
  dashscope?: string;
}

export interface UsageStats {
  [service: string]: {
    usage_count: number;
    last_used_at: string | null;
    created_at: string;
  };
}

export class APIKeyService {
  private static readonly STORAGE_KEY = 'flopap_api_keys';
  private static readonly USAGE_STATS_KEY = 'flopap_api_usage_stats';

  /**
   * 获取指定服务的API密钥 - 同步版本用于验证
   */
  static getAPIKey(service: keyof APIKeyConfig): string | null {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY);
      const keys = stored ? JSON.parse(stored) : {};
      return keys[service] || null;
    } catch (error) {
      console.error('Failed to get API key:', error);
      return null;
    }
  }

  /**
   * 获取所有API密钥 - 同步版本
   */
  static getAllAPIKeys(): APIKeyConfig {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY);
      return stored ? JSON.parse(stored) : {};
    } catch (error) {
      console.error('Failed to get API keys:', error);
      return {};
    }
  }

  /**
   * 保存API密钥 - 同步版本
   */
  static saveAPIKey(service: keyof APIKeyConfig, apiKey: string): void {
    const keys = this.getAllAPIKeys();
    keys[service] = apiKey;
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(keys));
    
    // 初始化使用统计
    this.initUsageStats(service);
  }

  /**
   * 删除指定服务的API密钥
   */
  static removeAPIKey(service: keyof APIKeyConfig): void {
    const keys = this.getAllAPIKeys();
    delete keys[service];
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(keys));
    
    // 删除使用统计
    this.removeUsageStats(service);
  }

  /**
   * 清除所有API密钥
   */
  static clearAllAPIKeys(): void {
    localStorage.removeItem(this.STORAGE_KEY);
    localStorage.removeItem(this.USAGE_STATS_KEY);
  }

  /**
   * 获取已配置的服务列表
   */
  static getConfiguredServices(): string[] {
    const keys = this.getAllAPIKeys();
    return Object.keys(keys).filter(service => keys[service as keyof APIKeyConfig]);
  }

  /**
   * 验证API密钥格式
   */
  static validateKeyFormat(service: keyof APIKeyConfig, apiKey: string): boolean {
    if (!apiKey || apiKey.trim().length === 0) return false;
    
    switch (service) {
      case 'deepseek':
        return apiKey.startsWith('sk-');
      case 'openai':
        return apiKey.startsWith('sk-');
      case 'gemini':
        return apiKey.length > 20; // Gemini keys are typically longer
      case 'dashscope':
        return apiKey.length > 20; // DashScope keys
      default:
        return false;
    }
  }

  /**
   * 初始化使用统计
   */
  private static initUsageStats(service: string): void {
    const stats = this.getUsageStats();
    if (!stats[service]) {
      stats[service] = {
        usage_count: 0,
        last_used_at: null,
        created_at: new Date().toISOString()
      };
      localStorage.setItem(this.USAGE_STATS_KEY, JSON.stringify(stats));
    }
  }

  /**
   * 删除使用统计
   */
  private static removeUsageStats(service: string): void {
    const stats = this.getUsageStats();
    delete stats[service];
    localStorage.setItem(this.USAGE_STATS_KEY, JSON.stringify(stats));
  }

  /**
   * 获取使用统计
   */
  static getUsageStats(): UsageStats {
    try {
      const stored = localStorage.getItem(this.USAGE_STATS_KEY);
      return stored ? JSON.parse(stored) : {};
    } catch {
      return {};
    }
  }

  /**
   * 更新使用统计
   */
  static updateUsageStats(service: string): void {
    const stats = this.getUsageStats();
    if (stats[service]) {
      stats[service].usage_count += 1;
      stats[service].last_used_at = new Date().toISOString();
      localStorage.setItem(this.USAGE_STATS_KEY, JSON.stringify(stats));
    }
  }
}

// 导出兼容函数
export const getUsageStats = () => APIKeyService.getUsageStats();
export const getConfiguredServices = () => APIKeyService.getConfiguredServices();
