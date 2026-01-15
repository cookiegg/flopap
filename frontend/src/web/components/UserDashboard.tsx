/**
 * Framework V2 用户仪表板组件 - 简化版本
 */

import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Zap, Heart, Clock, Loader2 } from 'lucide-react';
import { getUsageStats } from '../../services/apiKeyService';
import type { UsageStats } from '../../services/apiKeyService';

interface UserDashboardProps {
  theme?: 'dark' | 'light';
}

interface DashboardStats {
  apiUsage: UsageStats;
  totalCalls: number;
  activeServices: number;
}

const UserDashboard: React.FC<UserDashboardProps> = ({ theme = 'dark' }) => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  const isDark = theme === 'dark';

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      const apiUsageData = getUsageStats();
      
      const totalCalls = Object.values(apiUsageData).reduce((sum, usage) => sum + usage.usage_count, 0);
      const activeServices = Object.keys(apiUsageData).length;

      setStats({
        apiUsage: apiUsageData,
        totalCalls,
        activeServices
      });
    } catch (error) {
      console.error('加载统计数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-12 space-y-4">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
        <span className={isDark ? 'text-gray-400' : 'text-gray-500'}>加载统计数据...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-20">
      {/* 统计卡片 */}
      <div className="space-y-4">
        <h3 className={`text-lg font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
          使用统计
        </h3>

        <div className="grid grid-cols-2 gap-3">
          <div className={`p-4 rounded-xl ${isDark ? 'bg-blue-500/10 border border-blue-500/20' : 'bg-blue-50 border border-blue-100'}`}>
            <div className="flex items-center gap-2 mb-2">
              <Zap size={18} className="text-blue-500" />
              <span className="text-sm font-bold text-blue-500">API调用</span>
            </div>
            <span className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
              {stats?.totalCalls || 0}
            </span>
          </div>

          <div className={`p-4 rounded-xl ${isDark ? 'bg-green-500/10 border border-green-500/20' : 'bg-green-50 border border-green-100'}`}>
            <div className="flex items-center gap-2 mb-2">
              <Heart size={18} className="text-green-500" />
              <span className="text-sm font-bold text-green-500">活跃服务</span>
            </div>
            <span className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
              {stats?.activeServices || 0}
            </span>
          </div>
        </div>
      </div>

      {/* 服务使用详情 */}
      {stats?.activeServices > 0 && (
        <div className="space-y-4">
          <h3 className={`text-lg font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
            服务使用详情
          </h3>

          <div className="space-y-3">
            {Object.entries(stats.apiUsage).map(([service, usage]) => (
              <div
                key={service}
                className={`p-4 rounded-xl border ${isDark ? 'bg-gray-800/40 border-white/5' : 'bg-white border-gray-100'}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className={`font-bold ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
                    {service.toUpperCase()}
                  </span>
                  <span className="text-sm text-blue-500 font-bold">
                    {usage.usage_count} 次调用
                  </span>
                </div>
                
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span>创建时间: {new Date(usage.created_at).toLocaleDateString()}</span>
                  <span>
                    最后使用: {usage.last_used_at 
                      ? new Date(usage.last_used_at).toLocaleDateString() 
                      : '从未使用'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 空状态 */}
      {stats?.activeServices === 0 && (
        <div className={`text-center py-12 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
          <BarChart3 size={48} className="mx-auto mb-4 opacity-50" />
          <p className="text-lg font-medium mb-2">暂无使用数据</p>
          <p className="text-sm">配置API密钥后开始使用AI功能</p>
        </div>
      )}
    </div>
  );
};

export default UserDashboard;
