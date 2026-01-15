import React, { useState, useEffect } from 'react';
import { X, RefreshCw, Layers, FileText, Play, Activity, CheckCircle, AlertCircle, Clock, Calendar, BookOpen, Download, Users, Sparkles, UploadCloud } from 'lucide-react';
import {
    getFactoryStatus,
    triggerFetchArxiv,
    triggerCandidatePool,
    triggerContentGen,
    triggerRecommendation,
    FactoryStatus,
    TaskStatus
} from '../../services/factoryService';
import {
    getRecommendationSettings,
    updateRecommendationSettings,
    type RecommendationSettings
} from '../../services/recommendationService';
import {
    getAvailableConferences,
    triggerConferenceImport,
    triggerConferencePool,
    triggerConferenceContent,
    type ConferenceInfo
} from '../../services/dataSourceService';
import { getPoolSettings, updatePoolSettings } from '../../services/poolSettingsService';


interface FactoryControlModalProps {
    isOpen: boolean;
    onClose: () => void;
    isDark: boolean;
    language?: 'en' | 'zh';
}

const translations = {
    en: {
        title: "Factory Control",
        targetDate: "Target Date",
        hint: "💡 Recommended order: Fetch → Candidate Pool → Recommendation → Content",
        steps: {
            fetch: { title: "Fetch Arxiv", desc: "Download papers from arXiv for target date" },
            candidate: { title: "Candidate Pool", desc: "Filter CS papers into candidate pool" },
            rec: { title: "User Recommendation", desc: "Generate personalized rankings for user" },
            content: { title: "Content Generation", desc: "Generate translations, AI insights, and TTS audio" }
        },
        settings: {
            arxivRatio: "ArXiv Ratio",
            maxPoolSize: "Max Pool Size",
            autoSave: "*Settings auto-save on run"
        },
        contentGen: {
            fullPool: "Full Candidate Pool",
            myRec: "My Recommendations",
            trans: "Translation",
            ai: "AI Insight",
            tts: "TTS Audio",
            selectOne: "Please select at least one step"
        },
        run: "Run",
        running: "Running..."
    },
    zh: {
        title: "Factory 控制台",
        targetDate: "目标日期",
        hint: "💡 建议顺序：抓取 → 候选池 → 推荐 → 内容生成",
        steps: {
            fetch: { title: "抓取 Arxiv", desc: "下载目标日期的 arXiv 论文" },
            candidate: { title: "生成候选池", desc: "将论文过滤并存入候选池" },
            rec: { title: "用户推荐", desc: "为用户生成个性化推荐排序" },
            content: { title: "内容生成", desc: "生成翻译、AI 解读和 TTS 音频" }
        },
        settings: {
            arxivRatio: "ArXiv 比例",
            maxPoolSize: "最大推荐池",
            autoSave: "* 运行任务时自动保存设置"
        },
        contentGen: {
            fullPool: "完整候选池",
            myRec: "我的推荐列表",
            trans: "中译",
            ai: "AI 解读",
            tts: "TTS 音频",
            selectOne: "请至少选择一个步骤"
        },
        run: "运行",
        running: "运行中..."
    }
};

const FactoryControlModal: React.FC<FactoryControlModalProps> = ({
    isOpen,
    onClose,
    isDark,
    language = 'en'
}) => {
    const t = translations[language === 'zh' ? 'zh' : 'en'];
    const [status, setStatus] = useState<FactoryStatus | null>(null);
    const [refreshing, setRefreshing] = useState(false);

    // ... rest of state initialization ...
    const [targetDate, setTargetDate] = useState(() => {
        const d = new Date();
        d.setDate(d.getDate() - 3);
        return d.toISOString().split('T')[0];
    });

    // Category State
    const [category, setCategory] = useState('cs');
    const categories = [
        { id: 'cs', label: 'CS (Computer Science)' },
        { id: 'ai-ml-cv', label: 'AI / ML / CV' },
        { id: 'math', label: 'Math' },
        { id: 'physics', label: 'Physics' },
        { id: 'all', label: 'All Categories' }
    ];

    // Recommendation Settings State
    const [recSettings, setRecSettings] = useState<RecommendationSettings | null>(null);
    const [recSaving, setRecSaving] = useState(false);

    // Content Gen Options
    const [genScope, setGenScope] = useState<'candidate' | 'user'>('candidate');
    const [genSteps, setGenSteps] = useState({
        trans: true,
        ai: true,
        tts: true
    });

    // Conference State
    const [conferences, setConferences] = useState<ConferenceInfo[]>([]);
    const [loadingConferences, setLoadingConferences] = useState(false);
    const [activeTab, setActiveTab] = useState<'arxiv' | 'conferences'>('arxiv');
    const [confPoolRatios, setConfPoolRatios] = useState<Record<string, number>>({});  // 每个会议的推荐池比例 (默认 20%)
    const [confContentScope, setConfContentScope] = useState<'all' | 'pool'>('pool');  // 内容生成范围
    const [confGenSteps, setConfGenSteps] = useState({
        trans: true,
        ai: true,
        tts: true
    });

    // Toast notification state
    const [toastMessage, setToastMessage] = useState<string | null>(null);
    const showToast = (message: string) => {
        setToastMessage(message);
        setTimeout(() => setToastMessage(null), 3000);
    };

    // ... useEffect ...
    useEffect(() => {
        if (isOpen) {
            fetchStatus();
            fetchRecSettings();
            fetchConferences(true);  // Initial load - show loading spinner
            const interval = setInterval(() => {
                fetchStatus();
                fetchConferences(false);  // Background refresh - no loading spinner
            }, 3000);
            return () => clearInterval(interval);
        }
    }, [isOpen]);

    const fetchConferences = async (isInitialLoad: boolean = false) => {
        // Only show loading spinner on initial load, not on background refresh
        if (isInitialLoad) {
            setLoadingConferences(true);
        }
        try {
            const confs = await getAvailableConferences();
            setConferences(confs);
        } catch (e) {
            console.error('Failed to fetch conferences', e);
        } finally {
            if (isInitialLoad) {
                setLoadingConferences(false);
            }
        }
    };

    // ... methods ...
    const fetchStatus = async () => {
        try {
            const s = await getFactoryStatus();
            setStatus(s);
        } catch (e) {
            console.error(e);
        }
    };

    const fetchRecSettings = async () => {
        try {
            const s = await getRecommendationSettings();
            setRecSettings({
                arxiv_ratio: s.arxiv_ratio,
                conference_ratio: s.conference_ratio,
                max_pool_size: s.max_pool_size,
                enable_auto_generation: s.enable_auto_generation,
                preferred_models: s.preferred_models
            });
        } catch (e) {
            console.error("Failed to fetch recommendation settings", e);
        }
    };

    const handleFetchArxiv = async () => {
        setRefreshing(true);
        try {
            await triggerFetchArxiv(targetDate);
            await fetchStatus();
        } finally {
            setRefreshing(false);
        }
    };

    const handleCandidatePool = async () => {
        setRefreshing(true);
        try {
            await triggerCandidatePool(targetDate, category);
            await fetchStatus();
        } finally {
            setRefreshing(false);
        }
    };

    const handleRecGen = async () => {
        setRefreshing(true);
        try {
            // First save settings if they exist
            if (recSettings) {
                await updateRecommendationSettings(recSettings);
            }
            await triggerRecommendation(category);
            await fetchStatus();
        } finally {
            setRefreshing(false);
        }
    };

    const handleContentGen = async () => {
        const steps = (Object.keys(genSteps) as ('trans' | 'ai' | 'tts')[]).filter(k => genSteps[k]);
        if (steps.length === 0) {
            alert(t.contentGen.selectOne);
            return;
        }

        setRefreshing(true);
        try {
            await triggerContentGen({
                target_date: targetDate,
                scope: genScope,
                steps: steps,
                category
            });
            await fetchStatus();
        } finally {
            setRefreshing(false);
        }
    };

    // Conference handlers
    const handleConfImport = async (confId: string) => {
        try {
            await triggerConferenceImport(confId);
            await fetchConferences(false);
            showToast(`✅ ${confId.toUpperCase()} 导入已启动`);
        } catch (e: any) {
            alert(e.message || 'Import failed');
        }
    };

    const handleConfPool = async (confId: string) => {
        try {
            const ratio = confPoolRatios[confId] || 0.2;
            // 保存设置到数据库
            await updatePoolSettings(confId, {
                pool_ratio: ratio,
                max_pool_size: 5000,
                show_mode: 'pool',
                filter_no_content: true
            });
            // 触发推荐池生成
            await triggerConferencePool(confId, false, ratio);
            await fetchConferences(false);
            showToast(`✅ ${confId.toUpperCase()} 推荐池生成已启动`);
        } catch (e: any) {
            alert(e.message || 'Pool generation failed');
        }
    };

    const handleConfContent = async (confId: string) => {
        try {
            const steps = (Object.keys(confGenSteps) as ('trans' | 'ai' | 'tts')[]).filter(k => confGenSteps[k]);
            if (steps.length === 0) {
                alert(language === 'zh' ? '请至少选择一个步骤' : 'Select at least one step');
                return;
            }
            const ratio = confPoolRatios[confId] || 0.2;
            await triggerConferenceContent(confId, steps, confContentScope, ratio);
            await fetchConferences(false);
            showToast(`✅ ${confId.toUpperCase()} 内容生成已启动`);
        } catch (e: any) {
            alert(e.message || 'Content generation failed');
        }
    };

    if (!isOpen) return null;

    const StatusBadge = ({ task }: { task: TaskStatus }) => {
        const state = task.status;
        let color = 'bg-slate-500';
        let Icon = Clock;

        if (state === 'running') { color = 'bg-blue-500 animate-pulse'; Icon = RefreshCw; }
        if (state === 'success') { color = 'bg-emerald-500'; Icon = CheckCircle; }
        if (state === 'success_empty') { color = 'bg-amber-500'; Icon = CheckCircle; }
        if (state === 'error') { color = 'bg-red-500'; Icon = AlertCircle; }

        return (
            <div className="flex items-center gap-2">
                <span className={`px-2 py-0.5 rounded text-xs text-white font-mono flex items-center gap-1 ${color}`}>
                    <Icon size={12} className={state === 'running' ? 'animate-spin' : ''} />
                    {state?.toUpperCase()}
                </span>
                {task.count > 0 && (
                    <span className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                        {task.count} papers
                    </span>
                )}
            </div>
        );
    };

    const TaskCard = ({
        step,
        title,
        description,
        icon: Icon,
        task,
        onRun,
        disabled,
        children
    }: {
        step: number;
        title: string;
        description: string;
        icon: React.ElementType;
        task?: TaskStatus;
        onRun: () => void;
        disabled?: boolean;
        children?: React.ReactNode;
    }) => (
        <div className={`p-4 rounded-xl border transition-all ${isDark ? 'bg-slate-800/50 border-slate-700' : 'bg-slate-50 border-slate-200'
            } ${disabled ? 'opacity-50' : ''}`}>
            <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3 flex-1">
                    <div className={`p-2 rounded-lg ${task?.status === 'success' ? 'bg-emerald-500/20 text-emerald-500' :
                        task?.status === 'running' ? 'bg-blue-500/20 text-blue-500' :
                            isDark ? 'bg-slate-700 text-slate-400' : 'bg-slate-200 text-slate-500'
                        }`}>
                        <Icon size={18} />
                    </div>
                    <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                            <span className={`text-xs font-bold ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                                STEP {step}
                            </span>
                            <h4 className={`font-semibold ${isDark ? 'text-white' : 'text-slate-800'}`}>
                                {title}
                            </h4>
                        </div>
                        <p className={`text-xs mb-2 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                            {description}
                        </p>
                        {task && <StatusBadge task={task} />}
                        {task?.error && (
                            <div className="mt-2 p-2 bg-red-500/10 border border-red-500/20 rounded text-red-400 text-xs">
                                {task.error}
                            </div>
                        )}
                        {task?.last_run_at && (
                            <div className={`mt-1 text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                                Last: {new Date(task.last_run_at).toLocaleTimeString()}
                            </div>
                        )}
                    </div>
                </div>
                <button
                    onClick={onRun}
                    disabled={disabled || task?.status === 'running' || refreshing}
                    className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                >
                    {task?.status === 'running' ? t.running : t.run}
                </button>
            </div>
            {children}
        </div>
    );

    return (
        <>
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80">
                <div className={`${isDark ? 'bg-slate-900 border-slate-700' : 'bg-white border-slate-200'} border rounded-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto no-scrollbar`}>
                    {/* Header */}
                    <div className={`flex items-center justify-between p-4 border-b ${isDark ? 'border-slate-800' : 'border-slate-100'}`}>
                        <div className="flex items-center gap-2">
                            <Activity className="text-blue-500" />
                            <h3 className={`text-lg font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>
                                {t.title}
                            </h3>
                        </div>
                        <button onClick={onClose} className={`p-2 hover:bg-slate-700/20 rounded-lg ${isDark ? 'text-white' : 'text-slate-900'}`}>
                            <X size={20} />
                        </button>
                    </div>

                    {/* Tab Switcher */}
                    <div className={`flex p-2 gap-2 border-b ${isDark ? 'border-slate-800 bg-slate-900' : 'border-slate-200 bg-slate-50'}`}>
                        <button
                            onClick={() => setActiveTab('arxiv')}
                            className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-sm font-medium transition-all ${activeTab === 'arxiv'
                                ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/30'
                                : isDark
                                    ? 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-white'
                                    : 'bg-white text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                                }`}
                        >
                            <RefreshCw size={16} />
                            <span>{language === 'zh' ? 'ArXiv 每日' : 'ArXiv Daily'}</span>
                        </button>
                        <button
                            onClick={() => setActiveTab('conferences')}
                            className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-sm font-medium transition-all ${activeTab === 'conferences'
                                ? 'bg-purple-600 text-white shadow-lg shadow-purple-900/30'
                                : isDark
                                    ? 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-white'
                                    : 'bg-white text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                                }`}
                        >
                            <BookOpen size={16} />
                            <span>{language === 'zh' ? '会议论文' : 'Conferences'}</span>
                        </button>
                    </div>

                    {/* ArXiv Tab Content */}
                    {activeTab === 'arxiv' && (
                        <div className="p-4 space-y-4">
                            {/* Date Picker */}
                            <div className={`p-3 rounded-xl border ${isDark ? 'bg-slate-800 border-slate-700' : 'bg-blue-50 border-blue-100'}`}>
                                <div className="flex items-center gap-3">
                                    <Calendar className={isDark ? 'text-blue-400' : 'text-blue-600'} size={20} />
                                    <div className="flex-1">
                                        <label className={`text-xs font-medium ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                                            {t.targetDate}
                                        </label>
                                        <input
                                            type="date"
                                            value={targetDate}
                                            onChange={(e) => setTargetDate(e.target.value)}
                                            className={`w-full mt-1 px-2 py-1 rounded border text-sm ${isDark
                                                ? 'bg-slate-700 border-slate-600 text-white'
                                                : 'bg-white border-slate-200 text-slate-800'
                                                }`}
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* Workflow Hint */}
                            <div className={`px-3 py-2 rounded-lg text-xs ${isDark ? 'bg-blue-900/30 text-blue-300' : 'bg-blue-50 text-blue-700'}`}>
                                {t.hint}
                            </div>

                            {/* Step 1: Fetch */}
                            <TaskCard
                                step={1}
                                title={t.steps.fetch.title}
                                description={t.steps.fetch.desc}
                                icon={RefreshCw}
                                task={status?.fetch_arxiv}
                                onRun={handleFetchArxiv}
                            />

                            {/* Step 2: Candidates */}
                            <TaskCard
                                step={2}
                                title={t.steps.candidate.title}
                                description={t.steps.candidate.desc}
                                icon={Layers}
                                task={status?.gen_candidate_pool}
                                onRun={handleCandidatePool}
                            >
                                <div className="mt-4 pt-4 border-t border-slate-700/50">
                                    <label className={`text-xs font-medium block mb-2 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                                        Target Category
                                    </label>
                                    <div className="flex flex-wrap gap-2">
                                        {categories.map(c => (
                                            <button
                                                key={c.id}
                                                onClick={() => setCategory(c.id)}
                                                className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${category === c.id
                                                    ? 'bg-blue-600 border-blue-600 text-white shadow-sm shadow-blue-500/20'
                                                    : isDark
                                                        ? 'bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-600 hover:text-slate-300'
                                                        : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300 hover:text-slate-800'
                                                    }`}
                                            >
                                                {c.label}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </TaskCard>

                            {/* Step 3: Recommendation */}
                            <TaskCard
                                step={3}
                                title={t.steps.rec.title}
                                description={t.steps.rec.desc}
                                icon={FileText}
                                task={status?.gen_recommendation}
                                onRun={handleRecGen}
                            >
                                {recSettings && (
                                    <div className="mt-4 pt-4 border-t border-slate-700/50 space-y-4">
                                        <div>
                                            <div className="flex justify-between text-xs mb-1">
                                                <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>
                                                    {t.settings.arxivRatio}
                                                </span>
                                                <span className="text-blue-500 font-mono">{recSettings.arxiv_ratio}%</span>
                                            </div>
                                            <input
                                                type="range"
                                                min="1"
                                                max="100"
                                                value={recSettings.arxiv_ratio}
                                                onChange={(e) => setRecSettings({ ...recSettings, arxiv_ratio: parseInt(e.target.value) })}
                                                className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
                                            />
                                        </div>
                                        <div>
                                            <div className="flex justify-between text-xs mb-1">
                                                <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>
                                                    {t.settings.maxPoolSize}
                                                </span>
                                                <span className="text-emerald-500 font-mono">{recSettings.max_pool_size}</span>
                                            </div>
                                            <input
                                                type="range"
                                                min="10"
                                                max="500"
                                                step="10"
                                                value={recSettings.max_pool_size}
                                                onChange={(e) => setRecSettings({ ...recSettings, max_pool_size: parseInt(e.target.value) })}
                                                className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                                            />
                                        </div>
                                        <div className="text-right">
                                            <span className="text-[10px] text-slate-500 mr-2">
                                                {t.settings.autoSave}
                                            </span>
                                        </div>
                                    </div>
                                )}
                            </TaskCard>

                            {/* Step 4: Content Generation */}
                            <TaskCard
                                step={4}
                                title={t.steps.content.title}
                                description={t.steps.content.desc}
                                icon={Play}
                                task={status?.gen_content}
                                onRun={handleContentGen}
                            >
                                <div className="mt-4 pt-4 border-t border-slate-700/50 space-y-3">
                                    {/* Scope Selector */}
                                    <div className="flex gap-4 text-sm">
                                        <label className={`flex items-center gap-2 cursor-pointer ${isDark ? 'text-white' : 'text-slate-700'}`}>
                                            <input
                                                type="radio"
                                                name="scope"
                                                checked={genScope === 'candidate'}
                                                onChange={() => setGenScope('candidate')}
                                                className="accent-blue-500"
                                            />
                                            {t.contentGen.fullPool}
                                        </label>
                                        <label className={`flex items-center gap-2 cursor-pointer ${isDark ? 'text-white' : 'text-slate-700'}`}>
                                            <input
                                                type="radio"
                                                name="scope"
                                                checked={genScope === 'user'}
                                                onChange={() => setGenScope('user')}
                                                className="accent-blue-500"
                                            />
                                            {t.contentGen.myRec}
                                        </label>
                                    </div>

                                    {/* Steps Selector */}
                                    <div className="flex gap-4 text-sm">
                                        {(['trans', 'ai', 'tts'] as const).map((step) => (
                                            <label key={step} className={`flex items-center gap-2 cursor-pointer ${isDark ? 'text-slate-300' : 'text-slate-600'}`}>
                                                <input
                                                    type="checkbox"
                                                    checked={genSteps[step]}
                                                    onChange={e => setGenSteps({ ...genSteps, [step]: e.target.checked })}
                                                    className="accent-emerald-500"
                                                />
                                                {step === 'trans' ? t.contentGen.trans : step === 'ai' ? t.contentGen.ai : t.contentGen.tts}
                                            </label>
                                        ))}
                                    </div>
                                </div>
                            </TaskCard>

                        </div>
                    )}

                    {/* Conference Tab Content */}
                    {activeTab === 'conferences' && (
                        <div className="p-4 space-y-3">
                            <div className={`px-3 py-2 rounded-lg text-xs ${isDark ? 'bg-purple-900/30 text-purple-300' : 'bg-purple-50 text-purple-700'}`}>
                                💡 {language === 'zh' ? '流程: 导入 → 推荐池 → 内容生成' : 'Workflow: Import → Pool → Content'}
                            </div>

                            {/* Content Settings */}
                            <div className={`p-3 rounded-xl border space-y-3 ${isDark ? 'bg-slate-800/50 border-slate-700' : 'bg-slate-50 border-slate-200'}`}>
                                <div className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                                    💡 {language === 'zh' ? '推荐池比例在每个会议卡片中单独设置' : 'Pool ratio is set per conference below'}
                                </div>

                                {/* Content Scope Toggle */}
                                <div className={`pt-2 border-t ${isDark ? 'border-slate-700' : 'border-slate-200'}`}>
                                    <div className={`text-xs mb-2 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                                        {language === 'zh' ? '内容生成范围' : 'Content Scope'}
                                    </div>
                                    <div className="flex gap-3 text-sm">
                                        <label className={`flex items-center gap-2 cursor-pointer ${isDark ? 'text-slate-300' : 'text-slate-600'}`}>
                                            <input
                                                type="radio"
                                                name="confContentScope"
                                                checked={confContentScope === 'all'}
                                                onChange={() => setConfContentScope('all')}
                                                className="accent-purple-500"
                                            />
                                            {language === 'zh' ? '全部论文' : 'All Papers'}
                                        </label>
                                        <label className={`flex items-center gap-2 cursor-pointer ${isDark ? 'text-slate-300' : 'text-slate-600'}`}>
                                            <input
                                                type="radio"
                                                name="confContentScope"
                                                checked={confContentScope === 'pool'}
                                                onChange={() => setConfContentScope('pool')}
                                                className="accent-purple-500"
                                            />
                                            {language === 'zh' ? '仅推荐池' : 'Pool Only'}
                                        </label>
                                    </div>
                                </div>


                                {/* Steps Selector */}
                                <div className={`pt-2 border-t ${isDark ? 'border-slate-700' : 'border-slate-200'}`}>
                                    <div className={`text-xs mb-2 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                                        {language === 'zh' ? '生成步骤' : 'Generation Steps'}
                                    </div>
                                    <div className="flex gap-4 text-sm">
                                        {(['trans', 'ai', 'tts'] as const).map((step) => (
                                            <label key={step} className={`flex items-center gap-2 cursor-pointer ${isDark ? 'text-slate-300' : 'text-slate-600'}`}>
                                                <input
                                                    type="checkbox"
                                                    checked={confGenSteps[step]}
                                                    onChange={e => setConfGenSteps({ ...confGenSteps, [step]: e.target.checked })}
                                                    className="accent-purple-500"
                                                />
                                                {step === 'trans' ? (language === 'zh' ? '翻译' : 'Trans') :
                                                    step === 'ai' ? (language === 'zh' ? '解读' : 'AI') :
                                                        (language === 'zh' ? '语音' : 'TTS')}
                                            </label>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            {loadingConferences ? (
                                <div className={`text-center py-8 text-sm flex flex-col items-center justify-center gap-2 ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                                    <RefreshCw className="animate-spin" size={24} />
                                    {language === 'zh' ? '加载中...' : 'Loading conferences...'}
                                </div>
                            ) : conferences.length === 0 ? (
                                <div className={`text-center py-8 text-sm ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                                    {language === 'zh' ? '暂无会议数据' : 'No conferences found'}
                                </div>
                            ) : (
                                <div className="space-y-2">
                                    {conferences.map((conf) => {
                                        const importStatus = conf.status?.import?.status;
                                        const poolStatus = conf.status?.pool?.status;
                                        const contentStatus = conf.status?.content?.status;

                                        return (
                                            <div
                                                key={conf.id}
                                                className={`p-3 rounded-xl border ${isDark ? 'bg-slate-800/50 border-slate-700' : 'bg-slate-50 border-slate-200'}`}
                                            >
                                                <div className="flex items-center justify-between mb-2">
                                                    <div>
                                                        <span className={`font-medium text-sm ${isDark ? 'text-white' : 'text-slate-800'}`}>
                                                            {conf.name}
                                                        </span>
                                                        {conf.paper_count > 0 && (
                                                            <span className={`ml-2 text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                                                                {conf.paper_count} papers
                                                            </span>
                                                        )}
                                                    </div>
                                                    {conf.imported && (
                                                        <CheckCircle size={14} className="text-emerald-500" />
                                                    )}
                                                </div>

                                                {/* Per-conference Pool Ratio Slider */}
                                                {conf.imported && (
                                                    <div className="mb-2">
                                                        <div className="flex justify-between text-[10px] mb-0.5">
                                                            <span className={isDark ? 'text-slate-500' : 'text-slate-400'}>
                                                                {language === 'zh' ? '推荐池比例' : 'Pool Ratio'}
                                                            </span>
                                                            <span className="text-purple-400 font-mono">
                                                                {Math.round((confPoolRatios[conf.id] || 0.2) * 100)}%
                                                            </span>
                                                        </div>
                                                        <input
                                                            type="range"
                                                            min="10"
                                                            max="100"
                                                            step="5"
                                                            value={(confPoolRatios[conf.id] || 0.2) * 100}
                                                            onChange={(e) => setConfPoolRatios(prev => ({
                                                                ...prev,
                                                                [conf.id]: parseInt(e.target.value) / 100
                                                            }))}
                                                            className="w-full h-1 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-purple-500"
                                                        />
                                                    </div>
                                                )}

                                                <div className="flex gap-2">
                                                    <button
                                                        onClick={() => handleConfImport(conf.id)}
                                                        disabled={importStatus === 'running'}
                                                        className={`flex-1 px-2 py-1.5 rounded-lg text-xs font-medium flex items-center justify-center gap-1 ${conf.imported
                                                            ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                                                            : isDark
                                                                ? 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                                                                : 'bg-slate-200 text-slate-600 hover:bg-slate-300'
                                                            } ${importStatus === 'running' ? 'opacity-50' : ''}`}
                                                    >
                                                        <Download size={12} />
                                                        {importStatus === 'running' ? '...' : language === 'zh' ? '导入' : 'Import'}
                                                    </button>

                                                    <button
                                                        onClick={() => handleConfPool(conf.id)}
                                                        disabled={!conf.imported || poolStatus === 'running'}
                                                        className={`flex-1 px-2 py-1.5 rounded-lg text-xs font-medium flex items-center justify-center gap-1 ${isDark
                                                            ? 'bg-slate-700 text-slate-300 hover:bg-slate-600 disabled:opacity-40'
                                                            : 'bg-slate-200 text-slate-600 hover:bg-slate-300 disabled:opacity-40'
                                                            }`}
                                                    >
                                                        <Users size={12} />
                                                        {poolStatus === 'running' ? '...' : language === 'zh' ? '推荐池' : 'Pool'}
                                                    </button>

                                                    <button
                                                        onClick={() => handleConfContent(conf.id)}
                                                        disabled={!conf.imported || contentStatus === 'running'}
                                                        className={`flex-1 px-2 py-1.5 rounded-lg text-xs font-medium flex items-center justify-center gap-1 ${isDark
                                                            ? 'bg-slate-700 text-slate-300 hover:bg-slate-600 disabled:opacity-40'
                                                            : 'bg-slate-200 text-slate-600 hover:bg-slate-300 disabled:opacity-40'
                                                            }`}
                                                    >
                                                        <Sparkles size={12} />
                                                        {contentStatus === 'running' ? '...' : language === 'zh' ? '内容' : 'Content'}
                                                    </button>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div >

            {/* Toast Notification */}
            {
                toastMessage && (
                    <div className={`fixed bottom-20 left-1/2 transform -translate-x-1/2 px-6 py-3 rounded-xl shadow-2xl z-[100] ${isDark ? 'bg-emerald-600 text-white' : 'bg-emerald-500 text-white'}`}>
                        {toastMessage}
                    </div>
                )
            }
        </>
    );
};

export default FactoryControlModal;
