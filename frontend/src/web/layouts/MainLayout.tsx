import React, { useRef, useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import TopBar from '../components/TopBar';
import BottomBar from '../components/BottomBar';
import SearchModal from '../components/SearchModal';
import HideConfirmModal from '../components/HideConfirmModal';
import ShareModal from '../components/ShareModal';
import OnboardingModal from '../components/OnboardingModal';
import { AppTheme, AppLanguage, DataSource, ViewMode, Tab, Paper, ArxivSubSource } from '../../types';
import { useUserStore } from '../../stores/useUserStore';
import { completeOnboarding } from '../../services/backendService';
import { useInteractionStore } from '../../stores/useInteractionStore';
import RightToolbar from '../components/RightToolbar';
import FactoryControlModal from '../components/FactoryControlModal';

// Props passed from App.tsx or managed here?
// Ideally MainLayout manages most UI state.
interface MainLayoutProps {
    theme: AppTheme;
    setTheme: React.Dispatch<React.SetStateAction<AppTheme>>;
    language: AppLanguage;
    setLanguage: React.Dispatch<React.SetStateAction<AppLanguage>>;

    // Audio props (Managed explicitly so it persists)
    isSpeaking: boolean;
    isLoadingAudio?: boolean;
    audioError: string | null;
    toggleSpeech: () => void;
    autoPlayMode: boolean;
    setAutoPlayMode: (auto: boolean) => void;

    // Search Props
    isSearching: boolean;
    searchPhrase: string;
    setSearchPhrase: (s: string) => void;
    onSearch: () => void;
    onClearSearch: () => void;

    // Data Source
    dataSource: DataSource;
    setDataSource: (source: DataSource) => void;
    arxivSub: ArxivSubSource;
    setArxivSub: (sub: ArxivSubSource) => void;

    // View Mode
    viewMode: ViewMode;
    setViewMode: (mode: ViewMode) => void;

    // Collection State (Shared between Profile selection and Feed display)
    viewingCollection: { active: boolean; papers: Paper[]; startIndex: number };
    setViewingCollection: React.Dispatch<React.SetStateAction<{ active: boolean; papers: Paper[]; startIndex: number }>>;

    // Current Paper Interaction State (For Bottom Bar)
    currentPaper: Paper | undefined;
}

const MainLayout: React.FC<MainLayoutProps> = ({
    theme, setTheme,
    language, setLanguage,
    isSpeaking, isLoadingAudio = false, audioError, toggleSpeech,
    autoPlayMode, setAutoPlayMode,
    isSearching, searchPhrase, setSearchPhrase, onSearch, onClearSearch,
    dataSource, setDataSource,
    arxivSub, setArxivSub,
    viewMode, setViewMode,
    viewingCollection, setViewingCollection,
    currentPaper
}) => {
    const navigate = useNavigate();
    const location = useLocation();
    const userStore = useUserStore();
    const interactionStore = useInteractionStore();

    // UI Local State
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [searchOpen, setSearchOpen] = useState(false);
    const [shareModalOpen, setShareModalOpen] = useState(false);
    const [showHideConfirm, setShowHideConfirm] = useState(false);
    const [showFactoryModal, setShowFactoryModal] = useState(false);

    // Hide confirm logic - needs to be connected to interactions
    // This is tricky because the confirmation result usually calls back into the interaction hook.
    // For now, we simply simulate the presence of the Modal, assuming the page will trigger it OR
    // we move the modal trigger to Global State? 
    // In Original App.tsx, `showHideConfirm` was state.
    // Let's keep it simple: If the FeedPage requests a hide confirmation, it might need to signal up.
    // Or we put the modal inside FeedPage? No, modals should be top level to overlay everything.
    // Ideally we use a global Modal store or similar.
    // OR we pass `setShowHideConfirm` down to FeedPage.

    // Derived State
    const isDark = theme === 'dark';
    const activeTab = location.pathname === '/profile' ? 'profile' : 'feed';

    const handleSourceSelect = (source: DataSource) => {
        setDataSource(source);
        if (location.pathname !== '/') {
            navigate('/');
        }
    };

    const handleBackFromCollection = () => {
        setViewingCollection({ active: false, papers: [], startIndex: 0 });
        navigate('/profile');
    };

    const handleTabChange = (tab: 'feed' | 'profile') => {
        if (tab === 'feed') navigate('/');
        else navigate('/profile');
    };

    const isLiked = currentPaper ? interactionStore.likedPaperIds.includes(currentPaper.id) : false;
    const isBookmarked = currentPaper ? interactionStore.bookmarkedPaperIds.includes(currentPaper.id) : false;

    // Onboarding
    const [showOnboarding, setShowOnboarding] = useState(false);
    // Logic to check onboarding status... handled in App.tsx or Store?
    // Using Store:
    if (userStore.isLoggedIn && userStore.user && !userStore.user.onboarding_completed && !showOnboarding) {
        // This might cause infinite re-renders if not careful.
        // Better to initialize once. App.tsx should handle this initial check.
    }

    return (
        <div className={`w-full h-screen flex flex-row overflow-hidden font-sans transition-all duration-300 ${isDark ? 'bg-black text-white' : 'bg-white text-gray-900'}`}>

            <OnboardingModal
                isOpen={showOnboarding}
                onComplete={async (prefs) => {
                    await userStore.updatePreferences(prefs);
                    setShowOnboarding(false);
                }}
            />

            {/* Left Sidebar (Fixed on Desktop, Drawer on Mobile) */}
            <Sidebar
                isOpen={sidebarOpen}
                onClose={() => setSidebarOpen(false)}
                currentSource={dataSource}
                onSelectSource={handleSourceSelect}
                arxivSub={arxivSub}
                onSelectArxivSub={setArxivSub}
                language={language}
                onToggleLanguage={() => setLanguage(l => l === 'en' ? 'zh' : 'en')}
                theme={theme}
                onToggleTheme={() => setTheme(t => t === 'dark' ? 'light' : 'dark')}
                activeTab={activeTab}
                onNavigate={handleTabChange}
                onFactoryClick={() => setShowFactoryModal(true)}
            />

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col min-w-0 h-full relative">

                <TopBar
                    isDark={isDark}
                    sidebarOpen={sidebarOpen}
                    setSidebarOpen={setSidebarOpen}
                    activeTab={activeTab}
                    viewMode={viewMode}
                    setViewMode={setViewMode}
                    isSpeaking={isSpeaking}
                    isLoadingAudio={isLoadingAudio}
                    audioError={audioError}
                    toggleSpeech={toggleSpeech}
                    autoPlayMode={autoPlayMode}
                    setAutoPlayMode={setAutoPlayMode}
                    onSearchOpen={() => setSearchOpen(true)}
                    viewingCollection={viewingCollection.active}
                    onBackFromCollection={handleBackFromCollection}
                    isSearching={isSearching}
                    searchPhrase={searchPhrase}
                    onClearSearch={onClearSearch}
                />

                <SearchModal
                    isOpen={searchOpen}
                    onClose={() => setSearchOpen(false)}
                    searchPhrase={searchPhrase}
                    setSearchPhrase={setSearchPhrase}
                    onSearch={() => {
                        setSearchOpen(false);
                        onSearch();
                        navigate('/');
                    }}
                    isDark={isDark}
                />

                {/* Scrollable Content */}
                <div className="flex-1 overflow-y-auto relative w-full">
                    <div className="max-w-7xl mx-auto w-full h-full"> {/* Widened container */}
                        <Outlet context={{ setShowHideConfirm }} />
                    </div>
                </div>

                {/* Hide Confirm Modal */}
                <HideConfirmModal
                    isOpen={showHideConfirm}
                    onClose={() => setShowHideConfirm(false)}
                    onConfirm={() => {
                        if (currentPaper) {
                            interactionStore.addNotInterested(currentPaper.id);
                        }
                        setShowHideConfirm(false);
                    }}
                    isDark={isDark}
                    language={language}
                />

                {/* Mobile Bottom Bar */}
                <div className="md:hidden">
                    <BottomBar
                        isDark={isDark}
                        activeTab={activeTab}
                        setActiveTab={handleTabChange}
                        language={language}
                        isLiked={isLiked}
                        isBookmarked={isBookmarked}
                        onHideClick={() => setShowHideConfirm(true)}
                        onToggleLike={() => currentPaper && interactionStore.toggleLike(currentPaper.id)}
                        onToggleBookmark={() => currentPaper && interactionStore.toggleBookmark(currentPaper.id)}
                        onShare={() => setShareModalOpen(true)}
                    />
                </div>
            </div>

            {/* Right Toolbar (Desktop Only, Feed Page Only) */}
            {activeTab === 'feed' && (
                <RightToolbar
                    isDark={isDark}
                    language={language}
                    isLiked={isLiked}
                    isBookmarked={isBookmarked}
                    onHideClick={() => setShowHideConfirm(true)}
                    onToggleLike={() => currentPaper && interactionStore.toggleLike(currentPaper.id)}
                    onToggleBookmark={() => currentPaper && interactionStore.toggleBookmark(currentPaper.id)}
                    onShare={() => setShareModalOpen(true)}
                    currentPaper={currentPaper}
                />
            )}

            <ShareModal
                paper={currentPaper}
                isOpen={shareModalOpen}
                onClose={() => setShareModalOpen(false)}
                isDark={isDark}
                currentViewMode={viewMode}
                infographicHtml={currentPaper?.infographicHtml}
            />

            <FactoryControlModal
                isOpen={showFactoryModal}
                onClose={() => setShowFactoryModal(false)}
                isDark={isDark}
                language={language}
            />
        </div>
    );
};

export default MainLayout;
