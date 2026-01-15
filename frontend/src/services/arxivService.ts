
import { Paper } from '../types';
import * as DB from './database';
import { generateMockPapers } from '../constants';

// Helper to get EST date (Used for UI display)
export const getTargetDateEST = (offsetDays: number = 3): { startStr: string; endStr: string; displayDate: string } => {
  const now = new Date();
  const estTimeStr = now.toLocaleString("en-US", { timeZone: "America/New_York" });
  const estDate = new Date(estTimeStr);
  estDate.setDate(estDate.getDate() - offsetDays);
  
  const yyyy = estDate.getFullYear();
  const mm = String(estDate.getMonth() + 1).padStart(2, '0');
  const dd = String(estDate.getDate()).padStart(2, '0');
  
  const dateStr = `${yyyy}${mm}${dd}`;
  
  return {
    startStr: `${dateStr}0000`,
    endStr: `${dateStr}2359`,
    displayDate: estDate.toLocaleDateString("en-US", { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
  };
};

// MOCK Implementation of ArXiv Fetching
export const fetchArxivPapers = async (
  startIndex: number, 
  maxResults: number, 
  categories: string[], 
  keywords: string[],
  searchPhrase?: string
): Promise<Paper[]> => {
  
  console.log(`[Mock Service] Fetching papers start=${startIndex} count=${maxResults}`);

  // Simulate Network Latency
  await new Promise(resolve => setTimeout(resolve, 800));

  // Generate Mock Data
  // We use the helper from constants, but modify IDs to be unique based on pagination
  const baseMocks = generateMockPapers(maxResults);
  
  const papers: Paper[] = baseMocks.map((p: any, index: number) => {
    // Deterministic pseudo-randomness for the demo
    const globalIndex = startIndex + index;
    const isSearch = !!searchPhrase;
    
    // Customize the mock data to look like it responded to the query
    let title = p.title;
    if (isSearch) {
        title = `[Result: ${searchPhrase}] ${title}`;
    }

    // Assign a consistent date
    const dateInfo = getTargetDateEST(3);

    return {
        ...p,
        id: `mock-paper-${globalIndex}`, // Unique ID for React keys
        title: title,
        publishedDate: dateInfo.displayDate,
        // Randomly assign categories from user preference if available, else defaults
        categories: categories.length > 0 ? [categories[index % categories.length], 'cs.AI'] : p.categories
    };
  });

  // --- CACHE LAYER (Preserved) ---
  // Even with mock data, we interact with DB to test the "Seen/Saved" logic
  const existingPapers = await DB.getPapersFromDB(papers.map(p => p.id));
  
  const mergedPapers = papers.map(newPaper => {
    const existing = existingPapers.find(ep => ep.id === newPaper.id);
    if (existing) {
      // Preserve AI data if we already have it in local DB
      return {
        ...newPaper,
        translatedTitle: existing.translatedTitle,
        translatedAbstract: existing.translatedAbstract,
        aiInsights: existing.aiInsights
      };
    }
    return newPaper;
  });

  if (mergedPapers.length > 0) {
    await DB.savePapersToDB(mergedPapers);
  }

  return mergedPapers;
};
