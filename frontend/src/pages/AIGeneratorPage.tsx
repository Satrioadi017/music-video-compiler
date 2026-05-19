import { useState } from 'react';
import { Sparkles, Hash, Image, Type } from 'lucide-react';
import toast from 'react-hot-toast';
import { contentApi } from '../services/api';
import type { AIContentResponse, ContentType } from '../types';

export default function AIGeneratorPage() {
  const [activeTab, setActiveTab] = useState<'content' | 'hashtags' | 'image' | 'caption'>('content');
  const [loading, setLoading] = useState(false);

  // Content generation
  const [contentForm, setContentForm] = useState({
    topic: '',
    platform: 'instagram',
    content_type: 'text' as ContentType,
    tone: 'professional',
    language: 'id',
    include_hashtags: true,
    include_caption: true,
    additional_instructions: '',
  });
  const [generatedContent, setGeneratedContent] = useState<AIContentResponse | null>(null);

  // Hashtags
  const [hashtagForm, setHashtagForm] = useState({ topic: '', platform: 'instagram', count: 30 });
  const [generatedHashtags, setGeneratedHashtags] = useState<string[]>([]);

  // Image
  const [imageForm, setImageForm] = useState({ prompt: '', size: '1024x1024', quality: 'standard', style: 'vivid' });
  const [generatedImages, setGeneratedImages] = useState<string[]>([]);

  // Caption
  const [captionForm, setCaptionForm] = useState({ topic: '', platform: 'instagram', language: 'id' });
  const [generatedCaption, setGeneratedCaption] = useState('');

  const handleGenerateContent = async () => {
    if (!contentForm.topic) { toast.error('Enter a topic'); return; }
    setLoading(true);
    try {
      const res = await contentApi.generateAI(contentForm);
      setGeneratedContent(res.data);
      toast.success('Content generated!');
    } catch {
      toast.error('Failed to generate content');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateHashtags = async () => {
    if (!hashtagForm.topic) { toast.error('Enter a topic'); return; }
    setLoading(true);
    try {
      const res = await contentApi.generateHashtags(hashtagForm);
      setGeneratedHashtags(res.data);
      toast.success('Hashtags generated!');
    } catch {
      toast.error('Failed to generate hashtags');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateImage = async () => {
    if (!imageForm.prompt) { toast.error('Enter a prompt'); return; }
    setLoading(true);
    try {
      const res = await contentApi.generateImage(imageForm);
      setGeneratedImages(res.data.urls || []);
      if (res.data.error) toast.error(res.data.error);
      else toast.success('Image generated!');
    } catch {
      toast.error('Failed to generate image');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateCaption = async () => {
    if (!captionForm.topic) { toast.error('Enter a topic'); return; }
    setLoading(true);
    try {
      const res = await contentApi.generateCaption(captionForm);
      setGeneratedCaption(res.data.caption || '');
      toast.success('Caption generated!');
    } catch {
      toast.error('Failed to generate caption');
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'content', label: 'Content', icon: Type },
    { id: 'hashtags', label: 'Hashtags', icon: Hash },
    { id: 'image', label: 'Image', icon: Image },
    { id: 'caption', label: 'Caption', icon: Sparkles },
  ] as const;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">AI Generator</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">Generate content, hashtags, images, and captions with AI</p>
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 bg-gray-100 dark:bg-gray-800 rounded-xl p-1">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex-1 flex items-center justify-center space-x-2 py-2.5 rounded-lg text-sm font-medium transition-colors ${
              activeTab === id ? 'bg-white dark:bg-gray-700 text-primary-600 shadow-sm' : 'text-gray-600 dark:text-gray-400'
            }`}
          >
            <Icon className="w-4 h-4" />
            <span>{label}</span>
          </button>
        ))}
      </div>

      {/* Content Generator */}
      {activeTab === 'content' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Generate Content</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Topic</label>
                <input
                  value={contentForm.topic}
                  onChange={(e) => setContentForm({ ...contentForm, topic: e.target.value })}
                  className="input-field"
                  placeholder="e.g., Tips produktivitas kerja dari rumah"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Platform</label>
                  <select value={contentForm.platform} onChange={(e) => setContentForm({ ...contentForm, platform: e.target.value })} className="input-field">
                    {['instagram', 'youtube', 'tiktok', 'facebook', 'twitter'].map((p) => (
                      <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tone</label>
                  <select value={contentForm.tone} onChange={(e) => setContentForm({ ...contentForm, tone: e.target.value })} className="input-field">
                    {['professional', 'casual', 'humorous', 'inspirational', 'educational'].map((t) => (
                      <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Additional Instructions</label>
                <textarea
                  value={contentForm.additional_instructions}
                  onChange={(e) => setContentForm({ ...contentForm, additional_instructions: e.target.value })}
                  className="input-field"
                  rows={3}
                  placeholder="Any specific instructions..."
                />
              </div>
              <button onClick={handleGenerateContent} className="btn-primary w-full flex items-center justify-center" disabled={loading}>
                <Sparkles className="w-4 h-4 mr-2" />
                {loading ? 'Generating...' : 'Generate Content'}
              </button>
            </div>
          </div>

          <div className="card">
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Result</h3>
            {generatedContent ? (
              <div className="space-y-4">
                {generatedContent.title && (
                  <div>
                    <label className="text-sm font-medium text-gray-500">Title</label>
                    <p className="text-gray-900 dark:text-white font-medium">{generatedContent.title}</p>
                  </div>
                )}
                <div>
                  <label className="text-sm font-medium text-gray-500">Caption</label>
                  <p className="text-gray-900 dark:text-white whitespace-pre-wrap">{generatedContent.caption}</p>
                </div>
                {generatedContent.hashtags.length > 0 && (
                  <div>
                    <label className="text-sm font-medium text-gray-500">Hashtags</label>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {generatedContent.hashtags.map((tag, i) => (
                        <span key={i} className="text-xs px-2 py-1 bg-primary-100 text-primary-700 rounded-full">{tag}</span>
                      ))}
                    </div>
                  </div>
                )}
                {generatedContent.suggested_media_prompt && (
                  <div>
                    <label className="text-sm font-medium text-gray-500">Suggested Image Prompt</label>
                    <p className="text-gray-600 dark:text-gray-400 text-sm">{generatedContent.suggested_media_prompt}</p>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-gray-400 text-center py-8">Generated content will appear here</p>
            )}
          </div>
        </div>
      )}

      {/* Hashtag Generator */}
      {activeTab === 'hashtags' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Generate Hashtags</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Topic</label>
                <input
                  value={hashtagForm.topic}
                  onChange={(e) => setHashtagForm({ ...hashtagForm, topic: e.target.value })}
                  className="input-field"
                  placeholder="e.g., fitness motivation"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Platform</label>
                  <select value={hashtagForm.platform} onChange={(e) => setHashtagForm({ ...hashtagForm, platform: e.target.value })} className="input-field">
                    {['instagram', 'youtube', 'tiktok', 'facebook', 'twitter'].map((p) => (
                      <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Count</label>
                  <input type="number" value={hashtagForm.count} onChange={(e) => setHashtagForm({ ...hashtagForm, count: parseInt(e.target.value) || 30 })} className="input-field" min={1} max={50} />
                </div>
              </div>
              <button onClick={handleGenerateHashtags} className="btn-primary w-full" disabled={loading}>
                {loading ? 'Generating...' : 'Generate Hashtags'}
              </button>
            </div>
          </div>
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Generated Hashtags</h3>
            {generatedHashtags.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {generatedHashtags.map((tag, i) => (
                  <span key={i} className="text-sm px-3 py-1.5 bg-primary-100 text-primary-700 rounded-full cursor-pointer hover:bg-primary-200">{tag}</span>
                ))}
              </div>
            ) : (
              <p className="text-gray-400 text-center py-8">Hashtags will appear here</p>
            )}
          </div>
        </div>
      )}

      {/* Image Generator */}
      {activeTab === 'image' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Generate Image</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Prompt</label>
                <textarea
                  value={imageForm.prompt}
                  onChange={(e) => setImageForm({ ...imageForm, prompt: e.target.value })}
                  className="input-field"
                  rows={4}
                  placeholder="Describe the image you want..."
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Size</label>
                  <select value={imageForm.size} onChange={(e) => setImageForm({ ...imageForm, size: e.target.value })} className="input-field">
                    <option value="1024x1024">1024x1024</option>
                    <option value="1792x1024">1792x1024</option>
                    <option value="1024x1792">1024x1792</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Style</label>
                  <select value={imageForm.style} onChange={(e) => setImageForm({ ...imageForm, style: e.target.value })} className="input-field">
                    <option value="vivid">Vivid</option>
                    <option value="natural">Natural</option>
                  </select>
                </div>
              </div>
              <button onClick={handleGenerateImage} className="btn-primary w-full" disabled={loading}>
                {loading ? 'Generating...' : 'Generate Image'}
              </button>
            </div>
          </div>
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Generated Image</h3>
            {generatedImages.length > 0 ? (
              <div className="space-y-4">
                {generatedImages.map((url, i) => (
                  <img key={i} src={url} alt={`Generated ${i + 1}`} className="w-full rounded-lg" />
                ))}
              </div>
            ) : (
              <p className="text-gray-400 text-center py-8">Generated image will appear here</p>
            )}
          </div>
        </div>
      )}

      {/* Caption Generator */}
      {activeTab === 'caption' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Generate Caption</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Topic</label>
                <input
                  value={captionForm.topic}
                  onChange={(e) => setCaptionForm({ ...captionForm, topic: e.target.value })}
                  className="input-field"
                  placeholder="e.g., Morning coffee vibes"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Platform</label>
                <select value={captionForm.platform} onChange={(e) => setCaptionForm({ ...captionForm, platform: e.target.value })} className="input-field">
                  {['instagram', 'youtube', 'tiktok', 'facebook', 'twitter'].map((p) => (
                    <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>
                  ))}
                </select>
              </div>
              <button onClick={handleGenerateCaption} className="btn-primary w-full" disabled={loading}>
                {loading ? 'Generating...' : 'Generate Caption'}
              </button>
            </div>
          </div>
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Generated Caption</h3>
            {generatedCaption ? (
              <p className="text-gray-900 dark:text-white whitespace-pre-wrap">{generatedCaption}</p>
            ) : (
              <p className="text-gray-400 text-center py-8">Caption will appear here</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
