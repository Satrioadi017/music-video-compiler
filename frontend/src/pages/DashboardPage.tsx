import { useEffect, useState } from 'react';
import {
  Users,
  Eye,
  ThumbsUp,
  TrendingUp,
  FileText,
  Radio,
  Calendar,
  Activity,
} from 'lucide-react';
import { analyticsApi, accountsApi, contentApi, streamsApi } from '../services/api';
import type { AnalyticsSummary, SocialAccount, ContentItem, LiveStreamItem } from '../types';

interface StatCardProps {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  change?: string;
  color: string;
}

function StatCard({ label, value, icon, change, color }: StatCardProps) {
  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500 dark:text-gray-400">{label}</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{value}</p>
          {change && (
            <p className="text-sm text-green-600 mt-1">
              <TrendingUp className="w-3 h-3 inline mr-1" />
              {change}
            </p>
          )}
        </div>
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${color}`}>
          {icon}
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [accounts, setAccounts] = useState<SocialAccount[]>([]);
  const [recentContent, setRecentContent] = useState<ContentItem[]>([]);
  const [streams, setStreams] = useState<LiveStreamItem[]>([]);

  useEffect(() => {
    Promise.all([
      analyticsApi.summary({ days: 30 }).catch(() => ({ data: null })),
      accountsApi.list().catch(() => ({ data: [] })),
      contentApi.list({ limit: 5 }).catch(() => ({ data: [] })),
      streamsApi.list().catch(() => ({ data: [] })),
    ]).then(([analyticsRes, accountsRes, contentRes, streamsRes]) => {
      setAnalytics(analyticsRes.data);
      setAccounts(accountsRes.data);
      setRecentContent(contentRes.data);
      setStreams(streamsRes.data);
    });
  }, []);

  const liveStreams = streams.filter((s) => s.status === 'live');

  const formatNumber = (num: number) => {
    if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
    if (num >= 1_000) return `${(num / 1_000).toFixed(1)}K`;
    return num.toString();
  };

  const statusColors: Record<string, string> = {
    draft: 'bg-gray-100 text-gray-700',
    published: 'bg-green-100 text-green-700',
    scheduled: 'bg-blue-100 text-blue-700',
    failed: 'bg-red-100 text-red-700',
    publishing: 'bg-yellow-100 text-yellow-700',
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">Overview of your social media performance</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Followers"
          value={formatNumber(analytics?.total_followers || 0)}
          icon={<Users className="w-6 h-6 text-blue-600" />}
          color="bg-blue-100 dark:bg-blue-900/30"
        />
        <StatCard
          label="Total Impressions"
          value={formatNumber(analytics?.total_impressions || 0)}
          icon={<Eye className="w-6 h-6 text-purple-600" />}
          color="bg-purple-100 dark:bg-purple-900/30"
        />
        <StatCard
          label="Engagement"
          value={formatNumber(analytics?.total_engagement || 0)}
          icon={<ThumbsUp className="w-6 h-6 text-green-600" />}
          color="bg-green-100 dark:bg-green-900/30"
        />
        <StatCard
          label="Engagement Rate"
          value={`${((analytics?.avg_engagement_rate || 0) * 100).toFixed(2)}%`}
          icon={<Activity className="w-6 h-6 text-orange-600" />}
          color="bg-orange-100 dark:bg-orange-900/30"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Connected Accounts */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
            <Users className="w-5 h-5 mr-2" /> Connected Accounts ({accounts.length})
          </h3>
          {accounts.length === 0 ? (
            <p className="text-gray-500 text-sm">No accounts connected yet.</p>
          ) : (
            <div className="space-y-3">
              {accounts.map((account) => (
                <div key={account.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center text-primary-700 text-xs font-bold uppercase">
                      {account.platform[0]}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white text-sm">
                        {account.display_name || account.platform_username}
                      </p>
                      <p className="text-xs text-gray-500 capitalize">{account.platform}</p>
                    </div>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full ${account.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                    {account.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Content */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
            <FileText className="w-5 h-5 mr-2" /> Recent Content
          </h3>
          {recentContent.length === 0 ? (
            <p className="text-gray-500 text-sm">No content created yet.</p>
          ) : (
            <div className="space-y-3">
              {recentContent.map((item) => (
                <div key={item.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                  <div className="flex-1 min-w-0 mr-3">
                    <p className="font-medium text-gray-900 dark:text-white text-sm truncate">
                      {item.title || item.caption?.substring(0, 50) || 'Untitled'}
                    </p>
                    <p className="text-xs text-gray-500 capitalize">{item.content_type}</p>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full whitespace-nowrap ${statusColors[item.status] || 'bg-gray-100 text-gray-700'}`}>
                    {item.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Live Streams & Quick Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
            <Radio className="w-5 h-5 mr-2 text-red-500" /> Live Streams
          </h3>
          {liveStreams.length === 0 ? (
            <p className="text-gray-500 text-sm">No active streams.</p>
          ) : (
            <div className="space-y-2">
              {liveStreams.map((stream) => (
                <div key={stream.id} className="flex items-center justify-between p-2 bg-red-50 dark:bg-red-900/20 rounded-lg">
                  <span className="text-sm font-medium text-gray-900 dark:text-white">{stream.title}</span>
                  <span className="flex items-center text-xs text-red-600">
                    <span className="w-2 h-2 bg-red-500 rounded-full mr-1 animate-pulse"></span>
                    LIVE
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
            <Calendar className="w-5 h-5 mr-2" /> Quick Stats
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Total Posts (30d)</span>
              <span className="font-semibold text-gray-900 dark:text-white">{analytics?.total_posts || 0}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Video Views</span>
              <span className="font-semibold text-gray-900 dark:text-white">{formatNumber(analytics?.total_video_views || 0)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Revenue</span>
              <span className="font-semibold text-gray-900 dark:text-white">${(analytics?.total_revenue || 0).toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Active Streams</span>
              <span className="font-semibold text-gray-900 dark:text-white">{liveStreams.length}</span>
            </div>
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Platform Coverage</h3>
          <div className="space-y-2">
            {['Instagram', 'YouTube', 'TikTok', 'Facebook', 'Twitter/X'].map((platform) => {
              const connected = accounts.some(
                (a) => a.platform === platform.toLowerCase().replace('/x', '')
              );
              return (
                <div key={platform} className="flex items-center justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-400">{platform}</span>
                  <span className={`px-2 py-0.5 rounded-full text-xs ${connected ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                    {connected ? 'Connected' : 'Not Connected'}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
