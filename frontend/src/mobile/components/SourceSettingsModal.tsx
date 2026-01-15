import React, { useState, useEffect } from 'react';
import { X, Settings, Loader2, RefreshCw } from 'lucide-react';
import { getPoolSettings, updatePoolSettings, PoolSettings } from '../../services/poolSettingsService';
import { triggerConferencePool } from '../../services/dataSourceService';
import { AppLanguage, AppTheme } from '../../types';

interface SourceSettingsModalProps {
    isOpen: boolean;
    onClose: () => void;
    sourceKey: string;
    sourceName: string;
    totalPapers?: number;
    language: AppLanguage;
    theme: AppTheme;
}

const SourceSettingsModal: React.FC<SourceSettingsModalProps> = ({
    isOpen,
    onClose,
    sourceKey,
    sourceName,
    totalPapers = 0,
    language,
    theme
}) => {
    const isDark = theme === 'dark';
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [settings, setSettings] = useState<PoolSettings>({
        pool_ratio: 0.2,
        max_pool_size: 2000,
        show_mode: 'pool',
        filter_no_content: true
    });

    const t = {
        title: language === 'zh' ? '池设置' : 'Pool Settings',
        poolRatio: language === 'zh' ? '推荐池比例' : 'Pool Ratio',
        maxSize: language === 'zh' ? '最大上限' : 'Max Size',
        showMode: language === 'zh' ? '显示模式' : 'Show Mode',
        poolOnly: language === 'zh' ? '仅推荐池' : 'Pool Only',
        showAll: language === 'zh' ? '全部论文' : 'All Papers',
        filterNoContent: language === 'zh' ? '隐藏无翻译/解读的论文' : 'Hide papers without content',
        saveAndRegenerate: language === 'zh' ? '保存并重新生成推荐池' : 'Save & Regenerate Pool',
        cancel: language === 'zh' ? '取消' : 'Cancel',
        papers: language === 'zh' ? '篇' : ' papers',
        regenerating: language === 'zh' ? '正在重新生成...' : 'Regenerating...',
    };

    useEffect(() => {
        if (isOpen && sourceKey) {
            loadSettings();
        }
    }, [isOpen, sourceKey]);

    const loadSettings = async () => {
        setLoading(true);
        try {
            const data = await getPoolSettings(sourceKey);
            setSettings({
                pool_ratio: data.pool_ratio,
                max_pool_size: data.max_pool_size,
                show_mode: data.show_mode as 'pool' | 'all',
                filter_no_content: data.filter_no_content
            });
        } catch (e) {
            console.error('Failed to load pool settings:', e);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            // 1. Save settings
            await updatePoolSettings(sourceKey, settings);

            // 2. Trigger pool regeneration
            await triggerConferencePool(sourceKey, false);

            onClose();
        } catch (e) {
            console.error('Failed to save pool settings:', e);
        } finally {
            setSaving(false);
        }
    };

    const poolSize = Math.min(Math.round(totalPapers * settings.pool_ratio), settings.max_pool_size);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/80">
            <div className={`${isDark ? 'bg-slate-900 border-slate-700' : 'bg-white border-slate-200'} border rounded-2xl max-w-md w-full`}>
                {/* Header */}
                <div className={`flex items-center justify-between p-4 border-b ${isDark ? 'border-slate-800' : 'border-slate-100'}`}>
                    <div className="flex items-center gap-2">
                        <Settings className="text-blue-500" size={20} />
                        <h3 className={`text-lg font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>
                            {sourceName} {t.title}
                        </h3>
                    </div>
                    <button onClick={onClose} className={`p-2 hover:bg-slate-700/20 rounded-lg ${isDark ? 'text-white' : 'text-slate-900'}`}>
                        <X size={20} />
                    </button>
                </div>

                {/* Content */}
                <div className="p-4 space-y-6">
                    {loading ? (
                        <div className="flex justify-center py-8">
                            <Loader2 className="animate-spin text-blue-500" size={32} />
                        </div>
                    ) : (
                        <>
                            {/* Pool Ratio Slider */}
                            <div>
                                <label className={`block text-sm font-medium mb-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                                    {t.poolRatio}: {Math.round(settings.pool_ratio * 100)}%
                                </label>
                                <input
                                    type="range"
                                    min="5"
                                    max="100"
                                    value={Math.round(settings.pool_ratio * 100)}
                                    onChange={(e) => setSettings({ ...settings, pool_ratio: parseInt(e.target.value) / 100 })}
                                    className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
                                />
                                <div className={`text-xs mt-1 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                                    {poolSize} / {totalPapers} {t.papers}
                                </div>
                            </div>

                            {/* Max Pool Size */}
                            <div>
                                <label className={`block text-sm font-medium mb-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                                    {t.maxSize}
                                </label>
                                <input
                                    type="number"
                                    min="10"
                                    max="10000"
                                    value={settings.max_pool_size}
                                    onChange={(e) => setSettings({ ...settings, max_pool_size: parseInt(e.target.value) || 2000 })}
                                    className={`w-full px-3 py-2 rounded-lg border ${isDark ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-gray-300 text-black'}`}
                                />
                            </div>

                            {/* Show Mode */}
                            <div>
                                <label className={`block text-sm font-medium mb-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                                    {t.showMode}
                                </label>
                                <div className="flex gap-2">
                                    <button
                                        onClick={() => setSettings({ ...settings, show_mode: 'pool' })}
                                        className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-all ${settings.show_mode === 'pool'
                                            ? 'bg-blue-600 text-white'
                                            : isDark
                                                ? 'bg-slate-800 text-gray-400 hover:bg-slate-700'
                                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                            }`}
                                    >
                                        {t.poolOnly}
                                    </button>
                                    <button
                                        onClick={() => setSettings({ ...settings, show_mode: 'all' })}
                                        className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-all ${settings.show_mode === 'all'
                                            ? 'bg-blue-600 text-white'
                                            : isDark
                                                ? 'bg-slate-800 text-gray-400 hover:bg-slate-700'
                                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                            }`}
                                    >
                                        {t.showAll}
                                    </button>
                                </div>
                            </div>

                            {/* Filter No Content */}
                            <div className="flex items-center gap-3">
                                <input
                                    type="checkbox"
                                    id="filterNoContent"
                                    checked={settings.filter_no_content}
                                    onChange={(e) => setSettings({ ...settings, filter_no_content: e.target.checked })}
                                    className="w-4 h-4 rounded accent-blue-500"
                                />
                                <label htmlFor="filterNoContent" className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                                    {t.filterNoContent}
                                </label>
                            </div>
                        </>
                    )}
                </div>

                {/* Footer */}
                <div className={`flex justify-end gap-3 p-4 border-t ${isDark ? 'border-slate-800' : 'border-slate-100'}`}>
                    <button
                        onClick={onClose}
                        className={`px-4 py-2 rounded-lg text-sm font-medium ${isDark ? 'bg-slate-800 text-gray-300 hover:bg-slate-700' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
                    >
                        {t.cancel}
                    </button>
                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className="px-4 py-2 rounded-lg text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
                    >
                        {saving && <Loader2 size={14} className="animate-spin" />}
                        {saving ? t.regenerating : t.saveAndRegenerate}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default SourceSettingsModal;
