/**
 * Framework V2 用户设置扩展组件 - Glassmorphism Redesign
 * 集成到现有的用户资料界面中
 */

import React, { useState } from 'react';
import { Key, Settings, BarChart3, ChevronRight, Zap, ArrowLeft, Shield, Sparkles } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import APIKeyManager from './APIKeyManager';
import UserDashboard from './UserDashboard';

interface UserSettingsV2Props {
  theme?: 'dark' | 'light';
  language?: 'en' | 'zh';
}

type SettingsSection = 'main' | 'api-keys' | 'recommendation' | 'dashboard';

const UserSettings: React.FC<UserSettingsV2Props> = ({ theme = 'dark', language = 'en' }) => {
  const [activeSection, setActiveSection] = useState<SettingsSection>('main');

  const isDark = theme === 'dark';

  // Glassmorphism Styles
  const glassCard = isDark
    ? 'bg-gray-900/40 backdrop-blur-xl border-white/5 shadow-xl'
    : 'bg-white/60 backdrop-blur-xl border-gray-200/50 shadow-lg';

  const glassHover = isDark
    ? 'hover:bg-gray-800/60'
    : 'hover:bg-white/80';

  const settingsItems = [
    {
      key: 'api-keys',
      title: 'API 密钥管理',
      subtitle: '自定义 AI 服务密钥',
      icon: Key,
      color: 'text-blue-400',
      bgGradient: 'from-blue-500/20 to-blue-600/5'
    },
    {
      key: 'dashboard',
      title: '使用统计',
      subtitle: '查看 API 消耗与生成记录',
      icon: BarChart3,
      color: 'text-orange-400',
      bgGradient: 'from-orange-500/20 to-orange-600/5'
    }
  ];

  return (
    <div className="w-full h-full relative overflow-hidden">
      <AnimatePresence mode="wait">
        {activeSection === 'main' ? (
          <motion.div
            key="main"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            {/* Header Card */}
            <div className={`p-6 rounded-3xl border ${glassCard} relative overflow-hidden group`}>
              <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/20 blur-[50px] rounded-full group-hover:bg-purple-500/30 transition-colors" />
              <div className="relative z-10">
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 text-white shadow-lg">
                    <Zap size={20} fill="currentColor" />
                  </div>
                  <h3 className={`text-lg font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>AI 助手增强</h3>
                </div>
                <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  配置专属 API 密钥，解锁 GPT-4 等高级模型，享受更精准的个性化推荐与深度解读。
                </p>
              </div>
            </div>

            {/* Settings Grid */}
            <div className="grid gap-3">
              {settingsItems.map((item) => {
                const Icon = item.icon;
                return (
                  <motion.button
                    key={item.key}
                    onClick={() => setActiveSection(item.key as SettingsSection)}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className={`flex items-center p-4 rounded-2xl border text-left transition-all group ${glassCard} ${glassHover} ${isDark ? 'border-white/5' : 'border-gray-200'}`}
                  >
                    <div className={`p-3 rounded-xl bg-gradient-to-br ${item.bgGradient} mr-4 group-hover:scale-110 transition-transform`}>
                      <Icon className={`w-5 h-5 ${item.color}`} />
                    </div>

                    <div className="flex-1 min-w-0">
                      <h4 className={`font-bold text-sm mb-0.5 ${isDark ? 'text-white' : 'text-gray-900'}`}>{item.title}</h4>
                      <p className={`text-xs truncate ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>{item.subtitle}</p>
                    </div>

                    <ChevronRight className={`w-5 h-5 ${isDark ? 'text-gray-600 group-hover:text-white' : 'text-gray-400 group-hover:text-gray-900'} transition-colors`} />
                  </motion.button>
                );
              })}
            </div>

            {/* Security Badge */}
            <div className={`p-4 rounded-2xl flex items-start gap-3 border ${isDark ? 'bg-blue-900/10 border-blue-800/30' : 'bg-blue-50 border-blue-100'}`}>
              <Shield className="w-5 h-5 text-blue-500 shrink-0 mt-0.5" />
              <div className="text-xs">
                <p className={`font-bold mb-1 ${isDark ? 'text-blue-200' : 'text-blue-800'}`}>安全承诺</p>
                <p className={isDark ? 'text-blue-400/80' : 'text-blue-600/80'}>
                  您的 API 密钥仅存储在本地设备，通过加密传输直接与服务商通信，绝不会上传至我们的服务器。
                </p>
              </div>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="sublevel"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="h-full flex flex-col"
          >
            {/* Subpage Header */}
            <div className="flex items-center gap-2 mb-6 shrink-0">
              <button
                onClick={() => setActiveSection('main')}
                className={`p-2 rounded-full hover:bg-white/10 transition-colors ${isDark ? 'text-white' : 'text-gray-900'}`}
              >
                <ArrowLeft size={20} />
              </button>
              <h3 className={`text-lg font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                {settingsItems.find(i => i.key === activeSection)?.title || '设置'}
              </h3>
            </div>

            {/* Subpage Content */}
            <div className="flex-1 overflow-y-auto no-scrollbar -mx-2 px-2 pb-20">
              {activeSection === 'api-keys' && (
                <APIKeyManager
                  theme={theme}
                  onKeysUpdated={() => {
                    console.log('API keys updated');
                  }}
                />
              )}

              {activeSection === 'dashboard' && (
                <UserDashboard theme={theme} />
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default UserSettings;
