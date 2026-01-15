/**
 * Data Source Service - 动态数据源管理
 */

import { getApiBaseUrl } from './backendService';

const API_BASE = getApiBaseUrl();

export interface SubSource {
    id: string;
    name: string;
}

export interface DataSourceInfo {
    id: string;
    name: string;
    type: 'streaming' | 'conference';
    paper_count?: number;
    sub_sources?: SubSource[];
}

export interface ConferenceInfo {
    id: string;
    name: string;
    file_size_mb: number;
    imported: boolean;
    paper_count: number;
    status: {
        import?: { status: string; count?: number; error?: string; last_run_at?: string };
        pool?: { status: string; count?: number; error?: string; last_run_at?: string };
        content?: { status: string; count?: number; error?: string; last_run_at?: string };
    };
}

/**
 * 获取所有可用的数据源
 */
export async function getDataSources(): Promise<DataSourceInfo[]> {
    const response = await fetch(`${API_BASE}/v1/data-sources`, {
        headers: {
            'Authorization': 'Bearer default',
        },
    });

    if (!response.ok) {
        throw new Error('Failed to fetch data sources');
    }

    const data = await response.json();
    return data.data_sources;
}

/**
 * 获取可用的会议列表 (包括未导入的)
 */
export async function getAvailableConferences(): Promise<ConferenceInfo[]> {
    const response = await fetch(`${API_BASE}/v1/factory/conferences`, {
        headers: {
            'Authorization': 'Bearer default',
        },
    });

    if (!response.ok) {
        throw new Error('Failed to fetch conferences');
    }

    const data = await response.json();
    return data.conferences;
}

/**
 * 触发会议导入
 */
export async function triggerConferenceImport(confId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/v1/factory/conference/${confId}/import`, {
        method: 'POST',
        headers: {
            'Authorization': 'Bearer default',
            'Content-Type': 'application/json',
        },
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to trigger import');
    }
}

/**
 * 触发会议推荐池生成
 */
export async function triggerConferencePool(
    confId: string,
    forceUpdate: boolean = false,
    poolRatio: number = 0.2
): Promise<void> {
    const response = await fetch(`${API_BASE}/v1/factory/conference/${confId}/pool`, {
        method: 'POST',
        headers: {
            'Authorization': 'Bearer default',
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            force_update: forceUpdate,
            pool_ratio: poolRatio
        }),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to trigger pool generation');
    }
}

/**
 * 触发会议内容生成
 * @param contentScope - "all" 全部论文 或 "pool" 仅推荐池 (从 user_paper_rankings 获取)
 */
export async function triggerConferenceContent(
    confId: string,
    steps: string[] = ['trans', 'ai'],
    contentScope: 'all' | 'pool' = 'all',
    poolRatio: number = 0.2
): Promise<void> {
    const response = await fetch(`${API_BASE}/v1/factory/conference/${confId}/content`, {
        method: 'POST',
        headers: {
            'Authorization': 'Bearer default',
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            steps,
            content_scope: contentScope,
            pool_ratio: poolRatio
        }),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to trigger content generation');
    }
}


