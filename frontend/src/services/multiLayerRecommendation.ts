/**
 * 多层推荐池前端适配 - 循环列表管理
 * 支持实时过滤和用户交互
 */

import { Paper, UserPreferences, UserInteractions } from '../types';
import { fetchFeedPapers, submitFeedback } from './backendService';

interface LocalFilters {
  dislikedToday: Set<string>;     // 当日不感兴趣
  likedToday: Set<string>;        // 当日点赞  
  bookmarkedToday: Set<string>;   // 当日收藏
}

class MultiLayerRecommendationManager {
  private serverRecommendations: Paper[] = [];
  private localFilters: LocalFilters;
  private displayPapers: Paper[] = [];
  private currentIndex: number = 0;
  
  constructor() {
    this.localFilters = {
      dislikedToday: new Set(),
      likedToday: new Set(),
      bookmarkedToday: new Set()
    };
  }
  
  /**
   * 加载服务端推荐 (多层过滤后的结果)
   */
  async loadRecommendations(source: string, cursor: number = 0): Promise<void> {
    try {
      const result = await fetchFeedPapers(cursor, 50, source);
      
      if (cursor === 0) {
        this.serverRecommendations = result.papers;
      } else {
        this.serverRecommendations.push(...result.papers);
      }
      
      this.updateDisplayPapers();
    } catch (error) {
      console.error('Failed to load recommendations:', error);
    }
  }
  
  /**
   * 处理用户不感兴趣 - 立即从显示列表移除
   */
  async handleDislike(paperId: string): Promise<void> {
    // 1. 立即从本地显示列表移除
    this.localFilters.dislikedToday.add(paperId);
    this.updateDisplayPapers();
    
    // 2. 调整当前索引
    this.adjustCurrentIndex();
    
    // 3. 异步同步到后端
    try {
      await submitFeedback(paperId, 'dislike', true, true);
    } catch (error) {
      console.error('Failed to submit dislike feedback:', error);
      // 可以考虑回滚本地状态
    }
    
    // 4. 检查是否需要加载更多
    if (this.getRemainingCount() < 5) {
      await this.loadMoreRecommendations();
    }
  }
  
  /**
   * 处理用户点赞 - 保持在显示列表中
   */
  async handleLike(paperId: string): Promise<void> {
    this.localFilters.likedToday.add(paperId);
    
    try {
      await submitFeedback(paperId, 'like', true);
    } catch (error) {
      console.error('Failed to submit like feedback:', error);
    }
  }
  
  /**
   * 处理用户收藏 - 保持在显示列表中
   */
  async handleBookmark(paperId: string): Promise<void> {
    this.localFilters.bookmarkedToday.add(paperId);
    
    try {
      await submitFeedback(paperId, 'bookmark', true);
    } catch (error) {
      console.error('Failed to submit bookmark feedback:', error);
    }
  }
  
  /**
   * 获取当前论文
   */
  getCurrentPaper(): Paper | null {
    if (this.displayPapers.length === 0) return null;
    return this.displayPapers[this.currentIndex];
  }
  
  /**
   * 移动到下一篇 (循环)
   */
  next(): Paper | null {
    if (this.displayPapers.length === 0) return null;
    this.currentIndex = (this.currentIndex + 1) % this.displayPapers.length;
    return this.getCurrentPaper();
  }
  
  /**
   * 移动到上一篇 (循环)
   */
  previous(): Paper | null {
    if (this.displayPapers.length === 0) return null;
    this.currentIndex = (this.currentIndex - 1 + this.displayPapers.length) % this.displayPapers.length;
    return this.getCurrentPaper();
  }
  
  /**
   * 获取剩余论文数量
   */
  getRemainingCount(): number {
    return this.displayPapers.length;
  }
  
  /**
   * 检查论文的交互状态
   */
  getPaperStatus(paperId: string): {
    liked: boolean;
    bookmarked: boolean;
    disliked: boolean;
  } {
    return {
      liked: this.localFilters.likedToday.has(paperId),
      bookmarked: this.localFilters.bookmarkedToday.has(paperId),
      disliked: this.localFilters.dislikedToday.has(paperId)
    };
  }
  
  /**
   * 更新显示论文列表 - 过滤不感兴趣的论文
   */
  private updateDisplayPapers(): void {
    this.displayPapers = this.serverRecommendations.filter(paper => 
      !this.localFilters.dislikedToday.has(paper.id)
    );
  }
  
  /**
   * 调整当前索引，避免越界
   */
  private adjustCurrentIndex(): void {
    if (this.displayPapers.length === 0) {
      this.currentIndex = 0;
    } else if (this.currentIndex >= this.displayPapers.length) {
      this.currentIndex = 0;
    }
  }
  
  /**
   * 加载更多推荐
   */
  private async loadMoreRecommendations(): Promise<void> {
    const cursor = this.serverRecommendations.length;
    await this.loadRecommendations('arxiv', cursor);
  }
  
  /**
   * 重置当日过滤器 (新的一天开始时调用)
   */
  resetDailyFilters(): void {
    this.localFilters = {
      dislikedToday: new Set(),
      likedToday: new Set(),
      bookmarkedToday: new Set()
    };
    this.updateDisplayPapers();
  }
}

// 使用示例
const recommendationManager = new MultiLayerRecommendationManager();

// 初始化加载
await recommendationManager.loadRecommendations('arxiv');

// 用户交互处理
const handleUserDislike = async () => {
  const currentPaper = recommendationManager.getCurrentPaper();
  if (currentPaper) {
    await recommendationManager.handleDislike(currentPaper.id);
  }
};

const handleUserLike = async () => {
  const currentPaper = recommendationManager.getCurrentPaper();
  if (currentPaper) {
    await recommendationManager.handleLike(currentPaper.id);
  }
};

// 导航
const nextPaper = () => recommendationManager.next();
const previousPaper = () => recommendationManager.previous();

// 获取状态
const getCurrentStatus = () => {
  const paper = recommendationManager.getCurrentPaper();
  if (paper) {
    return recommendationManager.getPaperStatus(paper.id);
  }
  return null;
};

export {
  MultiLayerRecommendationManager,
  handleUserDislike,
  handleUserLike,
  nextPaper,
  previousPaper,
  getCurrentStatus
};
