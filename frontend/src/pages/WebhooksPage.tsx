import { useEffect, useState } from 'react';
import { Plus, Trash2, TestTube2, Webhook } from 'lucide-react';
import toast from 'react-hot-toast';
import { webhooksApi } from '../services/api';
import type { Webhook as WebhookType } from '../types';

const EVENTS = [
  'content.published', 'content.failed',
  'schedule.triggered',
  'stream.started', 'stream.stopped', 'stream.error',
  'account.connected', 'account.disconnected',
  'analytics.updated',
];

export default function WebhooksPage() {
  const [webhooks, setWebhooks] = useState<WebhookType[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ name: '', url: '', secret: '', events: [] as string[] });

  const fetchWebhooks = async () => {
    try {
      const res = await webhooksApi.list();
      setWebhooks(res.data);
    } catch {
      toast.error('Failed to load webhooks');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchWebhooks(); }, []);

  const handleCreate = async () => {
    if (!form.name || !form.url) { toast.error('Fill name and URL'); return; }
    try {
      await webhooksApi.create(form as Partial<WebhookType>);
      toast.success('Webhook created');
      setShowCreate(false);
      setForm({ name: '', url: '', secret: '', events: [] });
      fetchWebhooks();
    } catch {
      toast.error('Failed to create webhook');
    }
  };

  const handleTest = async (id: string) => {
    try {
      const res = await webhooksApi.test(id, { event: 'test.ping', data: { message: 'Test ping' } });
      toast.success(`Test sent. Response: ${res.data.response_status}`);
    } catch {
      toast.error('Test failed');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this webhook?')) return;
    try {
      await webhooksApi.delete(id);
      toast.success('Deleted');
      fetchWebhooks();
    } catch {
      toast.error('Failed to delete');
    }
  };

  const toggleEvent = (event: string) => {
    setForm(prev => ({
      ...prev,
      events: prev.events.includes(event)
        ? prev.events.filter(e => e !== event)
        : [...prev.events, event],
    }));
  };

  if (loading) return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Webhooks</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Configure webhook endpoints for event notifications</p>
        </div>
        <button onClick={() => setShowCreate(!showCreate)} className="btn-primary flex items-center">
          <Plus className="w-4 h-4 mr-2" /> Add Webhook
        </button>
      </div>

      {showCreate && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">New Webhook</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Name</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="input-field" placeholder="My Webhook" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">URL</label>
              <input value={form.url} onChange={(e) => setForm({ ...form, url: e.target.value })} className="input-field" placeholder="https://example.com/webhook" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Secret (optional)</label>
              <input value={form.secret} onChange={(e) => setForm({ ...form, secret: e.target.value })} className="input-field" placeholder="Signing secret" />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Events</label>
              <div className="flex flex-wrap gap-2">
                {EVENTS.map((event) => (
                  <button
                    key={event}
                    onClick={() => toggleEvent(event)}
                    className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                      form.events.includes(event) ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                    }`}
                  >
                    {event}
                  </button>
                ))}
              </div>
            </div>
          </div>
          <div className="mt-4 flex space-x-3">
            <button onClick={handleCreate} className="btn-primary">Create</button>
            <button onClick={() => setShowCreate(false)} className="btn-secondary">Cancel</button>
          </div>
        </div>
      )}

      <div className="space-y-3">
        {webhooks.map((webhook) => (
          <div key={webhook.id} className="card">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="font-semibold text-gray-900 dark:text-white">{webhook.name}</h3>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${webhook.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                    {webhook.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
                <p className="text-sm text-gray-500 mt-1 font-mono">{webhook.url}</p>
                <div className="flex flex-wrap gap-1 mt-2">
                  {webhook.events.map((event) => (
                    <span key={event} className="text-xs px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded">{event}</span>
                  ))}
                </div>
                {webhook.failure_count > 0 && (
                  <p className="text-xs text-red-500 mt-2">Failures: {webhook.failure_count}</p>
                )}
              </div>
              <div className="flex space-x-2">
                <button onClick={() => handleTest(webhook.id)} className="p-2 text-primary-600 hover:bg-primary-50 rounded-lg" title="Test">
                  <TestTube2 className="w-4 h-4" />
                </button>
                <button onClick={() => handleDelete(webhook.id)} className="p-2 text-red-500 hover:bg-red-50 rounded-lg" title="Delete">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {webhooks.length === 0 && !showCreate && (
        <div className="text-center py-12">
          <Webhook className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No webhooks configured. Add one to receive event notifications.</p>
        </div>
      )}
    </div>
  );
}
