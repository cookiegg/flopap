import React, { useState, useEffect, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { AppLanguage, AppTheme, DataSource, ViewMode, Paper, ArxivSubSource } from '../types';
import * as StorageService from '../services/storageService';
import { Capacitor } from '@capacitor/core';
import { StatusBar, Style } from '@capacitor/status-bar';

// Stores
import { useUserStore } from '../stores/useUserStore';
import { useInteractionStore } from '../stores/useInteractionStore';

// Components & Pages
import MainLayout from './layouts/MainLayout';
import FeedPage from './pages/FeedPage';
import ProfilePage from './pages/ProfilePage';
import LoginScreen from './components/LoginScreen';
import LandingPage from './components/LandingPage';

// Hooks
import { usePaperFeed } from '../hooks/usePaperFeed';
import { usePaperAudio } from '../hooks/usePaperAudio';

// Constants
import { UI_STRINGS } from '../constants';

const AppContent: React.FC = () => {
  const isCloudEdition = import.meta.env.VITE_FLOPAP_EDITION === 'cloud';
  const userStore = useUserStore();
  const interactionStore = useInteractionStore();

  // Global UI State
  const [language, setLanguage] = useState<AppLanguage>('zh');
  const [theme, setTheme] = useState<AppTheme>('dark');
  const [dataSource, setDataSource] = useState<DataSource>('arxiv');
  const [arxivSub, setArxivSub] = useState<ArxivSubSource>('today');
  const [viewMode, setViewMode] = useState<ViewMode>(ViewMode.ORIGINAL);
  const [showLoginScreen, setShowLoginScreen] = useState(false);

  // Search State
  const [searchPhrase, setSearchPhrase] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  // Feed Logic (Lifted State potentially, or controlled by FeedPage but accessed by Audio?)
  // Audio Player needs access to 'papers' and 'activeIndex' to play next.
  // So we MUST keep Feed State at App level or in a Store.
  // For now, keeping it here to pass down.

  const {
    papers, setPapers, loading, page, hasMore, setPage, setHasMore, totalPapers, loadPapers
  } = usePaperFeed({
    interactions: interactionStore,
    preferences: userStore.preferences,
    dataSource,
    arxivSub
  });

  // Collection Viewing State
  const [viewingCollection, setViewingCollection] = useState<{ active: boolean; papers: Paper[]; startIndex: number }>({ active: false, papers: [], startIndex: 0 });
  const [activeIndex, setActiveIndex] = useState(0);

  // Audio Logic
  const containerRef = useRef<HTMLDivElement>(null);
  const isAutoScrolling = useRef(false);

  // Navigation Handler for Audio
  const handleNavigate = (index: number) => {
    isAutoScrolling.current = true;
    setActiveIndex(index);

    // Pre-fetch logic
    if (!viewingCollection.active && hasMore && !loading) {
      if (papers.length - index <= 3) {
        loadPapers(papers.length, userStore.preferences, dataSource, isSearching ? searchPhrase : undefined);
      }
    }

    if (containerRef.current) {
      const nextScrollTop = index * containerRef.current.clientHeight;
      containerRef.current.scrollTo({
        top: nextScrollTop,
        behavior: 'smooth'
      });
      setTimeout(() => {
        isAutoScrolling.current = false;
      }, 1000);
    }
  };

  const currentList = viewingCollection.active ? viewingCollection.papers : papers;

  const {
    isSpeaking, isLoadingAudio, audioError, toggleSpeech, stopSpeech,
    autoPlayMode, setAutoPlayMode
  } = usePaperAudio({
    currentList,
    activeIndex,
    onNavigate: handleNavigate
  });

  const initLoadTriggered = useRef(false);

  // Initialization
  useEffect(() => {
    const init = async () => {
      if (Capacitor.isNativePlatform()) {
        try {
          await StatusBar.setOverlaysWebView({ overlay: true });
          await StatusBar.setStyle({ style: theme === 'dark' ? Style.Dark : Style.Light });
        } catch (e) {
          console.warn('Status bar not available');
        }
      }

      // Check Auth
      await userStore.checkAuth();

      // Load Interactions
      await interactionStore.fetchInteractions();
    };
    init();
  }, []);

  // Initial Feed Load - usePaperFeed handles dynamic loading (two-step for standalone)
  useEffect(() => {
    if (initLoadTriggered.current) return;
    if (userStore.isLoggedIn && userStore.user && papers.length === 0 && !loading) {
      initLoadTriggered.current = true;
      loadPapers(0, userStore.preferences, 'arxiv');
    }
  }, [userStore.isLoggedIn, userStore.user, loading]); // Simplified deps

  useEffect(() => {
    if (!userStore.isLoggedIn) initLoadTriggered.current = false;
  }, [userStore.isLoggedIn]);

  // Theme Effect
  useEffect(() => {
    if (Capacitor.isNativePlatform()) {
      StatusBar.setStyle({ style: theme === 'dark' ? Style.Dark : Style.Light }).catch(() => { });
    }
  }, [theme]);

  // Refs for stable keyboard handler - always have latest values
  const activeIndexRef = useRef(activeIndex);
  const currentListRef = useRef(currentList);
  activeIndexRef.current = activeIndex;
  currentListRef.current = currentList;

  // Keyboard Navigation: Arrow keys for view modes and paper switching
  useEffect(() => {
    const viewModes = Object.values(ViewMode);

    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if user is typing in an input
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }

      const idx = activeIndexRef.current;
      const list = currentListRef.current;

      switch (e.key) {
        case 'ArrowLeft':
          e.preventDefault();
          setViewMode(prev => {
            const currentIndex = viewModes.indexOf(prev);
            const newIndex = currentIndex > 0 ? currentIndex - 1 : viewModes.length - 1;
            return viewModes[newIndex];
          });
          break;
        case 'ArrowRight':
          e.preventDefault();
          setViewMode(prev => {
            const currentIndex = viewModes.indexOf(prev);
            const newIndex = currentIndex < viewModes.length - 1 ? currentIndex + 1 : 0;
            return viewModes[newIndex];
          });
          break;
        case 'ArrowUp':
          e.preventDefault();
          if (idx > 0) {
            console.log('[Keyboard] ArrowUp: switching from', idx, 'to', idx - 1);
            setActiveIndex(idx - 1);
            stopSpeech();
          }
          break;
        case 'ArrowDown':
          e.preventDefault();
          if (idx < list.length - 1) {
            console.log('[Keyboard] ArrowDown: switching from', idx, 'to', idx + 1);
            setActiveIndex(idx + 1);
            stopSpeech();
          }
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []); // Empty deps - handler uses refs for latest values

  // Auth & Landing Flow
  if (isCloudEdition && !userStore.isLoggedIn) {
    if (Capacitor.isNativePlatform()) {
      return (
        <LoginScreen
          onSuccess={(token: string, user: any) => userStore.login(token, user)}
          isDark={theme === 'dark'}
          language={language}
          variant="mobile"
        />
      );
    }

    return (
      <LandingPage
        onStart={() => setShowLoginScreen(true)}
        language={language}
        onToggleLanguage={() => setLanguage(l => l === 'en' ? 'zh' : 'en')}
        theme={theme}
        showLoginModal={showLoginScreen}
        onCloseLogin={() => setShowLoginScreen(false)}
        onLoginSuccess={(token, user) => {
          userStore.login(token, user);
          setShowLoginScreen(false);
        }}
      />
    );
  }

  const currentPaper = currentList[activeIndex];

  // Search Handlers
  const handleSearch = () => {
    if (!searchPhrase.trim()) return;
    setIsSearching(true);
    setPapers([]);
    setPage(0);
    setHasMore(true);
    loadPapers(0, userStore.preferences, dataSource, searchPhrase);
  };

  const handleClearSearch = () => {
    setIsSearching(false);
    setSearchPhrase('');
    setPapers([]);
    setPage(0);
    setHasMore(true);
    loadPapers(0, userStore.preferences, dataSource);
  };

  return (
    <Router>
      <Routes>
        <Route element={
          <MainLayout
            theme={theme}
            setTheme={setTheme}
            language={language}
            setLanguage={setLanguage}
            isSpeaking={isSpeaking}
            isLoadingAudio={isLoadingAudio}
            audioError={audioError}
            toggleSpeech={toggleSpeech}
            autoPlayMode={autoPlayMode}
            setAutoPlayMode={setAutoPlayMode}
            isSearching={isSearching}
            searchPhrase={searchPhrase}
            setSearchPhrase={setSearchPhrase}
            onSearch={handleSearch}
            onClearSearch={handleClearSearch}
            dataSource={dataSource}
            arxivSub={arxivSub}
            setArxivSub={setArxivSub}
            setDataSource={(source) => {
              setDataSource(source);
              setPapers([]);
              setPage(0);
              setHasMore(true);
              loadPapers(0, userStore.preferences, source);
              setActiveIndex(0);
            }}
            viewMode={viewMode}
            setViewMode={setViewMode}
            viewingCollection={viewingCollection}
            setViewingCollection={setViewingCollection}
            currentPaper={currentPaper}
          />
        }>
          <Route path="/" element={
            <FeedPage
              dataSource={dataSource}
              viewMode={viewMode}
              language={language}
              theme={theme}
              isSearching={isSearching}
              searchPhrase={searchPhrase}
              onClearSearch={handleClearSearch}
              activeIndex={activeIndex}
              setActiveIndex={(idx) => {
                setActiveIndex(idx);
                stopSpeech(); // Stop speech on manual scroll/change
              }}
              containerRef={containerRef}
              isAutoScrolling={isAutoScrolling}
              papers={papers}
              setPapers={setPapers}
              loading={loading}
              hasMore={hasMore}
              loadPapers={loadPapers}
              totalPapers={totalPapers}
              viewingCollection={viewingCollection}
              setViewingCollection={setViewingCollection}
              onSwipeView={(direction) => {
                // Simple logic to changing viewMode based on swipe
                // Copied from original App.tsx
                const viewOrder = [ViewMode.ORIGINAL, ViewMode.TRANSLATION, ViewMode.AI_INSIGHT, ViewMode.INFOGRAPHIC, ViewMode.VISUALIZATION];
                const currentIndex = viewOrder.indexOf(viewMode);
                if (direction === 'left') {
                  if (currentIndex < viewOrder.length - 1) setViewMode(viewOrder[currentIndex + 1]);
                } else {
                  if (currentIndex > 0) setViewMode(viewOrder[currentIndex - 1]);
                }
              }}
              onInfographicHtmlChange={(html) => {
                // Update current paper?
                // Original App.tsx did: setCurrentInfographicHtml
                // But data flow suggests we should update the PAPER object or local state?
                // If it's just for ShareModal, we can read from Paper object if we stored it?
                // Or use a ref/state in MainLayout.
                // Passed to PaperCard via FeedPage.
                // Let's update the paper object in 'papers'
                if (currentPaper) {
                  const updated = { ...currentPaper, infographicHtml: html };
                  setPapers(prev => prev.map(p => p.id === currentPaper.id ? updated : p));
                }
              }}
            />
          } />
          <Route path="/profile" element={
            <ProfilePage
              onSelectPaper={(paper, collection) => {
                // Viewing collection logic
                const paperIndex = collection.findIndex(p => p.id === paper.id);
                setViewingCollection({
                  active: true,
                  papers: collection,
                  startIndex: paperIndex >= 0 ? paperIndex : 0
                });
                setActiveIndex(paperIndex >= 0 ? paperIndex : 0);
                // Navigate to Feed (Home) to view
                // In the new Router, we might want a specific route for this?
                // Or just reuse '/', handled by MainLayout props?
                // If MainLayout handles the 'viewingCollection' state, '/' will render currentList.
                // BUT we need to navigate there.
                // We are using 'navigate' inside the component but we don't have it here directly
                // unless we pass it or the component uses it.
                // ProfilePage uses the passed callback.
                // We can navigate here using a ref or just rely on state change IF we weren't using routes.
                // BUT we ARE using routes.
                // So we need to navigate to '/' after setting state.
                // Since we are in the render body, we can't navigate.
                // Wait, simple fix: pass a wrapper to ProfilePage that calls navigate.
              }}
              language={language}
              theme={theme}
              isCloudEdition={isCloudEdition}
            />
          } />
        </Route>
      </Routes>
    </Router>
  );
}

const App: React.FC = () => {
  return <AppContent />;
};

export default App;