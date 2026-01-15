
import { Paper, UserPreferences } from '../types';

// Mock Data for NeurIPS 2024 (Simulating a large local JSON dataset)
const MOCK_NEURIPS_DATA: Paper[] = [
  {
    id: 'neurips-2024-001',
    title: 'DPO: Direct Preference Optimization',
    abstract: 'We propose a simple approach to fine-tuning large language models to align with human preferences without the need for complex reinforcement learning. Our method, DPO, optimizes the policy directly to satisfy preferences.',
    authors: ['Rafailov et al.'],
    categories: ['cs.LG', 'cs.AI'],
    publishedDate: '2023-12-01'
  },
  {
    id: 'neurips-2024-002',
    title: 'Gaussian Splatting for Real-Time Radiance Field Rendering',
    abstract: 'We present a method for real-time rendering of radiance fields using 3D Gaussian splatting. This allows for high-quality view synthesis at 100+ FPS.',
    authors: ['Kerbl et al.'],
    categories: ['cs.CV', 'cs.GR'],
    publishedDate: '2023-12-01'
  },
  {
    id: 'neurips-2024-003',
    title: 'Q-Transformer: Scalable Offline Reinforcement Learning',
    abstract: 'We adapt the Transformer architecture for offline reinforcement learning, enabling scalable Q-learning on large datasets.',
    authors: ['Chebotar et al.'],
    categories: ['cs.RO', 'cs.LG'],
    publishedDate: '2023-12-01'
  },
  {
    id: 'neurips-2024-004',
    title: 'Toolformer: Language Models Can Teach Themselves to Use Tools',
    abstract: 'Toolformer is a model trained to decide which APIs to call, when to call them, what arguments to pass, and how to best incorporate the results into future token prediction.',
    authors: ['Schick et al.'],
    categories: ['cs.CL', 'cs.AI'],
    publishedDate: '2023-12-01'
  },
  {
    id: 'neurips-2024-005',
    title: 'Segment Anything',
    abstract: 'We introduce the Segment Anything Model (SAM), a promptable segmentation system with zero-shot generalization to unfamiliar objects and images.',
    authors: ['Kirillov et al.'],
    categories: ['cs.CV'],
    publishedDate: '2023-12-01'
  },
  // Add 15 more generic ones to simulate scrolling
  ...Array.from({ length: 15 }).map((_, i) => ({
      id: `neurips-2024-gen-${i}`,
      title: `Advances in Neural Information Processing Systems #${i+1}`,
      abstract: `This paper discusses novel architectures for deep learning, specifically focusing on optimization landscapes and generalization bounds in high-dimensional spaces.`,
      authors: [`Researcher ${i}`],
      categories: i % 2 === 0 ? ['cs.LG'] : ['math.OC'],
      publishedDate: '2023-12-01'
  }))
];

// Ranking Algorithm
const calculateScore = (paper: Paper, prefs: UserPreferences): number => {
    let score = 0;
    
    // Category match
    const catMatch = paper.categories.some(c => prefs.selectedCategories.includes(c));
    if (catMatch) score += 5;

    // Keyword match (Case insensitive)
    const combinedText = (paper.title + ' ' + paper.abstract).toLowerCase();
    prefs.keywords.forEach(kw => {
        if (combinedText.includes(kw.toLowerCase())) {
            score += 10;
        }
    });

    return score;
};

export const fetchConferencePapers = async (
    startIndex: number,
    maxResults: number,
    prefs: UserPreferences
): Promise<Paper[]> => {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 500));

    // 1. Copy data
    let allPapers = [...MOCK_NEURIPS_DATA];

    // 2. Rank papers based on user preferences
    allPapers.sort((a, b) => {
        const scoreA = calculateScore(a, prefs);
        const scoreB = calculateScore(b, prefs);
        // Descending order
        return scoreB - scoreA;
    });

    // 3. Paginate
    return allPapers.slice(startIndex, startIndex + maxResults);
};
