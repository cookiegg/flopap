/**
 * Pool Settings Service - 数据源池设置 API
 */
import axios from 'axios';
import { getApiBaseUrl } from './backendService';

const API_BASE = getApiBaseUrl();

export interface PoolSettings {
    pool_ratio: number;  // 0.0-1.0
    max_pool_size: number;
    show_mode: 'pool' | 'all';
    filter_no_content: boolean;
}

export interface PoolSettingsResponse extends PoolSettings {
    user_id: string;
    source_key: string;
    updated_at: string;
}

/**
 * 获取数据源池设置
 */
export const getPoolSettings = async (sourceKey: string): Promise<PoolSettingsResponse> => {
    const response = await axios.get(`${API_BASE}/v1/pool-settings/${sourceKey}`, {
        headers: {
            'Authorization': `Bearer default`
        }
    });
    return response.data;
};

/**
 * 更新数据源池设置
 */
export const updatePoolSettings = async (sourceKey: string, settings: PoolSettings): Promise<{
    message: string;
    source_key: string;
    settings: PoolSettings;
}> => {
    const response = await axios.put(`${API_BASE}/v1/pool-settings/${sourceKey}`, settings, {
        headers: {
            'Authorization': `Bearer default`
        }
    });
    return response.data;
};

/**
 * 获取所有数据源池设置
 */
export const getAllPoolSettings = async (): Promise<{
    user_id: string;
    settings: Array<{
        source_key: string;
        pool_ratio: number;
        max_pool_size: number;
        show_mode: string;
        filter_no_content: boolean;
    }>;
}> => {
    const response = await axios.get(`${API_BASE}/v1/pool-settings`, {
        headers: {
            'Authorization': `Bearer default`
        }
    });
    return response.data;
};
