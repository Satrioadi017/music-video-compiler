import { useEffect, useState } from 'react';
import { Plus, Send, Trash2, Edit, FileText } from 'lucide-react';
import toast from 'react-hot-toast';
import { contentApi, accountsApi } from '../services/api';
import type { ContentItem, ContentStatus, ContentType, SocialAccount } from '../types';

export default function ContentPage() {
  const [content, setContent] = useState<ContentItem[]>([]);
  const [accounts, setAccounts] = useState<SocialAccount[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [filter, setFilter] = useState<ContentStatus | ''>('');
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({
    content_type: 'text' as ContentType,
    title: '',
    caption: '',
    hashtags: '',
    social_account_id: '',
  });

  const fetchData = async () => {
    try {
      const [contentRes, accountsRes] = await Promise.all([
        contentApi.list({ status: filter || undefined }),
        accountsApi.list(),
      ]);
      setContent(contentRes.data);
      setAccounts(accountsRes.data);
    } catch {
      toast.error('Failed to load content');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [filter]);

  const handleCreate = async () => {
    try {
      await contentApi.create({
        content_type: form.content_type,
        title: form.title,
        caption: form.caption,
        hashtags: form.hashtags.split(',').map((h) => h.trim()).filter(Boolean),
        social_account_id: form.social_account_id || undefined,
      } as Partial<ContentItem>);
      toast.success('Content created');
      setShowCreate(false);
      setForm({ content_type: 'text', title: '', caption: '', hashtags: '', social_account_id: '' });
      fetchData();
    } catch {
      toast.error('Failed to create content');
    }
  };

  const handlePublish = async (id: string) => {
    try {
      await contentApi.publish(id);
      toast.success('Publishing...');
      fetchData();
    } catch {
      toast.error('Failed to publish');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this content?')) return;
    try {
      await contentApi.delete(id);
      toast.success('Deleted');
      fetchData();
    } catch {
      toast.error('Failed to delete');
    }
  };

  const statusColors: Record<string, string> = {
    draft: 'bg-gray-100 text-gray-700',
    published: 'bg-green-100 text-green-700',
    scheduled: 'bg-blue-100 text-blue-700',
    failed: 'bg-red-100 text-red-700',
    publishing: 'bg-yellow-100 text-yellow-700',
    queued: 'bg-indigo-100 text-indigo-700',
    archived: 'bg-gray-100 text-gray-500',
  };

  if (loading) return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Content Manager</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Create, manage, and publish content</p>
        </div>
        <button onClick={() => setShowCreate(!showCreate)} className="btn-primary flex items-center">
          <Plus className="w-4 h-4 mr-2" /> New Content
        </button>
      </div>

      {/* Filter */}
      <div className="flex space-x-2 overflow-x-auto">
        {['', 'draft', 'published', 'scheduled', 'failed'].map((s) => (
          <button
            key={s}
            onClick={() => setFilter(s as ContentStatus | '')}
            className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
              filter === s ? 'bg-primary-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-100 dark:bg-gray-800 dark:text-gray-400'
            }`}
          >
            {s || 'All'}
          </button>
        ))}
      </div>

      {/* Create Form */}
      {showCreate && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Create Content</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Type</label>
              <select
                value={form.content_type}
                onChange={(e) => setForm({ ...form, content_type: e.target.value as ContentType })}
                className="input-field"
              >
                {['text', 'image', 'video', 'reel', 'story', 'carousel'].map((t) => (
                  <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Account</label>
              <select
                value={form.social_account_id}
                onChange={(e) => setForm({ ...form, social_account_id: e.target.value })}
                className="input-field"
              >
                <option value="">Select account</option>
                {accounts.map((a) => (
                  <option key={a.id} value={a.id}>{a.display_name || a.platform_username} ({a.platform})</option>
                ))}
              </select>
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Title</label>
              <input
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                className="input-field"
                placeholder="Content title"
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Caption</label>
              <textarea
                value={form.caption}
                onChange={(e) => setForm({ ...form, caption: e.target.value })}
                className="input-field"
                rows={4}
                placeholder="Write your caption..."
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Hashtags (comma separated)</label>
              <input
                value={form.hashtags}
                onChange={(e) => setForm({ ...form, hashtags: e.target.value })}
                className="input-field"
                placeholder="#trending, #viral, #content"
              />
            </div>
          </div>
          <div className="mt-4 flex space-x-3">
            <button onClick={handleCreate} className="btn-primary">Create</button>
            <button onClick={() => setShowCreate(false)} className="btn-secondary">Cancel</button>
          </div>
        </div>
      )}

      {/* Content List */}
      <div className="space-y-3">
        {content.map((item) => (
          <div key={item.id} className="card flex items-center justify-between">
            <div className="flex-1 min-w-0 mr-4">
              <div className="flex items-center space-x-3">
                <FileText className="w-5 h-5 text-gray-400 flex-shrink-0" />
                <div className="min-w-0">
                  <p className="font-medium text-gray-900 dark:text-white truncate">
                    {item.title || item.caption?.substring(0, 60) || 'Untitled'}
                  </p>
                  <div className="flex items-center space-x-2 mt-1">
                    <span className="text-xs text-gray-500 capitalize">{item.content_type}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${statusColors[item.status]}`}>{item.status}</span>
                    {item.ai_generated && <span className="text-xs px-2 py-0.5 rounded-full bg-purple-100 text-purple-700">AI</span>}
                  </div>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {item.status === 'draft' && (
                <button onClick={() => handlePublish(item.id)} className="p-2 text-green-600 hover:bg-green-50 rounded-lg" title="Publish">
                  <Send className="w-4 h-4" />
                </button>
              )}
              <button onClick={() => handleDelete(item.id)} className="p-2 text-red-500 hover:bg-red-50 rounded-lg" title="Delete">
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {content.length === 0 && (
        <div className="text-center py-12">
          <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No content found. Create your first post!</p>
        </div>
      )}
    </div>
  );
}
