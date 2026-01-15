
import React, { useState, useEffect } from 'react';
import { UserPreferences, UserInteractions, Paper, AppLanguage, AppTheme, User } from '../../types';
import { ARXIV_CATEGORIES, UI_STRINGS } from '../../constants';
import { List, Grid, ChevronRight, UserCircle, Edit2, Plus, X, Settings } from 'lucide-react';
import { getUserInteractions, getUserCollection } from '../../services/backendService';
import UserMenu from './UserMenu';
import UserSettingsV2 from './UserSettingsV2';

interface UserProfileProps {
  preferences: UserPreferences;
  interactions: UserInteractions;
  onUpdatePreferences: (prefs: UserPreferences) => void;
  onSelectPaper: (paper: Paper, collection: Paper[]) => void;
  onLogout: () => void;
  user?: User;
  language: AppLanguage;
  theme: AppTheme;
  isActive?: boolean; // 用于检测页面是否激活，触发数据刷新
  isCloudEdition?: boolean; // 用于显示正确的用户类型
}

type ProfileTab = 'prefs' | 'likes' | 'bookmarks' | 'settings';
type DisplayMode = 'list' | 'grid';

interface UserStats {
  liked_count: number;
  bookmarked_count: number;
  disliked_count: number;
}

const UserProfile: React.FC<UserProfileProps> = ({ preferences, interactions, onUpdatePreferences, onSelectPaper, onLogout, user, language, theme, isActive = true, isCloudEdition = false }) => {
  // CHANGED: Default tab is now 'likes'
  const [activeTab, setActiveTab] = useState<ProfileTab>('likes');
  const [displayMode, setDisplayMode] = useState<DisplayMode>('list');

  // Editing state
  const [isEditing, setIsEditing] = useState(false);
  const [editCats, setEditCats] = useState<string[]>(preferences.selectedCategories);
  const [editKeywords, setEditKeywords] = useState<string[]>(preferences.keywords);
  const [newKeyword, setNewKeyword] = useState('');

  // Collection state
  const [collectionPapers, setCollectionPapers] = useState<Paper[]>([]);
  const [loadingCollection, setLoadingCollection] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);

  // Stats state - 从后端获取
  const [stats, setStats] = useState<UserStats>({
    liked_count: 0,
    bookmarked_count: 0,
    disliked_count: 0
  });

  const ui = UI_STRINGS[language];
  const isDark = theme === 'dark';

  // Theme Classes
  const bgClass = isDark ? 'bg-black' : 'bg-gray-50';
  const textClass = isDark ? 'text-white' : 'text-gray-900';
  const subTextClass = isDark ? 'text-gray-500' : 'text-gray-500';
  const cardBgClass = isDark ? 'bg-gray-800/40 border-white/5' : 'bg-white border-gray-200 shadow-sm';
  const headerBgClass = isDark ? 'bg-gradient-to-b from-gray-900 to-black' : 'bg-white border-b border-gray-100';
  const inputBgClass = isDark ? 'bg-black border-gray-700 text-white' : 'bg-white border-gray-300 text-gray-900';
  const tagBgClass = isDark ? 'bg-gray-800 text-gray-300 border-gray-700' : 'bg-gray-100 text-gray-700 border-gray-200';

  // 加载统计数据 - 页面激活时刷新
  useEffect(() => {
    console.log('[UserProfile] Stats useEffect triggered, isActive:', isActive);
    const loadStats = async () => {
      try {
        const response = await getUserInteractions();

        // 从后端获取统计数据
        if (response.stats) {
          setStats({
            liked_count: response.stats.liked_count || 0,
            bookmarked_count: response.stats.bookmarked_count || 0,
            disliked_count: response.stats.disliked_count || 0
          });
        }
      } catch (error) {
        console.error('Failed to load stats:', error);
      }
    };

    if (isActive) {
      loadStats();
    }
  }, [isActive]);

  // 当interactions变化时，立即刷新统计数据（不管isActive状态）
  useEffect(() => {
    console.log('[UserProfile] Interactions changed, refreshing stats');
    const loadStats = async () => {
      try {
        const response = await getUserInteractions();
        if (response.stats) {
          setStats({
            liked_count: response.stats.liked_count || 0,
            bookmarked_count: response.stats.bookmarked_count || 0,
            disliked_count: response.stats.disliked_count || 0
          });
        }
      } catch (error) {
        console.error('Failed to load stats:', error);
      }
    };
    loadStats();
  }, [interactions]);

  // 当页面激活或切换标签时，重新加载数据
  useEffect(() => {
    console.log('[UserProfile] Collection useEffect triggered, activeTab:', activeTab, 'isActive:', isActive);
    // Load papers when switching tabs - 从后端分页加载
    const loadCollection = async () => {
      setLoadingCollection(true);

      if (activeTab === 'likes' || activeTab === 'bookmarks') {
        const collectionType = activeTab === 'likes' ? 'liked' : 'bookmarked';
        const result = await getUserCollection(collectionType, 20, 0);

        setCollectionPapers(result.papers);
      } else {
        setCollectionPapers([]);
      }

      setLoadingCollection(false);
    };

    if (activeTab !== 'prefs' && isActive) {
      loadCollection();
    }
  }, [activeTab, isActive]);

  // 当interactions变化时，立即刷新collection（如果在相关标签）
  useEffect(() => {
    console.log('[UserProfile] Interactions changed, refreshing collection for tab:', activeTab);
    if (activeTab === 'likes' || activeTab === 'bookmarks') {
      const loadCollection = async () => {
        setLoadingCollection(true);
        const collectionType = activeTab === 'likes' ? 'liked' : 'bookmarked';
        const result = await getUserCollection(collectionType, 20, 0);
        setCollectionPapers(result.papers);
        setLoadingCollection(false);
      };
      loadCollection();
    }
  }, [interactions, activeTab]);

  const handleSave = () => {
    onUpdatePreferences({
      selectedCategories: editCats,
      keywords: editKeywords
    });
    setIsEditing(false);
  };

  const toggleCat = (id: string) => {
    setEditCats(prev =>
      prev.includes(id) ? prev.filter(c => c !== id) : [...prev, id]
    );
  };

  const addKeyword = () => {
    if (newKeyword.trim() && !editKeywords.includes(newKeyword.trim())) {
      setEditKeywords([...editKeywords, newKeyword.trim()]);
      setNewKeyword('');
    }
  };

  const removeKeyword = (kw: string) => {
    setEditKeywords(prev => prev.filter(k => k !== kw));
  };

  const getBgColor = (id: string) => {
    const bgSeed = id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    const hue = bgSeed % 360;
    // Adjust gradient for light mode if needed, but colorful cards usually look okay
    if (isDark) {
      return `linear-gradient(135deg, hsl(${hue}, 60%, 20%), #1a1a1a)`;
    } else {
      return `linear-gradient(135deg, hsl(${hue}, 70%, 90%), #ffffff)`;
    }
  };

  const renderCollectionList = () => {
    if (loadingCollection) {
      return <div className="p-12 text-center text-gray-500 flex flex-col items-center gap-3"><div className="animate-spin w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full"></div>{ui.loading}</div>;
    }
    if (collectionPapers.length === 0) {
      return <div className="p-12 text-center text-gray-500 text-sm italic">{ui.nothingHere}</div>;
    }

    if (displayMode === 'grid') {
      return (
        <div className="grid grid-cols-2 gap-3 pb-20">
          {collectionPapers.map((p) => (
            <div
              key={p.id}
              onClick={() => onSelectPaper(p, collectionPapers)}
              className={`aspect-[3/4] rounded-xl p-3 flex flex-col justify-between relative overflow-hidden cursor-pointer active:scale-95 transition-transform border shadow-md ${isDark ? 'border-white/5' : 'border-gray-100'}`}
              style={{ background: getBgColor(p.id) }}
            >
              <div className="z-10">
                <h4 className={`font-bold text-xs line-clamp-4 leading-relaxed drop-shadow-sm ${isDark ? 'text-white' : 'text-gray-900'}`}>
                  {p.translatedTitle || p.title}
                </h4>
              </div>
              <div className="z-10 mt-auto">
                <p className={`text-[10px] font-mono mt-2 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>{p.id}</p>
                <div className="flex gap-1 mt-1 flex-wrap">
                  {p.categories.slice(0, 1).map(c => (
                    <span key={c} className={`text-[8px] px-1.5 py-0.5 rounded ${isDark ? 'bg-white/20 text-white' : 'bg-black/10 text-black'}`}>{c}</span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      );
    }

    return (
      <div className="space-y-3 pb-20">
        {collectionPapers.map(p => (
          <div
            key={p.id}
            onClick={() => onSelectPaper(p, collectionPapers)}
            className={`p-4 rounded-xl border flex flex-col gap-2 cursor-pointer transition-colors ${cardBgClass} ${isDark ? 'hover:bg-gray-800' : 'hover:bg-white'}`}
          >
            <div className="flex justify-between items-start gap-2">
              <h4 className={`font-bold text-sm line-clamp-2 leading-tight ${textClass}`}>{p.translatedTitle || p.title}</h4>
              <ChevronRight className="w-4 h-4 text-gray-500 flex-shrink-0 mt-1" />
            </div>
            <p className={`text-xs line-clamp-2 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{p.translatedAbstract || p.abstract}</p>
            <div className="flex items-center justify-between mt-1">
              <div className="flex gap-2">
                {p.categories.slice(0, 3).map(c => (
                  <span key={c} className="px-2 py-0.5 bg-blue-500/10 text-blue-500 text-[10px] rounded border border-blue-500/20">{c}</span>
                ))}
              </div>
              <span className="text-[10px] text-gray-500">{p.publishedDate}</span>
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className={`h-full overflow-y-auto no-scrollbar relative ${bgClass} ${textClass}`}>
      <UserMenu
        isOpen={isUserMenuOpen}
        onClose={() => setIsUserMenuOpen(false)}
        onLogout={onLogout}
        user={user}
        language={language}
        theme={theme}
        isCloudEdition={isCloudEdition}
      />

      {/* 1. Header Area */}
      <div className={`pt-8 pb-6 px-6 ${headerBgClass}`}>
        <div className="flex items-center justify-between mb-6">
          {/* Replaced Logout Button with spacing div or just removed to align right */}
          <div className="w-10"></div>

          <div className="flex items-center gap-4">
            <div className="text-right">
              <h1 className={`text-xl font-bold ${textClass}`}>
                {user?.name || user?.phone_number || ui.guestUser}
              </h1>
              <p className={`text-xs ${subTextClass}`}>
                {user?.name && user?.phone_number ?
                  `${user.phone_number} • ${ui.cloudUser}` :
                  (user?.email ? `${user.email} • ${ui.cloudUser}` :
                    `${ui.welcomeBack} • ${ui.cloudUser}`)}
              </p>
            </div>
            <button
              onClick={() => setIsUserMenuOpen(true)}
              className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 p-[2px] shrink-0 transform active:scale-95 transition-transform"
            >
              <div className={`w-full h-full rounded-full flex items-center justify-center overflow-hidden ${isDark ? 'bg-black' : 'bg-white'}`}>
                {user?.avatar_url ? (
                  <img src={user.avatar_url} alt="Profile" className="w-full h-full object-cover" />
                ) : (
                  <UserCircle size={32} className="text-gray-400" />
                )}
              </div>
            </button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-3 gap-3">
          <div className={`rounded-2xl p-3 text-center border ${cardBgClass}`}>
            <span className={`block text-lg font-bold ${textClass}`}>{preferences.selectedCategories.length}</span>
            <span className="text-[10px] text-gray-400 uppercase tracking-wider">{ui.myTopics}</span>
          </div>
          <div className={`rounded-2xl p-3 text-center border ${cardBgClass}`}>
            <span className={`block text-lg font-bold ${textClass}`}>{stats.liked_count}</span>
            <span className="text-[10px] text-gray-400 uppercase tracking-wider">{ui.like}</span>
          </div>
          <div className={`rounded-2xl p-3 text-center border ${cardBgClass}`}>
            <span className={`block text-lg font-bold ${textClass}`}>{stats.bookmarked_count}</span>
            <span className="text-[10px] text-gray-400 uppercase tracking-wider">{ui.save}</span>
          </div>
        </div>
      </div>

      {/* 2. Tab Navigation - CHANGED ORDER: Likes, Bookmarks, Prefs, Settings */}
      <div className="px-6 mb-6">
        <div className={`flex p-1 rounded-xl border ${isDark ? 'bg-gray-900 border-white/10' : 'bg-gray-100 border-gray-200'}`}>
          <button
            onClick={() => setActiveTab('likes')}
            className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all ${activeTab === 'likes'
              ? (isDark ? 'bg-gray-700 text-white shadow' : 'bg-white text-gray-900 shadow')
              : 'text-gray-500'}`}
          >
            {ui.likesTab}
          </button>
          <button
            onClick={() => setActiveTab('bookmarks')}
            className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all ${activeTab === 'bookmarks'
              ? (isDark ? 'bg-gray-700 text-white shadow' : 'bg-white text-gray-900 shadow')
              : 'text-gray-500'}`}
          >
            {ui.savedTab}
          </button>
          <button
            onClick={() => setActiveTab('prefs')}
            className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all ${activeTab === 'prefs'
              ? (isDark ? 'bg-gray-700 text-white shadow' : 'bg-white text-gray-900 shadow')
              : 'text-gray-500'}`}
          >
            {ui.prefsTab}
          </button>
          <button
            onClick={() => setActiveTab('settings')}
            className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all ${activeTab === 'settings'
              ? (isDark ? 'bg-gray-700 text-white shadow' : 'bg-white text-gray-900 shadow')
              : 'text-gray-500'}`}
          >
            AI设置
          </button>
        </div>
      </div>

      {/* 3. Content Area */}
      <div className="px-6 pb-24 animate-fade-in">

        {/* EDIT PREFERENCES VIEW */}
        {activeTab === 'prefs' && (
          <div className="space-y-8">
            {/* Editing Toggle */}
            {!isEditing && (
              <button
                onClick={() => setIsEditing(true)}
                className="w-full flex items-center justify-between p-4 bg-blue-500/10 border border-blue-500/30 rounded-xl text-blue-500 hover:bg-blue-500/20 transition-colors"
              >
                <span className="font-bold text-sm">{ui.customizeFeed}</span>
                <Edit2 size={16} />
              </button>
            )}

            {isEditing ? (
              <div className={`rounded-2xl border p-4 space-y-6 animate-fade-in ${isDark ? 'bg-gray-900/50 border-white/10' : 'bg-gray-50 border-gray-200'}`}>
                {/* Keywords Input */}
                <div>
                  <label className="text-xs font-bold text-gray-400 uppercase mb-3 block">{ui.yourKeywords}</label>
                  <div className="flex gap-2 mb-3">
                    <input
                      type="text"
                      value={newKeyword}
                      onChange={(e) => setNewKeyword(e.target.value)}
                      placeholder={ui.addKeywordPlaceholder}
                      className={`flex-1 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500 ${inputBgClass}`}
                    />
                    <button onClick={addKeyword} className="bg-blue-600 p-2 rounded-lg text-white">
                      <Plus size={20} />
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {editKeywords.map(kw => (
                      <span key={kw} className={`text-xs px-2 py-1 rounded flex items-center gap-1 border ${tagBgClass}`}>
                        {kw}
                        <button onClick={() => removeKeyword(kw)}><X size={12} /></button>
                      </span>
                    ))}
                  </div>
                </div>

                {/* Categories Grid */}
                <div>
                  <label className="text-xs font-bold text-gray-400 uppercase mb-3 block">{ui.yourTopics}</label>
                  <div className="grid grid-cols-2 gap-2">
                    {ARXIV_CATEGORIES.map(cat => (
                      <button
                        key={cat.id}
                        onClick={() => toggleCat(cat.id)}
                        className={`text-left px-3 py-2 rounded-lg text-xs border transition-all ${editCats.includes(cat.id)
                          ? 'bg-blue-600 border-blue-500 text-white'
                          : isDark ? 'bg-black border-gray-800 text-gray-500' : 'bg-white border-gray-300 text-gray-500'
                          }`}
                      >
                        <span className="font-bold block">{cat.id}</span>
                      </button>
                    ))}
                  </div>
                </div>

                <div className="flex gap-2 pt-2">
                  <button onClick={() => setIsEditing(false)} className={`flex-1 py-3 text-sm font-bold rounded-xl ${isDark ? 'bg-gray-800 text-gray-400' : 'bg-gray-200 text-gray-600'}`}>{ui.cancel}</button>
                  <button onClick={handleSave} className="flex-1 py-3 text-sm font-bold text-white bg-blue-600 rounded-xl shadow-lg shadow-blue-900/40">{ui.saveChanges}</button>
                </div>
              </div>
            ) : (
              <>
                {/* Display Current Prefs */}
                <section>
                  <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">{ui.yourTopics}</h3>
                  <div className="flex flex-wrap gap-2">
                    {preferences.selectedCategories.map(catId => (
                      <span key={catId} className={`px-3 py-1.5 rounded-full text-xs font-medium border ${tagBgClass}`}>
                        {catId}
                      </span>
                    ))}
                    {preferences.selectedCategories.length === 0 && <span className="text-sm text-gray-500 italic">{ui.noneSelected}</span>}
                  </div>
                </section>

                <section>
                  <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">{ui.yourKeywords}</h3>
                  <div className="flex flex-wrap gap-2">
                    {preferences.keywords.map((kw, i) => (
                      <span key={i} className={`px-3 py-1.5 rounded-full text-xs font-medium border ${tagBgClass}`}>
                        #{kw}
                      </span>
                    ))}
                    {preferences.keywords.length === 0 && <span className="text-sm text-gray-500 italic">{ui.noneSet}</span>}
                  </div>
                </section>
              </>
            )}
          </div>
        )}

        {/* COLLECTION VIEW (Likes & Bookmarks) */}
        {(activeTab === 'likes' || activeTab === 'bookmarks') && (
          <div>
            <div className="flex items-center justify-end mb-4">
              {/* View Toggle */}
              <div className={`flex p-1 rounded-lg border ${isDark ? 'bg-gray-900 border-gray-800' : 'bg-gray-100 border-gray-200'}`}>
                <button
                  onClick={() => setDisplayMode('list')}
                  className={`p-1.5 rounded ${displayMode === 'list'
                    ? (isDark ? 'bg-gray-700 text-white shadow' : 'bg-white text-gray-900 shadow')
                    : 'text-gray-500'}`}
                >
                  <List size={16} />
                </button>
                <button
                  onClick={() => setDisplayMode('grid')}
                  className={`p-1.5 rounded ${displayMode === 'grid'
                    ? (isDark ? 'bg-gray-700 text-white shadow' : 'bg-white text-gray-900 shadow')
                    : 'text-gray-500'}`}
                >
                  <Grid size={16} />
                </button>
              </div>
            </div>
            {renderCollectionList()}
          </div>
        )}

        {/* SETTINGS VIEW (Framework V2) */}
        {activeTab === 'settings' && (
          <div className="px-6">
            <UserSettingsV2 theme={theme} language={language} />
          </div>
        )}
      </div>
    </div>
  );
};

export default UserProfile;
