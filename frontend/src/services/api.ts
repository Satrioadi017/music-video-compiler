import axios from 'axios';
import type {
  User,
  Token,
  SocialAccount,
  ContentItem,
  Schedule,
  AnalyticsSummary,
  AnalyticsRecord,
  LiveStreamItem,
  Webhook,
  AIContentRequest,
  AIContentResponse,
} from '../types';

const API_BASE = '/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth
export const authApi = {
  register: (data: { email: string; username: string; password: string; full_name?: string }) =>
    api.post<User>('/auth/register', data),
  login: (data: { email: string; password: string }) =>
    api.post<Token>('/auth/login', data),
  getMe: () => api.get<User>('/auth/me'),
  updateMe: (data: { full_name?: string; avatar_url?: string }) =>
    api.put<User>('/auth/me', data),
};

// Accounts
export const accountsApi = {
  list: () => api.get<SocialAccount[]>('/accounts/'),
  create: (data: Partial<SocialAccount>) => api.post<SocialAccount>('/accounts/', data),
  get: (id: string) => api.get<SocialAccount>(`/accounts/${id}`),
  update: (id: string, data: Partial<SocialAccount>) => api.put<SocialAccount>(`/accounts/${id}`, data),
  delete: (id: string) => api.delete(`/accounts/${id}`),
};

// Content
export const contentApi = {
  list: (params?: { status?: string; limit?: number; offset?: number }) =>
    api.get<ContentItem[]>('/content/', { params }),
  create: (data: Partial<ContentItem>) => api.post<ContentItem>('/content/', data),
  get: (id: string) => api.get<ContentItem>(`/content/${id}`),
  update: (id: string, data: Partial<ContentItem>) => api.put<ContentItem>(`/content/${id}`, data),
  delete: (id: string) => api.delete(`/content/${id}`),
  publish: (id: string) => api.post<ContentItem>(`/content/${id}/publish`),
  generateAI: (data: AIContentRequest) => api.post<AIContentResponse>('/content/ai/generate', data),
  generateHashtags: (data: { topic: string; platform: string; count?: number }) =>
    api.post<string[]>('/content/ai/hashtags', data),
  generateImage: (data: { prompt: string; size?: string; quality?: string }) =>
    api.post('/content/ai/image', data),
  generateCaption: (params: { topic: string; platform: string; language?: string }) =>
    api.post('/content/ai/caption', null, { params }),
};

// Schedules
export const schedulesApi = {
  list: (params?: { status?: string; is_active?: boolean }) =>
    api.get<Schedule[]>('/schedules/', { params }),
  create: (data: Partial<Schedule>) => api.post<Schedule>('/schedules/', data),
  get: (id: string) => api.get<Schedule>(`/schedules/${id}`),
  update: (id: string, data: Partial<Schedule>) => api.put<Schedule>(`/schedules/${id}`, data),
  delete: (id: string) => api.delete(`/schedules/${id}`),
  pause: (id: string) => api.post<Schedule>(`/schedules/${id}/pause`),
  resume: (id: string) => api.post<Schedule>(`/schedules/${id}/resume`),
};

// Analytics
export const analyticsApi = {
  summary: (params?: { social_account_id?: string; days?: number }) =>
    api.get<AnalyticsSummary>('/analytics/summary', { params }),
  accountAnalytics: (accountId: string, days?: number) =>
    api.get<AnalyticsRecord[]>(`/analytics/accounts/${accountId}`, { params: { days } }),
  platformBreakdown: (days?: number) =>
    api.get<Record<string, { accounts: string[]; total_impressions: number }>>('/analytics/platforms', { params: { days } }),
};

// Streams
export const streamsApi = {
  list: () => api.get<LiveStreamItem[]>('/streams/'),
  create: (data: Partial<LiveStreamItem>) => api.post<LiveStreamItem>('/streams/', data),
  get: (id: string) => api.get<LiveStreamItem>(`/streams/${id}`),
  update: (id: string, data: Partial<LiveStreamItem>) => api.put<LiveStreamItem>(`/streams/${id}`, data),
  delete: (id: string) => api.delete(`/streams/${id}`),
  action: (id: string, action: string) => api.post<LiveStreamItem>(`/streams/${id}/action`, { action }),
};

// Webhooks
export const webhooksApi = {
  list: () => api.get<Webhook[]>('/webhooks/'),
  create: (data: Partial<Webhook>) => api.post<Webhook>('/webhooks/', data),
  get: (id: string) => api.get<Webhook>(`/webhooks/${id}`),
  update: (id: string, data: Partial<Webhook>) => api.put<Webhook>(`/webhooks/${id}`, data),
  delete: (id: string) => api.delete(`/webhooks/${id}`),
  test: (id: string, data?: { event?: string; data?: Record<string, unknown> }) =>
    api.post(`/webhooks/${id}/test`, data),
};

export default api;
