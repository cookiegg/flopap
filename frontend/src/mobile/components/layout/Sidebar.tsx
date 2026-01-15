
import React, { useState, useEffect } from 'react';
import { DataSource, AppLanguage, AppTheme, ArxivSubSource, DataSourceInfo } from '../../../types';
import { UI_STRINGS } from '../../../constants';
import { getDataSources } from '../../../services/dataSourceService';
import { X, Flame, Layers, Globe, Moon, Sun, ChevronDown, ChevronRight, Calendar, History, Activity, BookOpen, Share2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Share } from '@capacitor/share';
import { Capacitor } from '@capacitor/core';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  currentSource: DataSource;
  onSelectSource: (source: DataSource) => void;
  arxivSub: ArxivSubSource;
  onSelectArxivSub: (sub: ArxivSubSource) => void;
  language: AppLanguage;
  onToggleLanguage: () => void;
  theme: AppTheme;
  onToggleTheme: () => void;
  activeTab?: 'feed' | 'profile';
  onNavigate?: (tab: 'feed' | 'profile') => void;
  onFactoryClick?: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  onClose,
  currentSource,
  onSelectSource,
  arxivSub,
  onSelectArxivSub,
  language,
  onToggleLanguage,
  theme,
  onToggleTheme,
  activeTab,
  onNavigate,
  onFactoryClick
}) => {
  const ui = UI_STRINGS[language];
  const isDark = theme === 'dark';
  const [arxivExpanded, setArxivExpanded] = useState(currentSource === 'arxiv');
  const [conferencesExpanded, setConferencesExpanded] = useState(false);
  const [dataSources, setDataSources] = useState<DataSourceInfo[]>([]);
  const [loadingDataSources, setLoadingDataSources] = useState(true);
  const [showZoom, setShowZoom] = useState(false);

  // 加载动态数据源
  useEffect(() => {
    const loadDataSources = async () => {
      try {
        const sources = await getDataSources();
        setDataSources(sources);
      } catch (error) {
        console.error('Failed to load data sources:', error);
        // 降级到静态数据源
        setDataSources([
          { id: 'arxiv', name: 'ArXiv Daily', type: 'streaming', sub_sources: [{ id: 'today', name: 'Today' }, { id: 'week', name: 'This Week' }] },
          { id: 'neurips2025', name: 'NeurIPS 2025', type: 'conference' }
        ]);
      } finally {
        setLoadingDataSources(false);
      }
    };
    loadDataSources();
  }, []);

  const handleArxivSubSelect = (sub: ArxivSubSource) => {
    onSelectSource('arxiv');
    onSelectArxivSub(sub);
    onClose();
  };

  const handleConferenceSelect = (confId: string) => {
    onSelectSource(confId);
    onClose();
  };

  // Handle share/save QR code
  const handleSaveImage = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      if (Capacitor.isNativePlatform()) {
        await Share.share({
          title: language === 'en' ? 'Support FloPap' : '支持 FloPap',
          text: language === 'en' ? 'Scan to support our development!' : '感谢支持 FloPap 论文浏览工具！',
          url: 'https://flopap.com/mm_reward_qrcode_small.png',
          dialogTitle: language === 'en' ? 'Save or Share QR Code' : '保存或分享二维码',
        });
      } else {
        const link = document.createElement('a');
        link.href = '/mm_reward_qrcode_small.png';
        link.download = 'flopap_reward_qrcode.png';
        link.click();
      }
    } catch (error) {
      console.error('Error sharing image:', error);
    }
  };

  // 分离arxiv和会议数据源
  const conferenceSources = dataSources.filter(s => s.type === 'conference');

  return (
    <>
      {/* Overlay with animation */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 md:hidden"
            onClick={onClose}
          />
        )}
      </AnimatePresence>

      {/* Sidebar with animation */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ x: '-100%' }}
            animate={{ x: 0 }}
            exit={{ x: '-100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className={`fixed md:static top-0 left-0 h-full w-72 flex-shrink-0 ${isDark ? 'bg-black border-gray-800' : 'bg-white border-gray-200'} border-r z-[60] shadow-2xl md:shadow-none flex flex-col`}
          >
            <div className="p-4 flex-1 flex flex-col min-h-0 overflow-hidden">
              <div className="flex justify-end items-center mb-2 md:mb-3">
                <button onClick={onClose} className={`md:hidden p-1 rounded-full ${isDark ? 'hover:bg-gray-800 text-gray-400' : 'hover:bg-gray-100 text-gray-600'}`}>
                  <X size={20} />
                </button>
              </div>

              <div className="space-y-3 flex-1 overflow-y-auto no-scrollbar pb-4">

                {/* Navigation (Desktop) */}
                {onNavigate && (
                  <div className="md:block hidden">
                    <div className="space-y-2">
                      <button
                        onClick={() => onNavigate('feed')}
                        className={`w-full flex items-center gap-3 p-2 rounded-xl transition-all ${activeTab === 'feed'
                          ? isDark ? 'bg-gray-800 text-white' : 'bg-gray-100 text-black font-bold'
                          : isDark ? 'text-gray-400 hover:text-white hover:bg-gray-800' : 'text-gray-500 hover:text-black hover:bg-gray-100'
                          }`}
                      >
                        <div className={`p-2 rounded-lg ${activeTab === 'feed' ? 'bg-blue-500 text-white' : 'bg-transparent'}`}>
                          <Layers size={18} />
                        </div>
                        <span>{language === 'en' ? 'Feed' : '推荐流'}</span>
                      </button>

                      <button
                        onClick={() => onNavigate('profile')}
                        className={`w-full flex items-center gap-3 p-2 rounded-xl transition-all ${activeTab === 'profile'
                          ? isDark ? 'bg-gray-800 text-white' : 'bg-gray-100 text-black font-bold'
                          : isDark ? 'text-gray-400 hover:text-white hover:bg-gray-800' : 'text-gray-500 hover:text-black hover:bg-gray-100'
                          }`}
                      >
                        <div className={`p-2 rounded-lg ${activeTab === 'profile' ? 'bg-blue-500 text-white' : 'bg-transparent'}`}>
                          <History size={18} />
                        </div>
                        <span>{language === 'en' ? 'Profile' : '个人中心'}</span>
                      </button>
                    </div>
                    <hr className={`my-2 ${isDark ? 'border-gray-800' : 'border-gray-200'}`} />
                  </div>
                )}

                {/* Settings Row (Theme & Language) */}
                <div>
                  <div className="flex gap-2">
                    {/* Theme Toggle */}
                    <button
                      onClick={onToggleTheme}
                      className={`flex-1 flex items-center justify-center gap-2 p-2 rounded-xl transition-colors ${isDark ? 'bg-gray-800 hover:bg-gray-700' : 'bg-gray-100 hover:bg-gray-200'}`}
                      title={isDark ? ui.darkMode : ui.lightMode}
                    >
                      {isDark ? <Moon size={18} className="text-purple-400" /> : <Sun size={18} className="text-orange-500" />}
                      <span className={`text-sm font-medium ${isDark ? 'text-white' : 'text-gray-900'}`}>{isDark ? 'Dark' : 'Light'}</span>
                    </button>

                    {/* Language Toggle */}
                    <button
                      onClick={onToggleLanguage}
                      className={`flex-1 flex items-center justify-center gap-2 p-3 rounded-xl transition-colors ${isDark ? 'bg-gray-800 hover:bg-gray-700' : 'bg-gray-100 hover:bg-gray-200'}`}
                      title={language === 'en' ? 'English' : '中文'}
                    >
                      <Globe size={18} className="text-blue-400" />
                      <span className={`text-sm font-medium ${isDark ? 'text-white' : 'text-gray-900'}`}>{language === 'en' ? 'EN' : 'ZH'}</span>
                    </button>
                  </div>
                </div>

                {/* Factory Control (Standalone Only) */}
                {onFactoryClick && (
                  <div>
                    <hr className={`my-2 ${isDark ? 'border-gray-800' : 'border-gray-200'}`} />
                    <button
                      onClick={() => { onFactoryClick(); onClose(); }}
                      className={`w-full flex items-center gap-3 p-2 rounded-xl transition-all ${isDark ? 'bg-slate-800 text-slate-300 hover:bg-slate-700' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                        }`}
                    >
                      <div className={`p-2 rounded-lg ${isDark ? 'bg-slate-700' : 'bg-white'}`}>
                        <Activity size={18} className="text-emerald-500" />
                      </div>
                      <div className="text-left">
                        <div className="font-bold text-sm">Factory Control</div>
                        <div className="text-[10px] opacity-80">Manage Pipelines</div>
                      </div>
                    </button>
                  </div>
                )}
                <hr className={`${isDark ? 'border-gray-800' : 'border-gray-200'} my-1`} />

                {/* Data Sources - ArXiv with expandable sub-menu */}
                <div>
                  {/* ArXiv Main Button */}
                  <button
                    onClick={() => setArxivExpanded(!arxivExpanded)}
                    className={`w-full flex items-center justify-between p-2 rounded-xl transition-all ${currentSource === 'arxiv'
                      ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/40'
                      : isDark ? 'bg-gray-800 text-gray-300 hover:bg-gray-700' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${currentSource === 'arxiv' ? 'bg-white/20' : isDark ? 'bg-gray-700' : 'bg-white'}`}>
                        <Flame size={18} />
                      </div>
                      <div className="text-left">
                        <div className="font-bold text-sm">ArXiv Daily</div>
                        <div className="text-[10px] opacity-80">{ui.latestResearch}</div>
                      </div>
                    </div>
                    {arxivExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                  </button>

                  {/* ArXiv Sub-menu with animation */}
                  <AnimatePresence>
                    {arxivExpanded && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="ml-4 mt-2 space-y-1 overflow-hidden"
                      >
                        {/* Today */}
                        <button
                          onClick={() => handleArxivSubSelect('today')}
                          className={`w-full flex items-center gap-3 p-2 rounded-lg transition-all ${currentSource === 'arxiv' && arxivSub === 'today'
                            ? 'bg-blue-500/30 text-blue-400'
                            : isDark ? 'text-gray-400 hover:bg-gray-800' : 'text-gray-600 hover:bg-gray-100'
                            }`}
                        >
                          <Calendar size={14} />
                          <span className="text-sm">{language === 'en' ? 'Today' : '今日论文'}</span>
                        </button>
                        {/* Week */}
                        <button
                          onClick={() => handleArxivSubSelect('week')}
                          className={`w-full flex items-center gap-3 p-2 rounded-lg transition-all ${currentSource === 'arxiv' && arxivSub === 'week'
                            ? 'bg-blue-500/30 text-blue-400'
                            : isDark ? 'text-gray-400 hover:bg-gray-800' : 'text-gray-600 hover:bg-gray-100'
                            }`}
                        >
                          <History size={14} />
                          <span className="text-sm">{language === 'en' ? 'This Week' : '一周论文'}</span>
                        </button>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                {/* Conferences Section - Dynamic */}
                {conferenceSources.length > 0 && (
                  <div>
                    <button
                      onClick={() => setConferencesExpanded(!conferencesExpanded)}
                      className={`w-full flex items-center justify-between p-2 rounded-xl transition-all ${conferenceSources.some(c => c.id === currentSource)
                        ? 'bg-purple-600 text-white shadow-lg shadow-purple-900/40'
                        : isDark ? 'bg-gray-800 text-gray-300 hover:bg-gray-700' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                    >
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${conferenceSources.some(c => c.id === currentSource) ? 'bg-white/20' : isDark ? 'bg-gray-700' : 'bg-white'}`}>
                          <BookOpen size={18} />
                        </div>
                        <div className="text-left">
                          <div className="font-bold text-sm">{language === 'en' ? 'Conferences' : '顶级会议'}</div>
                          <div className="text-[10px] opacity-80">{conferenceSources.length} {language === 'en' ? 'available' : '个可用'}</div>
                        </div>
                      </div>
                      {conferencesExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                    </button>

                    {/* Conference Sub-menu with animation */}
                    <AnimatePresence>
                      {conferencesExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          className="ml-4 mt-2 space-y-1 overflow-hidden"
                        >
                          {conferenceSources.map((conf) => (
                            <button
                              key={conf.id}
                              onClick={() => handleConferenceSelect(conf.id)}
                              className={`w-full flex items-center justify-between gap-3 p-2 rounded-lg transition-all ${currentSource === conf.id
                                ? 'bg-purple-500/30 text-purple-400'
                                : isDark ? 'text-gray-400 hover:bg-gray-800' : 'text-gray-600 hover:bg-gray-100'
                                }`}
                            >
                              <div className="flex items-center gap-2">
                                <Layers size={14} />
                                <span className="text-sm">{conf.name}</span>
                              </div>
                              {conf.paper_count && (
                                <span className="text-[10px] opacity-60">{conf.paper_count}</span>
                              )}
                            </button>
                          ))}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                )}

                {/* Loading indicator */}
                {loadingDataSources && (
                  <div className={`text-center text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                    {language === 'en' ? 'Loading sources...' : '加载数据源...'}
                  </div>
                )}

              </div>
            </div>

            {/* Reward QR Code with Share functionality */}
            <div className={`mt-auto p-4 border-t ${isDark ? 'border-gray-800' : 'border-gray-200'} flex flex-col items-center`}>
              <span className={`text-[10px] font-bold mb-3 uppercase tracking-widest ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                {language === 'en' ? 'Support Development' : '非常感谢您的支持与赞赏'}
              </span>
              <div
                className={`p-2 rounded-xl transition-transform active:scale-95 cursor-pointer ${isDark ? 'bg-white/5' : 'bg-white shadow-sm border border-gray-100'}`}
                onClick={() => setShowZoom(true)}
              >
                <img
                  src="/mm_reward_qrcode_small.png"
                  alt="Reward QR Code"
                  className="w-32 h-32 rounded-lg object-cover"
                />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* QR Code Zoom Modal */}
      <AnimatePresence>
        {showZoom && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/90 backdrop-blur-xl z-[100] flex items-center justify-center"
            onClick={() => setShowZoom(false)}
          >
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              transition={{ type: 'spring', damping: 20 }}
              className="relative"
              onClick={(e) => e.stopPropagation()}
            >
              <img
                src="/mm_reward_qrcode_small.png"
                alt="Reward QR Code"
                className="w-72 h-72 rounded-2xl shadow-2xl"
              />
              <button
                onClick={handleSaveImage}
                className="absolute -bottom-16 left-1/2 -translate-x-1/2 flex items-center gap-2 bg-white/20 backdrop-blur-md text-white px-6 py-3 rounded-full text-sm font-bold"
              >
                <Share2 size={18} />
                {language === 'en' ? 'Save / Share' : '保存 / 分享'}
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default Sidebar;
