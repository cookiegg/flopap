/**
 * Framework V2 推荐设置组件 - Glassmorphism Redesign
 */

import React, { useState, useEffect } from 'react';
import { Settings, Sliders, Zap, Brain, Save, Loader2, CheckCircle, Info } from 'lucide-react';
import { motion } from 'framer-motion';
import {
  getRecommendationSettings,
  updateRecommendationSettings,
  getAvailableModels,
  type RecommendationSettings,
  type AvailableModel
} from '../../../services/recommendationService';

interface RecommendationSettingsProps {
  onSettingsUpdated?: (settings: RecommendationSettings) => void;
  theme?: 'dark' | 'light';
}

const RecommendationSettings: React.FC<RecommendationSettingsProps> = ({
  onSettingsUpdated,
  theme = 'dark'
}) => {
  const [settings, setSettings] = useState<RecommendationSettings>({
    arxiv_ratio: 10,
    conference_ratio: 20,
    max_pool_size: 50,
    enable_auto_generation: false,
    preferred_models: []
  });
  const [availableModels, setAvailableModels] = useState<Record<string, AvailableModel>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const isDark = theme === 'dark';

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [settingsData, modelsData] = await Promise.all([
        getRecommendationSettings(),
        getAvailableModels()
      ]);

      setSettings({
        arxiv_ratio: settingsData.arxiv_ratio,
        conference_ratio: settingsData.conference_ratio,
        max_pool_size: settingsData.max_pool_size,
        enable_auto_generation: settingsData.enable_auto_generation,
        preferred_models: settingsData.preferred_models
      });
      setAvailableModels(modelsData.models);
    } catch (error) {
      console.error('加载设置失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      await updateRecommendationSettings(settings);
      setSaved(true);
      onSettingsUpdated?.(settings);

      // 3秒后隐藏保存成功提示
      setTimeout(() => setSaved(false), 3000);
    } catch (error) {
      console.error('保存设置失败:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleSliderChange = (key: keyof RecommendationSettings, value: number) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  const handleModelToggle = (modelKey: string) => {
    setSettings(prev => ({
      ...prev,
      preferred_models: prev.preferred_models.includes(modelKey)
        ? prev.preferred_models.filter(m => m !== modelKey)
        : [...prev.preferred_models, modelKey]
    }));
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-12 space-y-4">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
        <span className={isDark ? 'text-gray-400' : 'text-gray-500'}>加载配置中...</span>
      </div>
    );
  }

  // Common styles
  const cardStyle = `p-5 rounded-2xl border transition-all ${isDark ? 'bg-gray-800/40 border-white/5' : 'bg-white border-gray-100 shadow-sm'}`;
  const labelStyle = `text-sm font-bold mb-3 flex items-center gap-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`;

  return (
    <div className="space-y-6 pb-20">

      {/* 1. Ratio Sliders */}
      <section className={cardStyle}>
        <h3 className={labelStyle}>
          <Sliders className="w-4 h-4 text-purple-500" />
          推荐内容配比
        </h3>

        <div className="space-y-6">
          {/* ArXiv Ratio */}
          <div>
            <div className="flex justify-between text-xs mb-2">
              <span className={isDark ? 'text-gray-400' : 'text-gray-500'}>arXiv 最新论文</span>
              <span className="font-mono font-bold text-purple-500">{settings.arxiv_ratio}%</span>
            </div>
            <input
              type="range"
              min="1"
              max="50"
              value={settings.arxiv_ratio}
              onChange={(e) => handleSliderChange('arxiv_ratio', parseInt(e.target.value))}
              className="w-full h-1.5 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-purple-500"
            />
          </div>

          {/* Conference Ratio */}
          <div>
            <div className="flex justify-between text-xs mb-2">
              <span className={isDark ? 'text-gray-400' : 'text-gray-500'}>顶级会议论文 (CVPR/ICCV...)</span>
              <span className="font-mono font-bold text-blue-500">{settings.conference_ratio}%</span>
            </div>
            <input
              type="range"
              min="1"
              max="50"
              value={settings.conference_ratio}
              onChange={(e) => handleSliderChange('conference_ratio', parseInt(e.target.value))}
              className="w-full h-1.5 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
            />
          </div>


        </div>
      </section>

      {/* 2. Auto Generation Toggle */}
      <section className={cardStyle}>
        <div className="flex items-center justify-between">
          <div>
            <h3 className={`font-bold text-sm ${isDark ? 'text-white' : 'text-gray-900'}`}>智能内容生成</h3>
            <p className="text-xs text-gray-500 mt-1">自动生成 AI 信息图/可视化解读, 耗费较大,谨慎操作</p>
          </div>

          <button
            onClick={() => setSettings(prev => ({ ...prev, enable_auto_generation: !prev.enable_auto_generation }))}
            className={`w-12 h-7 rounded-full p-1 transition-colors duration-300 ${settings.enable_auto_generation ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'}`}
          >
            <motion.div
              layout
              className="w-5 h-5 bg-white rounded-full shadow-md"
              animate={{ x: settings.enable_auto_generation ? 20 : 0 }}
            />
          </button>
        </div>
      </section>

      {/* 3. Model Preference */}
      <section>
        <h3 className={`text-xs font-bold uppercase tracking-wider mb-3 px-1 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
          优先使用模型
        </h3>
        <div className="grid grid-cols-1 gap-3">
          {Object.entries(availableModels).map(([modelKey, model]) => {
            const isSelected = settings.preferred_models.includes(modelKey);
            return (
              <motion.div
                key={modelKey}
                onClick={() => handleModelToggle(modelKey)}
                whileTap={{ scale: 0.98 }}
                className={`p-4 rounded-xl border cursor-pointer relative transition-all duration-200 ${isSelected
                  ? (isDark
                    ? 'bg-blue-900/20 border-blue-500/50 shadow-[0_0_15px_rgba(59,130,246,0.15)]'
                    : 'bg-blue-50 border-blue-500 shadow-sm')
                  : cardStyle
                  }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <span className={`font-bold text-sm ${isSelected ? 'text-blue-500' : (isDark ? 'text-white' : 'text-gray-900')}`}>
                      {model.name}
                    </span>
                    {isSelected && <CheckCircle size={14} className="text-blue-500" />}
                  </div>
                  <span className="text-[10px] font-mono text-gray-400">
                    {model.provider}
                  </span>
                </div>

                <p className={`text-xs leading-relaxed mb-3 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                  {model.description}
                </p>

                <div className={`flex items-center gap-1.5 text-[10px] font-medium px-2 py-1 rounded w-fit ${isDark ? 'bg-black/20 text-gray-400' : 'bg-gray-100 text-gray-600'
                  }`}>
                  <span>¥ {(model.cost_per_1k_tokens * 7.2).toFixed(4)} / 1k tokens</span>
                </div>
              </motion.div>
            );
          })}
        </div>
      </section>

      {/* Floating Save Button */}
      <div className="fixed bottom-24 left-0 right-0 z-20 px-6 mx-auto max-w-md md:max-w-2xl pointer-events-none">
        <button
          onClick={handleSave}
          disabled={saving}
          className="w-full py-3.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-bold shadow-lg shadow-blue-900/20 flex items-center justify-center gap-2 disabled:opacity-70 active:scale-95 transition-transform pointer-events-auto"
        >
          {saving ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              正在保存...
            </>
          ) : saved ? (
            <>
              <CheckCircle className="w-5 h-5" />
              已保存
            </>
          ) : (
            <>
              <Save className="w-5 h-5" />
              保存设置
            </>
          )}
        </button>
      </div>

      {/* spacer for fixed footer */}
      <div className="h-20" />
    </div>
  );
};

export default RecommendationSettings;
