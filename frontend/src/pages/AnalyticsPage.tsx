import { useEffect, useState } from 'react';
import { BarChart3, TrendingUp, Eye, ThumbsUp, Users } from 'lucide-react';
import { analyticsApi } from '../services/api';
import type { AnalyticsSummary } from '../types';

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    analyticsApi.summary({ days })
      .then((res) => setAnalytics(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [days]);

  const formatNumber = (num: number) => {
    if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
    if (num >= 1_000) return `${(num / 1_000).toFixed(1)}K`;
    return num.toString();
  };

  if (loading) return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Analytics Dashboard</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Track your social media performance</p>
        </div>
        <select value={days} onChange={(e) => setDays(Number(e.target.value))} className="input-field w-auto">
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
          <option value={365}>Last year</option>
        </select>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-xl flex items-center justify-center">
              <Users className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Followers</p>
              <p className="text-xl font-bold text-gray-900 dark:text-white">{formatNumber(analytics?.total_followers || 0)}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/30 rounded-xl flex items-center justify-center">
              <Eye className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Impressions</p>
              <p className="text-xl font-bold text-gray-900 dark:text-white">{formatNumber(analytics?.total_impressions || 0)}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-green-100 dark:bg-green-900/30 rounded-xl flex items-center justify-center">
              <ThumbsUp className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Engagement</p>
              <p className="text-xl font-bold text-gray-900 dark:text-white">{formatNumber(analytics?.total_engagement || 0)}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-orange-100 dark:bg-orange-900/30 rounded-xl flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Engagement Rate</p>
              <p className="text-xl font-bold text-gray-900 dark:text-white">{((analytics?.avg_engagement_rate || 0) * 100).toFixed(2)}%</p>
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white flex items-center">
            <BarChart3 className="w-5 h-5 mr-2" /> Performance Overview
          </h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">Total Posts</span>
              <span className="font-semibold text-gray-900 dark:text-white">{analytics?.total_posts || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">Total Reach</span>
              <span className="font-semibold text-gray-900 dark:text-white">{formatNumber(analytics?.total_reach || 0)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">Video Views</span>
              <span className="font-semibold text-gray-900 dark:text-white">{formatNumber(analytics?.total_video_views || 0)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">Revenue</span>
              <span className="font-semibold text-green-600">${(analytics?.total_revenue || 0).toFixed(2)}</span>
            </div>
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Daily Trends</h3>
          {analytics?.daily_stats && analytics.daily_stats.length > 0 ? (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {analytics.daily_stats.slice(-10).reverse().map((stat) => (
                <div key={stat.id} className="flex items-center justify-between text-sm p-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                  <span className="text-gray-600 dark:text-gray-400">{stat.date}</span>
                  <div className="flex space-x-4">
                    <span className="text-gray-900 dark:text-white">{formatNumber(stat.impressions)} imp</span>
                    <span className="text-green-600">{stat.engagement_rate.toFixed(2)}%</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-center py-8">No analytics data available yet</p>
          )}
        </div>
      </div>
    </div>
  );
}
