import React, { useRef, useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import Sidebar from '../components/layout/Sidebar';
import TopBar from '../components/layout/TopBar';
import BottomBar from '../components/layout/BottomBar';
import SearchModal from '../components/modals/SearchModal';
import HideConfirmModal from '../components/modals/HideConfirmModal';
import ShareModal from '../components/modals/ShareModal';
import OnboardingModal from '../components/auth/OnboardingModal';
import { AppTheme, AppLanguage, DataSource, ViewMode, Tab, Paper, ArxivSubSource } from '../../types';
import { useUserStore } from '../../stores/useUserStore';
import { useInteractionStore } from '../../stores/useInteractionStore';

import { completeOnboarding } from '../../services/backendService';
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
    autoPlayMode: boolean; // Add Prop
    setAutoPlayMode: (auto: boolean) => void; // Add Prop

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
    onNotInterested?: (paperId: string) => void;
}

const MainLayout: React.FC<MainLayoutProps> = ({
    theme, setTheme,
    language, setLanguage,
    isSpeaking, isLoadingAudio = false, audioError, toggleSpeech,
    isSearching, searchPhrase, setSearchPhrase, onSearch, onClearSearch,
    dataSource, setDataSource,
    arxivSub, setArxivSub,
    viewMode, setViewMode,
    viewingCollection, setViewingCollection,
    currentPaper,
    onNotInterested,
    autoPlayMode, setAutoPlayMode
}) => {
    const navigate = useNavigate();
    const location = useLocation();
    const userStore = useUserStore();
    const interactionStore = useInteractionStore();

    // ... (existing imports)

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
        <div className={`w-full h-[100dvh] flex flex-col font-sans overflow-hidden max-w-md md:max-w-2xl mx-auto md:shadow-2xl md:my-0 md:rounded-none relative transition-all duration-300 ${isDark ? 'bg-black text-white' : 'bg-gray-50 text-gray-900'}`}>

            <OnboardingModal
                isOpen={showOnboarding}
                onComplete={async (prefs) => {
                    await userStore.updatePreferences(prefs);
                    await completeOnboarding();
                    setShowOnboarding(false);
                }}
            />

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
                onFactoryClick={() => setShowFactoryModal(true)}
            />

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
                    navigate('/'); // Go to feed if not there
                }}
                isDark={isDark}
            />

            {/* Main Content (Outlet) */}
            <div className="flex-1 w-full min-h-0 relative">
                <Outlet context={{
                    // Context for child pages if needed, though they usually get props from router or stores
                    // We can't easily pass props via Outlet without `useOutletContext`.
                    // So we might wrap Routes in App.tsx instead of using Layout as a pure wrapper validation.
                    // But let's use Outlet for structure.
                    setShowHideConfirm
                }} />
            </div>

            {/* Hide Confirm Modal (Global) - needs callback to confirm action */}
            <HideConfirmModal
                isOpen={showHideConfirm}
                onClose={() => setShowHideConfirm(false)}
                onConfirm={() => {
                    if (currentPaper && onNotInterested) {
                        onNotInterested(currentPaper.id);
                    }
                    setShowHideConfirm(false);
                }}
                isDark={isDark}
                language={language}
            />


            <BottomBar
                isDark={isDark}
                activeTab={activeTab}
                setActiveTab={handleTabChange}
                language={language}
                isLiked={isLiked}
                isBookmarked={isBookmarked}
                onHideClick={() => setShowHideConfirm(true)} // This triggers the modal
                onToggleLike={() => currentPaper && interactionStore.toggleLike(currentPaper.id)}
                onToggleBookmark={() => currentPaper && interactionStore.toggleBookmark(currentPaper.id)}
                onShare={() => setShareModalOpen(true)}
            />

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
