import axios from 'axios';
import { getApiBaseUrl } from './backendService';

// Replicate API setup
const api = axios.create({
    baseURL: getApiBaseUrl(),
    timeout: 30000,
    proxy: false,
});

api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

const handleApiError = (error: unknown, context: string) => {
    console.error(`${context}:`, error);
};

export interface TaskStatus {
    status: 'idle' | 'running' | 'success' | 'success_empty' | 'error';
    count: number;
    last_date?: string;
    last_run_at?: string;
    error?: string;
    scope?: string;
}

export interface FactoryStatus {
    fetch_arxiv: TaskStatus;
    gen_candidate_pool: TaskStatus;
    gen_recommendation: TaskStatus;
    gen_content: TaskStatus;
}

export interface ContentGenOptions {
    target_date?: string;
    scope: 'candidate' | 'user';
    steps: ('trans' | 'ai' | 'tts')[];
}

export const getFactoryStatus = async (): Promise<FactoryStatus> => {
    try {
        const response = await api.get('/v1/factory/status');
        return response.data;
    } catch (error) {
        handleApiError(error, 'Failed to get factory status');
        throw error;
    }
};

export const triggerFetchArxiv = async (targetDate?: string) => {
    try {
        const response = await api.post('/v1/factory/fetch-arxiv', { target_date: targetDate });
        return response.data;
    } catch (error) {
        handleApiError(error, 'Failed to trigger arxiv fetch');
        throw error;
    }
};

export const triggerCandidatePool = async (targetDate?: string, category: string = 'cs') => {
    try {
        const response = await api.post('/v1/factory/candidate-pool', {
            target_date: targetDate,
            category
        });
        return response.data;
    } catch (error) {
        handleApiError(error, 'Failed to trigger candidate pool');
        throw error;
    }
};

export const triggerRecommendation = async (category: string = 'cs') => {
    try {
        const response = await api.post('/v1/factory/recommendation', { category });
        return response.data;
    } catch (error) {
        handleApiError(error, 'Failed to trigger recommendation');
        throw error;
    }
};

export const triggerContentGen = async (options: ContentGenOptions & { category?: string }) => {
    try {
        const response = await api.post('/v1/factory/content-gen', {
            ...options,
            category: options.category || 'cs'
        });
        return response.data;
    } catch (error) {
        handleApiError(error, 'Failed to trigger content generation');
        throw error;
    }
};
