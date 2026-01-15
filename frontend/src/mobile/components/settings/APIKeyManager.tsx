/**
 * Framework V2 API密钥管理组件 - 本地存储版本
 */

import React, { useState, useEffect } from 'react';
import { Key, Eye, EyeOff, Trash2, Plus, CheckCircle, XCircle, AlertTriangle, Loader2, ShieldCheck, Server } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { APIKeyService, APIKeyConfig } from '../../../services/apiKeyService';
import { AIService } from '../../../services/aiService';

interface APIKeyManagerProps {
  onKeysUpdated?: () => void;
  theme?: 'dark' | 'light';
}

interface ServiceConfig {
  name: string;
  description: string;
  configured: boolean;
}

const APIKeyManager: React.FC<APIKeyManagerProps> = ({ onKeysUpdated, theme = 'dark' }) => {
  const [services, setServices] = useState<Record<string, ServiceConfig>>({});
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedService, setSelectedService] = useState<string>('');
  const [apiKey, setApiKey] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<{ valid: boolean; message: string } | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const isDark = theme === 'dark';

  // 支持的服务配置
  const supportedServices = {
    deepseek: { name: 'DeepSeek', description: '用于生成信息图' },
    gemini: { name: 'Google Gemini', description: '用于生成可视化图' }
  };

  useEffect(() => {
    loadServices();
  }, []);

  const loadServices = async () => {
    try {
      setLoading(true);
      const configuredServices = APIKeyService.getConfiguredServices();

      const servicesMap: Record<string, ServiceConfig> = {};

      Object.entries(supportedServices).forEach(([serviceType, config]) => {
        servicesMap[serviceType] = {
          name: config.name,
          description: config.description,
          configured: configuredServices.includes(serviceType)
        };
      });

      setServices(servicesMap);
    } catch (error) {
      console.error('加载服务失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddKey = (serviceType?: string) => {
    setShowAddModal(true);
    setSelectedService(serviceType || '');
    setApiKey('');
    setValidationResult(null);
  };

  const handleValidateKey = async () => {
    if (!selectedService || !apiKey.trim()) return;

    try {
      setValidating(true);

      // 先验证格式
      const formatValid = APIKeyService.validateKeyFormat(selectedService as keyof APIKeyConfig, apiKey.trim());
      if (!formatValid) {
        setValidationResult({
          valid: false,
          message: 'API密钥格式不正确'
        });
        return;
      }

      // 直接验证密钥，不保存到存储
      let result;
      try {
        if (selectedService === 'deepseek') {
          const response = await fetch('https://api.deepseek.com/chat/completions', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${apiKey.trim()}`,
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
            result = {
              success: false,
              error: `DeepSeek API错误: ${response.status} - ${errorText}`
            };
          } else {
            result = { success: true };
          }
        } else if (selectedService === 'gemini') {
          const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${apiKey.trim()}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              contents: [{ parts: [{ text: 'Hi' }] }],
              generationConfig: { maxOutputTokens: 1 }
            })
          });

          if (!response.ok) {
            const errorText = await response.text();
            result = {
              success: false,
              error: `Gemini API错误: ${response.status} - ${errorText}`
            };
          } else {
            result = { success: true };
          }
        } else {
          result = {
            success: false,
            error: '不支持的服务类型'
          };
        }
      } catch (error) {
        result = {
          success: false,
          error: `网络错误: ${error instanceof Error ? error.message : '未知错误'}`
        };
      }

      setValidationResult({
        valid: result.success,
        message: result.success ? 'API密钥验证成功' : result.error || '密钥验证失败'
      });
    } catch (error) {
      setValidationResult({
        valid: false,
        message: '验证失败，请检查网络连接'
      });
    } finally {
      setValidating(false);
    }
  };

  const handleSubmitKey = async () => {
    if (!selectedService || !apiKey.trim() || !validationResult?.valid) return;

    try {
      setSubmitting(true);
      APIKeyService.saveAPIKey(selectedService as keyof APIKeyConfig, apiKey.trim());

      setShowAddModal(false);
      await loadServices();
      onKeysUpdated?.();
    } catch (error) {
      console.error('保存密钥失败:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteKey = async (serviceType: string) => {
    if (!confirm(`确定要删除 ${serviceType} 的API密钥吗？`)) return;

    try {
      APIKeyService.removeAPIKey(serviceType as keyof APIKeyConfig);
      await loadServices();
      onKeysUpdated?.();
    } catch (error) {
      console.error('删除密钥失败:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-12 space-y-4">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
        <span className={isDark ? 'text-gray-400' : 'text-gray-500'}>安全环境加载中...</span>
      </div>
    );
  }

  // Styles
  const cardStyle = `p-4 rounded-xl border transition-all ${isDark ? 'bg-gray-800/40 border-white/5' : 'bg-white border-gray-100 shadow-sm'}`;

  return (
    <div className="space-y-6 pb-20">
      {/* Header Info */}
      <div className={`p-4 rounded-xl border ${isDark ? 'bg-blue-900/10 border-blue-500/20' : 'bg-blue-50 border-blue-100'}`}>
        <div className="flex gap-3">
          <ShieldCheck className="w-5 h-5 text-blue-500 shrink-0 mt-0.5" />
          <div className="text-xs leading-relaxed space-y-1">
            <p className={`font-bold ${isDark ? 'text-blue-200' : 'text-blue-800'}`}>
              本地安全存储
            </p>
            <p className={isDark ? 'text-blue-400/80' : 'text-blue-600/80'}>
              密钥仅保存在您的本地客户端中，不会上传到服务器。通过安全通道直连AI服务商。
            </p>
          </div>
        </div>
      </div>

      {/* Services List */}
      <div className="grid gap-4">
        {Object.entries(services).map(([serviceType, config]) => (
          <motion.div
            key={serviceType}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={cardStyle}
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${isDark ? 'bg-white/5' : 'bg-gray-100'}`}>
                  <Server size={18} className={isDark ? 'text-gray-300' : 'text-gray-600'} />
                </div>
                <div>
                  <h3 className={`font-bold text-sm ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>{config.name}</h3>
                  <p className="text-[10px] text-gray-500">{config.description}</p>
                </div>
              </div>

              {config.configured ? (
                <div className="flex items-center gap-2">
                  <span className="flex items-center gap-1 text-[10px] font-bold text-green-500 bg-green-500/10 px-2 py-0.5 rounded-full">
                    <CheckCircle size={10} /> 已配置
                  </span>
                  <button
                    onClick={() => handleDeleteKey(serviceType)}
                    className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-colors"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => handleAddKey(serviceType)}
                  className="text-xs font-bold text-blue-500 hover:bg-blue-500/10 px-3 py-1.5 rounded-lg transition-colors"
                >
                  配置
                </button>
              )}
            </div>
          </motion.div>
        ))}
      </div>

      {/* Floating Add Button */}
      {!showAddModal && (
        <div className="fixed bottom-6 right-6 z-10">
          <button
            onClick={() => handleAddKey()}
            className="w-14 h-14 bg-blue-600 text-white rounded-full shadow-lg shadow-blue-600/30 flex items-center justify-center hover:scale-105 active:scale-95 transition-all"
          >
            <Plus size={24} />
          </button>
        </div>
      )}

      {/* Add Key Modal */}
      <AnimatePresence>
        {showAddModal && (
          <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center sm:p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => setShowAddModal(false)}
            />

            <motion.div
              initial={{ y: '100%' }}
              animate={{ y: 0 }}
              exit={{ y: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              className={`relative w-full sm:max-w-md rounded-t-3xl sm:rounded-3xl p-6 ${isDark ? 'bg-gray-900 border-t border-white/10' : 'bg-white'} shadow-2xl max-h-[90vh] overflow-y-auto`}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="w-12 h-1 bg-gray-300/20 rounded-full mx-auto mb-6 sm:hidden" />

              <h3 className={`text-xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                {selectedService ? `配置 ${supportedServices[selectedService as keyof typeof supportedServices]?.name} API 密钥` : '添加 API 密钥'}
              </h3>

              <div className="space-y-4">
                {/* Service Select - 只在没有预选服务时显示 */}
                {!selectedService && (
                  <div>
                    <label className={`block text-xs font-bold mb-2 ml-1 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>选择服务商</label>
                    <div className="grid grid-cols-2 gap-2">
                      {Object.entries(services)
                        .filter(([_, config]) => !config.configured)
                        .map(([serviceType, config]) => (
                          <div
                            key={serviceType}
                            onClick={() => {
                              setSelectedService(serviceType);
                              setValidationResult(null);
                            }}
                            className={`p-3 rounded-xl border text-center cursor-pointer transition-all ${selectedService === serviceType
                              ? 'border-blue-500 bg-blue-500/10 text-blue-500'
                              : (isDark ? 'border-gray-700 bg-gray-800 text-gray-400' : 'border-gray-200 bg-gray-50 text-gray-600')
                              }`}
                          >
                            <span className="text-sm font-bold">{config.name}</span>
                          </div>
                        ))}
                    </div>
                  </div>
                )}

                {/* 显示已选择的服务商 */}
                {selectedService && (
                  <div className={`p-3 rounded-xl border ${isDark ? 'border-blue-500/30 bg-blue-500/10' : 'border-blue-200 bg-blue-50'}`}>
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full bg-blue-500`}></div>
                      <span className={`text-sm font-bold ${isDark ? 'text-blue-300' : 'text-blue-700'}`}>
                        {supportedServices[selectedService as keyof typeof supportedServices]?.name}
                      </span>
                    </div>
                  </div>
                )}

                {/* API Key Input */}
                <div>
                  <label className={`block text-xs font-bold mb-2 ml-1 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>API密钥</label>
                  <div className="relative">
                    <input
                      type={showKey ? 'text' : 'password'}
                      value={apiKey}
                      onChange={(e) => {
                        setApiKey(e.target.value);
                        setValidationResult(null);
                      }}
                      className={`w-full p-4 pr-12 rounded-xl text-sm font-mono outline-none border transition-colors ${isDark
                        ? 'bg-black/40 border-gray-700 focus:border-blue-500 text-white placeholder-gray-600'
                        : 'bg-gray-50 border-gray-200 focus:border-blue-500 text-gray-900'
                        }`}
                      placeholder="输入API密钥..."
                    />
                    <button
                      type="button"
                      onClick={() => setShowKey(!showKey)}
                      className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-blue-500"
                    >
                      {showKey ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                </div>

                {/* Validation Status */}
                <AnimatePresence>
                  {validationResult && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className={`overflow-hidden rounded-xl ${validationResult.valid
                        ? 'bg-green-500/10 text-green-500'
                        : 'bg-red-500/10 text-red-500'
                        }`}
                    >
                      <div className="p-3 flex items-center gap-2 text-sm font-bold">
                        {validationResult.valid ? <CheckCircle size={16} /> : <XCircle size={16} />}
                        {validationResult.message}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Actions */}
                <div className="pt-4 flex gap-3">
                  <button
                    onClick={() => setShowAddModal(false)}
                    className={`flex-1 py-3 rounded-xl font-bold text-sm ${isDark ? 'bg-gray-800 text-gray-400' : 'bg-gray-100 text-gray-600'}`}
                  >
                    取消
                  </button>

                  {!validationResult?.valid ? (
                    <button
                      onClick={handleValidateKey}
                      disabled={!selectedService || !apiKey.trim() || validating}
                      className="flex-1 py-3 bg-blue-600 text-white rounded-xl font-bold text-sm flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {validating && <Loader2 size={16} className="animate-spin" />}
                      验证密钥
                    </button>
                  ) : (
                    <button
                      onClick={handleSubmitKey}
                      disabled={submitting}
                      className="flex-1 py-3 bg-green-600 text-white rounded-xl font-bold text-sm flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                      {submitting && <Loader2 size={16} className="animate-spin" />}
                      确认保存
                    </button>
                  )}
                </div>
              </div>

            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default APIKeyManager;
