export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string | null;
  is_active: boolean;
  avatar_url: string | null;
  created_at: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export type PlatformType = 'instagram' | 'youtube' | 'tiktok' | 'facebook' | 'twitter';
export type AccountStatus = 'active' | 'inactive' | 'expired' | 'suspended';
export type ContentType = 'text' | 'image' | 'video' | 'reel' | 'story' | 'carousel' | 'live';
export type ContentStatus = 'draft' | 'queued' | 'scheduled' | 'publishing' | 'published' | 'failed' | 'archived';
export type ScheduleStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
export type StreamStatus = 'idle' | 'starting' | 'live' | 'paused' | 'stopping' | 'stopped' | 'error';

export interface SocialAccount {
  id: string;
  platform: PlatformType;
  platform_user_id: string | null;
  platform_username: string | null;
  display_name: string | null;
  status: AccountStatus;
  followers_count: number;
  profile_data: Record<string, unknown>;
  created_at: string;
}

export interface ContentItem {
  id: string;
  content_type: ContentType;
  status: ContentStatus;
  title: string | null;
  caption: string | null;
  body: string | null;
  hashtags: string[];
  media_urls: string[];
  thumbnail_url: string | null;
  platform_post_id: string | null;
  platform_post_url: string | null;
  ai_generated: boolean;
  engagement_score: number;
  scheduled_at: string | null;
  published_at: string | null;
  created_at: string;
  social_account_id: string | null;
}

export interface Schedule {
  id: string;
  content_item_id: string;
  scheduled_time: string;
  status: ScheduleStatus;
  recurrence: string;
  recurrence_config: Record<string, unknown>;
  is_active: boolean;
  timezone: string;
  last_run_at: string | null;
  next_run_at: string | null;
  error_message: string | null;
  created_at: string;
}

export interface AnalyticsSummary {
  total_followers: number;
  total_impressions: number;
  total_reach: number;
  total_engagement: number;
  avg_engagement_rate: number;
  total_posts: number;
  total_video_views: number;
  total_revenue: number;
  period_start: string | null;
  period_end: string | null;
  daily_stats: AnalyticsRecord[];
}

export interface AnalyticsRecord {
  id: string;
  social_account_id: string;
  date: string;
  followers_count: number;
  followers_gained: number;
  followers_lost: number;
  posts_count: number;
  impressions: number;
  reach: number;
  engagement_rate: number;
  likes: number;
  comments: number;
  shares: number;
  saves: number;
  clicks: number;
  video_views: number;
  watch_time_hours: number;
  revenue: number;
}

export interface LiveStreamItem {
  id: string;
  title: string;
  description: string | null;
  status: StreamStatus;
  platforms: string[];
  resolution: string;
  bitrate: string;
  fps: number;
  video_source: string | null;
  audio_source: string | null;
  is_24_7: boolean;
  auto_restart: boolean;
  viewer_count: number;
  started_at: string | null;
  ended_at: string | null;
  created_at: string;
}

export interface Webhook {
  id: string;
  name: string;
  url: string;
  events: string[];
  is_active: boolean;
  last_triggered_at: string | null;
  last_response_status: number | null;
  last_error: string | null;
  failure_count: number;
  created_at: string;
}

export interface AIContentRequest {
  topic: string;
  platform: string;
  content_type: ContentType;
  tone: string;
  language: string;
  include_hashtags: boolean;
  include_caption: boolean;
  additional_instructions?: string;
}

export interface AIContentResponse {
  title: string | null;
  caption: string;
  body: string | null;
  hashtags: string[];
  suggested_media_prompt: string | null;
}
