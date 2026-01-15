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
import SplashScreen from './components/SplashScreen';

// Hooks
import { usePaperFeed } from '../hooks/usePaperFeed';
import { usePaperAudio } from '../hooks/usePaperAudio';

// Constants
import { UI_STRINGS } from '../constants';

const AppContent: React.FC = () => {
  const isCloudEdition = false; // Standalone edition - no authentication required
  const [showSplash, setShowSplash] = useState(true); // Show splash screen initially
  const userStore = useUserStore();
  const interactionStore = useInteractionStore();

  // Global UI State
  const [language, setLanguage] = useState<AppLanguage>('zh');
  const [theme, setTheme] = useState<AppTheme>('dark');
  const [dataSource, setDataSource] = useState<DataSource>('arxiv');
  const [arxivSub, setArxivSub] = useState<ArxivSubSource>('today');  // 新增: arxiv 子池
  const [viewMode, setViewMode] = useState<ViewMode>(ViewMode.ORIGINAL);
  const [showLoginScreen, setShowLoginScreen] = useState(false);

  // Search State
  const [searchPhrase, setSearchPhrase] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  const {
    papers, setPapers, loading, page, hasMore, setPage, setHasMore, totalPapers, loadPapers
  } = usePaperFeed({
    interactions: interactionStore,
    preferences: userStore.preferences,
    dataSource,
    arxivSub  // 传递 arxiv 子池
  });

  // Collection Viewing State
  const [viewingCollection, setViewingCollection] = useState<{ active: boolean; papers: Paper[]; startIndex: number }>({ active: false, papers: [], startIndex: 0 });
  const [activeIndex, setActiveIndex] = useState(0);

  // Audio Logic
  const containerRef = useRef<HTMLDivElement>(null);
  const isAutoScrolling = useRef(false);

  // Navigation Handler for Audio
  const handleNavigate = (index: number, isAutoPlay = false) => {
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
      }, 2500);
    }

    // 只有在非自动播放的情况下才停止音频
    if (!isAutoPlay) {
      stopSpeech();
    }
  };

  const currentList = viewingCollection.active ? viewingCollection.papers : papers;

  // Destructure hook result to object so we can pass it down cleanly
  const usePaperAudioData = usePaperAudio({
    currentList,
    activeIndex,
    onNavigate: handleNavigate
  });

  const { isSpeaking, audioError, toggleSpeech, stopSpeech } = usePaperAudioData;

  const initLoadTriggered = useRef(false);

  // Initialization
  useEffect(() => {
    const init = async () => {
      if (Capacitor.isNativePlatform()) {
        try {
          await StatusBar.setOverlaysWebView({ overlay: true });
          await StatusBar.setStyle({ style: theme === 'dark' ? Style.Dark : Style.Light });



        } catch (e) {
          console.warn('Native capabilities init failed:', e);
        }
      }

      // Check Auth
      await userStore.checkAuth();

      // Load Interactions
      await interactionStore.fetchInteractions();
    };
    init();
  }, []);

  // Standalone: Auto-proceed from splash after loading data
  useEffect(() => {
    if (showSplash && userStore.isLoggedIn) {
      // Preload initial data in background
      const preloadData = async () => {
        await interactionStore.fetchInteractions();
        // Give splash screen time to display (2 seconds minimum)
        await new Promise(resolve => setTimeout(resolve, 2000));
        setShowSplash(false);
      };
      preloadData();
    }
  }, [showSplash, userStore.isLoggedIn]);

  // Theme Effect
  useEffect(() => {
    if (Capacitor.isNativePlatform()) {
      StatusBar.setStyle({ style: theme === 'dark' ? Style.Dark : Style.Light }).catch(() => { });
    }
  }, [theme]);

  // Persistence: Save State (ViewMode & FeedState)
  useEffect(() => {
    if (userStore.isLoggedIn) {
      const today = new Date().toISOString().split('T')[0];
      const currentState = userStore.preferences.feedStates?.[dataSource] || { lastIndex: 0, lastUpdateDate: today };

      // Update if changed
      if (currentState.lastIndex !== activeIndex || userStore.preferences.lastViewMode !== viewMode) {
        userStore.updatePreferences({
          ...userStore.preferences,
          lastViewMode: viewMode,
          feedStates: {
            ...userStore.preferences.feedStates,
            [dataSource]: {
              lastIndex: activeIndex,
              lastUpdateDate: today
            }
          }
        });
      }
    }
  }, [activeIndex, viewMode, dataSource, userStore.isLoggedIn]);

  // Initial Feed Load & Restore
  useEffect(() => {
    if (initLoadTriggered.current) return;
    if (userStore.isLoggedIn && userStore.user && papers.length === 0 && !loading) {
      initLoadTriggered.current = true;

      // Restore ViewMode
      if (userStore.preferences.lastViewMode) {
        setViewMode(userStore.preferences.lastViewMode);
      }

      // Restore Feed Index
      const savedFeedState = userStore.preferences.feedStates?.[dataSource];
      const today = new Date().toISOString().split('T')[0];
      let startIdx = 0;
      let initSize = 10;

      if (savedFeedState && savedFeedState.lastUpdateDate === today) {
        startIdx = savedFeedState.lastIndex;
        initSize = Math.max(10, startIdx + 5);
        console.log(`[App] Restoring previous session: index=${startIdx}, size=${initSize}`);
      }

      loadPapers(0, userStore.preferences, dataSource, undefined, initSize).then(() => {
        if (startIdx > 0) {
          setActiveIndex(startIdx);
          // Allow time for render before scrolling
          setTimeout(() => {
            if (containerRef.current) {
              const nextScrollTop = startIdx * containerRef.current.clientHeight;
              containerRef.current.scrollTo({ top: nextScrollTop, behavior: 'auto' });
            }
          }, 100);
        }
      });
    }
  }, [userStore.isLoggedIn, userStore.user, loading]);

  // Standalone Edition: Show splash screen, then auto-proceed to main app
  if (showSplash) {
    return (
      <SplashScreen
        onComplete={() => setShowSplash(false)}
        isDark={theme === 'dark'}
        duration={2500}
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
            audioError={audioError}
            toggleSpeech={toggleSpeech}
            autoPlayMode={usePaperAudioData.autoPlayMode}
            setAutoPlayMode={usePaperAudioData.setAutoPlayMode}
            isSearching={isSearching}
            searchPhrase={searchPhrase}
            setSearchPhrase={setSearchPhrase}
            onSearch={handleSearch}
            onClearSearch={handleClearSearch}
            dataSource={dataSource}
            arxivSub={arxivSub}
            setArxivSub={setArxivSub}
            setDataSource={async (source) => {
              setDataSource(source);
              setPapers([]);
              setPage(0);
              setHasMore(true);

              // Restore State logic for new source
              const savedState = userStore.preferences.feedStates?.[source];
              const today = new Date().toISOString().split('T')[0];
              let startIdx = 0;
              let initSize = 10;

              if (savedState && savedState.lastUpdateDate === today) {
                startIdx = savedState.lastIndex;
                initSize = Math.max(10, startIdx + 5);
                console.log(`[App] Switching source to ${source}: Restoring index=${startIdx}`);
              } else {
                console.log(`[App] Switching source to ${source}: New session (0)`);
              }

              await loadPapers(0, userStore.preferences, source, undefined, initSize);

              setActiveIndex(startIdx);
              if (startIdx > 0) {
                setTimeout(() => {
                  if (containerRef.current) {
                    const nextScrollTop = startIdx * containerRef.current.clientHeight;
                    containerRef.current.scrollTo({ top: nextScrollTop, behavior: 'auto' });
                  }
                }, 50);
              }
            }}
            viewMode={viewMode}
            setViewMode={setViewMode}
            viewingCollection={viewingCollection}
            setViewingCollection={setViewingCollection}
            currentPaper={currentPaper}
            onNotInterested={(paperId) => {
              interactionStore.addNotInterested(paperId);
              // Remove locally to update UI immediately
              setPapers(prev => prev.filter(p => p.id !== paperId));
            }}
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
                // 只有在手动滚动时才停止音频
                if (!isAutoScrolling.current) {
                  stopSpeech(); // Stop speech on manual scroll/change
                }
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
                const viewOrder = [ViewMode.ORIGINAL, ViewMode.TRANSLATION, ViewMode.AI_INSIGHT, ViewMode.INFOGRAPHIC, ViewMode.VISUALIZATION];
                const currentIndex = viewOrder.indexOf(viewMode);
                if (direction === 'left') {
                  if (currentIndex < viewOrder.length - 1) setViewMode(viewOrder[currentIndex + 1]);
                } else {
                  if (currentIndex > 0) setViewMode(viewOrder[currentIndex - 1]);
                }
              }}
              onInfographicHtmlChange={(html) => {
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