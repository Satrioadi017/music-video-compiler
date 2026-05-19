import { useEffect, useState } from 'react';
import { Plus, Trash2, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';
import { accountsApi } from '../services/api';
import type { SocialAccount, PlatformType } from '../types';

const PLATFORMS: { value: PlatformType; label: string; color: string }[] = [
  { value: 'instagram', label: 'Instagram', color: 'bg-gradient-to-r from-purple-500 to-pink-500' },
  { value: 'youtube', label: 'YouTube', color: 'bg-red-600' },
  { value: 'tiktok', label: 'TikTok', color: 'bg-black' },
  { value: 'facebook', label: 'Facebook', color: 'bg-blue-600' },
  { value: 'twitter', label: 'Twitter/X', color: 'bg-gray-900' },
];

export default function AccountsPage() {
  const [accounts, setAccounts] = useState<SocialAccount[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [newAccount, setNewAccount] = useState({ platform: 'instagram' as PlatformType, platform_username: '', display_name: '' });
  const [loading, setLoading] = useState(true);

  const fetchAccounts = async () => {
    try {
      const res = await accountsApi.list();
      setAccounts(res.data);
    } catch {
      toast.error('Failed to load accounts');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAccounts(); }, []);

  const handleAdd = async () => {
    try {
      await accountsApi.create({
        platform: newAccount.platform,
        platform_username: newAccount.platform_username,
        display_name: newAccount.display_name,
      } as Partial<SocialAccount>);
      toast.success('Account added');
      setShowAdd(false);
      setNewAccount({ platform: 'instagram', platform_username: '', display_name: '' });
      fetchAccounts();
    } catch {
      toast.error('Failed to add account');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this account?')) return;
    try {
      await accountsApi.delete(id);
      toast.success('Account deleted');
      fetchAccounts();
    } catch {
      toast.error('Failed to delete account');
    }
  };

  if (loading) return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Social Accounts</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Manage your connected social media accounts</p>
        </div>
        <button onClick={() => setShowAdd(!showAdd)} className="btn-primary flex items-center">
          <Plus className="w-4 h-4 mr-2" /> Add Account
        </button>
      </div>

      {showAdd && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Add New Account</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Platform</label>
              <select
                value={newAccount.platform}
                onChange={(e) => setNewAccount({ ...newAccount, platform: e.target.value as PlatformType })}
                className="input-field"
              >
                {PLATFORMS.map((p) => (
                  <option key={p.value} value={p.value}>{p.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Username</label>
              <input
                value={newAccount.platform_username}
                onChange={(e) => setNewAccount({ ...newAccount, platform_username: e.target.value })}
                className="input-field"
                placeholder="@username"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Display Name</label>
              <input
                value={newAccount.display_name}
                onChange={(e) => setNewAccount({ ...newAccount, display_name: e.target.value })}
                className="input-field"
                placeholder="Display name"
              />
            </div>
          </div>
          <div className="mt-4 flex space-x-3">
            <button onClick={handleAdd} className="btn-primary">Add Account</button>
            <button onClick={() => setShowAdd(false)} className="btn-secondary">Cancel</button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {accounts.map((account) => {
          const platformInfo = PLATFORMS.find((p) => p.value === account.platform);
          return (
            <div key={account.id} className="card">
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm ${platformInfo?.color || 'bg-gray-500'}`}>
                    {account.platform[0].toUpperCase()}
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900 dark:text-white">
                      {account.display_name || account.platform_username || 'Unknown'}
                    </p>
                    <p className="text-sm text-gray-500 capitalize">{account.platform}</p>
                  </div>
                </div>
                <button onClick={() => handleDelete(account.id)} className="text-gray-400 hover:text-red-500">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
              <div className="mt-4 flex items-center justify-between">
                <div className="text-sm">
                  <span className="text-gray-500">Followers: </span>
                  <span className="font-medium text-gray-900 dark:text-white">{account.followers_count.toLocaleString()}</span>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full ${account.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                  {account.status}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {accounts.length === 0 && !showAdd && (
        <div className="text-center py-12">
          <RefreshCw className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No accounts connected. Click "Add Account" to get started.</p>
        </div>
      )}
    </div>
  );
}
