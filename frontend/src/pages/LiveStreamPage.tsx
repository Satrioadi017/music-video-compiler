import { useEffect, useState } from 'react';
import { Plus, Play, Square, RotateCw, Trash2, Radio } from 'lucide-react';
import toast from 'react-hot-toast';
import { streamsApi } from '../services/api';
import type { LiveStreamItem } from '../types';

export default function LiveStreamPage() {
  const [streams, setStreams] = useState<LiveStreamItem[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({
    title: '',
    description: '',
    platforms: [] as string[],
    resolution: '1920x1080',
    bitrate: '4500k',
    fps: 30,
    video_source: '',
    is_24_7: false,
    auto_restart: true,
  });

  const fetchStreams = async () => {
    try {
      const res = await streamsApi.list();
      setStreams(res.data);
    } catch {
      toast.error('Failed to load streams');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchStreams(); }, []);

  const handleCreate = async () => {
    if (!form.title) { toast.error('Enter a title'); return; }
    try {
      await streamsApi.create(form as Partial<LiveStreamItem>);
      toast.success('Stream created');
      setShowCreate(false);
      setForm({ title: '', description: '', platforms: [], resolution: '1920x1080', bitrate: '4500k', fps: 30, video_source: '', is_24_7: false, auto_restart: true });
      fetchStreams();
    } catch {
      toast.error('Failed to create stream');
    }
  };

  const handleAction = async (id: string, action: string) => {
    try {
      await streamsApi.action(id, action);
      toast.success(`Stream ${action} initiated`);
      fetchStreams();
    } catch {
      toast.error(`Failed to ${action} stream`);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this stream?')) return;
    try {
      await streamsApi.delete(id);
      toast.success('Deleted');
      fetchStreams();
    } catch {
      toast.error('Failed to delete stream');
    }
  };

  const togglePlatform = (platform: string) => {
    setForm(prev => ({
      ...prev,
      platforms: prev.platforms.includes(platform)
        ? prev.platforms.filter(p => p !== platform)
        : [...prev.platforms, platform],
    }));
  };

  const statusConfig: Record<string, { color: string; label: string }> = {
    idle: { color: 'bg-gray-100 text-gray-700', label: 'Idle' },
    starting: { color: 'bg-yellow-100 text-yellow-700', label: 'Starting...' },
    live: { color: 'bg-red-100 text-red-700', label: 'LIVE' },
    paused: { color: 'bg-orange-100 text-orange-700', label: 'Paused' },
    stopping: { color: 'bg-yellow-100 text-yellow-700', label: 'Stopping...' },
    stopped: { color: 'bg-gray-100 text-gray-700', label: 'Stopped' },
    error: { color: 'bg-red-100 text-red-700', label: 'Error' },
  };

  if (loading) return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Live Streaming</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Manage 24/7 live streams across platforms</p>
        </div>
        <button onClick={() => setShowCreate(!showCreate)} className="btn-primary flex items-center">
          <Plus className="w-4 h-4 mr-2" /> New Stream
        </button>
      </div>

      {showCreate && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Create Stream</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Title</label>
              <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} className="input-field" placeholder="Stream title" />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Description</label>
              <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className="input-field" rows={2} />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Platforms</label>
              <div className="flex flex-wrap gap-2">
                {['youtube', 'facebook', 'tiktok', 'instagram', 'twitter'].map((p) => (
                  <button
                    key={p}
                    onClick={() => togglePlatform(p)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                      form.platforms.includes(p)
                        ? 'bg-primary-600 text-white'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-400'
                    }`}
                  >
                    {p.charAt(0).toUpperCase() + p.slice(1)}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Video Source</label>
              <input value={form.video_source} onChange={(e) => setForm({ ...form, video_source: e.target.value })} className="input-field" placeholder="/path/to/video.mp4 or RTMP URL" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Resolution</label>
              <select value={form.resolution} onChange={(e) => setForm({ ...form, resolution: e.target.value })} className="input-field">
                <option value="1280x720">720p</option>
                <option value="1920x1080">1080p</option>
                <option value="3840x2160">4K</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Bitrate</label>
              <select value={form.bitrate} onChange={(e) => setForm({ ...form, bitrate: e.target.value })} className="input-field">
                <option value="2500k">2500k (720p)</option>
                <option value="4500k">4500k (1080p)</option>
                <option value="8000k">8000k (1080p HQ)</option>
                <option value="30000k">30000k (4K)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">FPS</label>
              <select value={form.fps} onChange={(e) => setForm({ ...form, fps: Number(e.target.value) })} className="input-field">
                <option value={24}>24</option>
                <option value={30}>30</option>
                <option value={60}>60</option>
              </select>
            </div>
            <div className="md:col-span-2 flex space-x-6">
              <label className="flex items-center space-x-2">
                <input type="checkbox" checked={form.is_24_7} onChange={(e) => setForm({ ...form, is_24_7: e.target.checked })} className="rounded" />
                <span className="text-sm text-gray-700 dark:text-gray-300">24/7 Nonstop</span>
              </label>
              <label className="flex items-center space-x-2">
                <input type="checkbox" checked={form.auto_restart} onChange={(e) => setForm({ ...form, auto_restart: e.target.checked })} className="rounded" />
                <span className="text-sm text-gray-700 dark:text-gray-300">Auto Restart on Failure</span>
              </label>
            </div>
          </div>
          <div className="mt-4 flex space-x-3">
            <button onClick={handleCreate} className="btn-primary">Create Stream</button>
            <button onClick={() => setShowCreate(false)} className="btn-secondary">Cancel</button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {streams.map((stream) => {
          const config = statusConfig[stream.status] || statusConfig.idle;
          return (
            <div key={stream.id} className="card">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-white">{stream.title}</h3>
                  <div className="flex items-center space-x-2 mt-1">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${config.color}`}>
                      {stream.status === 'live' && <span className="inline-block w-1.5 h-1.5 bg-red-500 rounded-full mr-1 animate-pulse"></span>}
                      {config.label}
                    </span>
                    {stream.is_24_7 && <span className="text-xs px-2 py-0.5 rounded-full bg-purple-100 text-purple-700">24/7</span>}
                  </div>
                </div>
                <button onClick={() => handleDelete(stream.id)} className="text-gray-400 hover:text-red-500">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              <div className="text-sm text-gray-500 space-y-1 mb-4">
                <p>Resolution: {stream.resolution} | {stream.fps}fps | {stream.bitrate}</p>
                <p>Platforms: {stream.platforms.join(', ') || 'None'}</p>
                {stream.viewer_count > 0 && <p>Viewers: {stream.viewer_count}</p>}
              </div>

              <div className="flex space-x-2">
                {['idle', 'stopped', 'error'].includes(stream.status) && (
                  <button onClick={() => handleAction(stream.id, 'start')} className="btn-primary flex items-center text-sm">
                    <Play className="w-3 h-3 mr-1" /> Start
                  </button>
                )}
                {stream.status === 'live' && (
                  <>
                    <button onClick={() => handleAction(stream.id, 'stop')} className="btn-danger flex items-center text-sm">
                      <Square className="w-3 h-3 mr-1" /> Stop
                    </button>
                    <button onClick={() => handleAction(stream.id, 'restart')} className="btn-secondary flex items-center text-sm">
                      <RotateCw className="w-3 h-3 mr-1" /> Restart
                    </button>
                  </>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {streams.length === 0 && !showCreate && (
        <div className="text-center py-12">
          <Radio className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No streams configured. Create one to start streaming!</p>
        </div>
      )}
    </div>
  );
}
