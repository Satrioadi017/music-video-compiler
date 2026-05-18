import { useEffect, useState } from 'react';
import { Plus, Pause, Play, Trash2, Calendar } from 'lucide-react';
import toast from 'react-hot-toast';
import { format } from 'date-fns';
import { schedulesApi, contentApi } from '../services/api';
import type { Schedule, ContentItem } from '../types';

export default function SchedulerPage() {
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [content, setContent] = useState<ContentItem[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({
    content_item_id: '',
    scheduled_time: '',
    recurrence: 'once',
    timezone: 'UTC',
  });

  const fetchData = async () => {
    try {
      const [schedulesRes, contentRes] = await Promise.all([
        schedulesApi.list(),
        contentApi.list({ status: 'draft' }),
      ]);
      setSchedules(schedulesRes.data);
      setContent(contentRes.data);
    } catch {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const handleCreate = async () => {
    if (!form.content_item_id || !form.scheduled_time) { toast.error('Fill all required fields'); return; }
    try {
      await schedulesApi.create({
        content_item_id: form.content_item_id,
        scheduled_time: new Date(form.scheduled_time).toISOString(),
        recurrence: form.recurrence,
        timezone: form.timezone,
      } as Partial<Schedule>);
      toast.success('Schedule created');
      setShowCreate(false);
      fetchData();
    } catch {
      toast.error('Failed to create schedule');
    }
  };

  const handlePause = async (id: string) => {
    try {
      await schedulesApi.pause(id);
      toast.success('Schedule paused');
      fetchData();
    } catch {
      toast.error('Failed to pause schedule');
    }
  };

  const handleResume = async (id: string) => {
    try {
      await schedulesApi.resume(id);
      toast.success('Schedule resumed');
      fetchData();
    } catch {
      toast.error('Failed to resume schedule');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this schedule?')) return;
    try {
      await schedulesApi.delete(id);
      toast.success('Deleted');
      fetchData();
    } catch {
      toast.error('Failed to delete');
    }
  };

  const statusColors: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-700',
    processing: 'bg-blue-100 text-blue-700',
    completed: 'bg-green-100 text-green-700',
    failed: 'bg-red-100 text-red-700',
    cancelled: 'bg-gray-100 text-gray-700',
  };

  if (loading) return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Content Scheduler</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Schedule and automate content publishing</p>
        </div>
        <button onClick={() => setShowCreate(!showCreate)} className="btn-primary flex items-center">
          <Plus className="w-4 h-4 mr-2" /> New Schedule
        </button>
      </div>

      {showCreate && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Create Schedule</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Content</label>
              <select
                value={form.content_item_id}
                onChange={(e) => setForm({ ...form, content_item_id: e.target.value })}
                className="input-field"
              >
                <option value="">Select content</option>
                {content.map((c) => (
                  <option key={c.id} value={c.id}>{c.title || c.caption?.substring(0, 40) || 'Untitled'}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Scheduled Time</label>
              <input
                type="datetime-local"
                value={form.scheduled_time}
                onChange={(e) => setForm({ ...form, scheduled_time: e.target.value })}
                className="input-field"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Recurrence</label>
              <select value={form.recurrence} onChange={(e) => setForm({ ...form, recurrence: e.target.value })} className="input-field">
                {['once', 'daily', 'weekly', 'monthly'].map((r) => (
                  <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Timezone</label>
              <select value={form.timezone} onChange={(e) => setForm({ ...form, timezone: e.target.value })} className="input-field">
                <option value="UTC">UTC</option>
                <option value="Asia/Jakarta">Asia/Jakarta (WIB)</option>
                <option value="America/New_York">US Eastern</option>
                <option value="Europe/London">UK</option>
              </select>
            </div>
          </div>
          <div className="mt-4 flex space-x-3">
            <button onClick={handleCreate} className="btn-primary">Create Schedule</button>
            <button onClick={() => setShowCreate(false)} className="btn-secondary">Cancel</button>
          </div>
        </div>
      )}

      <div className="space-y-3">
        {schedules.map((schedule) => (
          <div key={schedule.id} className="card flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Calendar className="w-5 h-5 text-gray-400" />
              <div>
                <p className="font-medium text-gray-900 dark:text-white text-sm">
                  {format(new Date(schedule.scheduled_time), 'PPpp')}
                </p>
                <div className="flex items-center space-x-2 mt-1">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${statusColors[schedule.status]}`}>{schedule.status}</span>
                  <span className="text-xs text-gray-500 capitalize">{schedule.recurrence}</span>
                  {!schedule.is_active && <span className="text-xs text-gray-400">Paused</span>}
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {schedule.is_active ? (
                <button onClick={() => handlePause(schedule.id)} className="p-2 text-yellow-600 hover:bg-yellow-50 rounded-lg" title="Pause">
                  <Pause className="w-4 h-4" />
                </button>
              ) : (
                <button onClick={() => handleResume(schedule.id)} className="p-2 text-green-600 hover:bg-green-50 rounded-lg" title="Resume">
                  <Play className="w-4 h-4" />
                </button>
              )}
              <button onClick={() => handleDelete(schedule.id)} className="p-2 text-red-500 hover:bg-red-50 rounded-lg" title="Delete">
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {schedules.length === 0 && !showCreate && (
        <div className="text-center py-12">
          <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No schedules yet. Create one to automate publishing.</p>
        </div>
      )}
    </div>
  );
}
