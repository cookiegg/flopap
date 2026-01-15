
export interface Insight {
  en: string;
  zh: string;
}

export interface User {
  id: string;
  email?: string;
  phone_number?: string;
  name?: string;
  avatar_url?: string;
  onboarding_completed?: boolean;
}

export interface Paper {
  id: string;
  arxiv_id?: string;  // ArXiv ID for API calls
  title: string;
  abstract: string;
  authors: string[];
  categories: string[];
  publishedDate: string;
  pdfUrl?: string;
  // User interaction states
  liked?: boolean;
  bookmarked?: boolean;
  disliked?: boolean;
  // Cached AI content to avoid refetching
  translatedTitle?: string;
  translatedAbstract?: string;
  aiInsights?: Insight[];
  visualizationUrl?: string;
  visual_html?: string;  // 新增：后端返回的可视化图数据
  translation?: {
    title_zh?: string;
    summary_zh?: string;
    ai_interpretation?: string;
    model_name?: string;
  };
  infographicUrl?: string;
  infographicHtml?: string;
}

export interface UserPreferences {
  selectedCategories: string[];
  keywords: string[]; // Comma separated or array
  name?: string;
  // Persisted UI State
  lastViewMode?: ViewMode;
  feedStates?: Record<DataSource, FeedState>;
}

export interface FeedState {
  lastIndex: number;
  lastUpdateDate: string; // YYYY-MM-DD
}

export interface UserInteractions {
  likedPaperIds: string[];
  bookmarkedPaperIds: string[];
  notInterestedPaperIds: string[];
  stats?: {
    liked_count: number;
    bookmarked_count: number;
    disliked_count: number;
  };
}

export enum ViewMode {
  ORIGINAL = 'Original',
  TRANSLATION = 'Translation',
  AI_INSIGHT = 'AI Insight',
  VISUALIZATION = 'Visualization',
  INFOGRAPHIC = 'Infographic',
}

export type Tab = 'feed' | 'profile';

// DataSource is now extensible - base types plus any conference ID string
export type DataSource = 'arxiv' | string;

// Known data source IDs for type safety in specific contexts
export const KNOWN_DATA_SOURCES = ['arxiv', 'neurips2025', 'neurips', 'iclr2025', 'icml2025', 'cvpr2025', 'aaai2025'] as const;

// Structure for dynamically loaded data sources
export interface DataSourceInfo {
  id: DataSource;
  name: string;
  type: 'streaming' | 'conference';
  paper_count?: number;
  sub_sources?: { id: string; name: string }[];
}

export type ArxivSubSource = 'today' | 'week';

export type AppLanguage = 'en' | 'zh';

export type AppTheme = 'dark' | 'light';

