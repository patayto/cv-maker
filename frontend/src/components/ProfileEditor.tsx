import { useEffect, useState } from 'react';
import { profileApi } from '../services/api';

interface ProfileEditorProps {
  onClose: () => void;
}

export default function ProfileEditor({ onClose }: ProfileEditorProps) {
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    profileApi
      .getProfile()
      .then(setContent)
      .catch((err) => {
        setError('Failed to load profile.');
        console.error('Profile load error:', err);
      })
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      await profileApi.updateProfile(content);
      setSaved(true);
    } catch (err) {
      setError('Failed to save profile.');
      console.error('Profile save error:', err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="text-gray-500 py-8 text-center">Loading profile…</div>;
  }

  return (
    <div className="bg-white rounded-lg shadow p-6 space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Candidate Profile</h2>
          <p className="text-sm text-gray-500">
            Markdown. Drives fit scoring, CV generation, and gap analysis — richer detail gives sharper output.
          </p>
        </div>
        <button onClick={onClose} className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300">
          Close
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      )}
      {saved && !error && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-3">
          <p className="text-green-800 text-sm">Profile saved.</p>
        </div>
      )}

      <textarea
        value={content}
        onChange={(e) => { setContent(e.target.value); setSaved(false); }}
        rows={28}
        className="w-full border border-gray-300 rounded-md px-3 py-2 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        aria-label="Candidate profile markdown"
      />

      <button
        onClick={handleSave}
        disabled={saving}
        className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-medium disabled:opacity-50"
      >
        {saving ? 'Saving…' : 'Save profile'}
      </button>
    </div>
  );
}
