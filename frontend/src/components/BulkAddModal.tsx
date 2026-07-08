import { useState } from 'react';
import { isAxiosError } from 'axios';
import { jobsApi } from '../services/api';
import type { BulkAddResponse } from '../services/api';

interface BulkAddModalProps {
  onClose: (createdAny: boolean) => void;
}

const STATUS_STYLES: Record<string, { icon: string; badge: string; label: string }> = {
  created: { icon: '✅', badge: 'bg-green-100 text-green-800', label: 'Created' },
  duplicate: { icon: '⏭️', badge: 'bg-yellow-100 text-yellow-800', label: 'Duplicate' },
  failed: { icon: '❌', badge: 'bg-red-100 text-red-800', label: 'Failed' },
};

export default function BulkAddModal({ onClose }: BulkAddModalProps) {
  const [input, setInput] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<BulkAddResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const parseUrls = (text: string): string[] =>
    text
      .split(/[,\n]+/)
      .map((u) => u.trim())
      .filter((u) => u.length > 0);

  const urls = parseUrls(input);

  const handleSubmit = async () => {
    setError(null);
    setSubmitting(true);
    try {
      const response = await jobsApi.bulkAddJobs(urls);
      setResult(response);
    } catch (err) {
      const detail = isAxiosError(err) ? err.response?.data?.detail : null;
      setError(typeof detail === 'string' ? detail : 'Bulk add failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleClose = () => {
    onClose((result?.created ?? 0) > 0);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[85vh] flex flex-col">
        <div className="flex justify-between items-center px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">Bulk Add Jobs</h2>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
            aria-label="Close"
          >
            &times;
          </button>
        </div>

        <div className="px-6 py-4 overflow-y-auto flex-1">
          {!result ? (
            <>
              <p className="text-sm text-gray-600 mb-2">
                Paste job posting URLs separated by commas (or new lines). Each URL is parsed and
                added as a job entry automatically.
              </p>
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={submitting}
                rows={6}
                placeholder="https://example.com/job/1, https://example.com/job/2"
                className="w-full border border-gray-300 rounded-md p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
              />
              <p className="text-xs text-gray-500 mt-1">
                {urls.length} URL{urls.length === 1 ? '' : 's'} detected (max 20 per batch)
              </p>
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-md p-3 mt-3">
                  <p className="text-red-800 text-sm">{error}</p>
                </div>
              )}
              {submitting && (
                <div className="flex items-center gap-3 mt-4 text-gray-600">
                  <div className="animate-spin h-5 w-5 border-2 border-blue-600 border-t-transparent rounded-full" />
                  <span className="text-sm">
                    Parsing {urls.length} URL{urls.length === 1 ? '' : 's'}… this can take a minute.
                  </span>
                </div>
              )}
            </>
          ) : (
            <>
              {/* Summary */}
              <div className="grid grid-cols-3 gap-3 mb-4">
                <div className="bg-green-50 border border-green-200 rounded-md p-3 text-center">
                  <div className="text-2xl font-bold text-green-700">{result.created}</div>
                  <div className="text-xs text-green-800">Created</div>
                </div>
                <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3 text-center">
                  <div className="text-2xl font-bold text-yellow-700">{result.duplicates}</div>
                  <div className="text-xs text-yellow-800">Duplicates</div>
                </div>
                <div className="bg-red-50 border border-red-200 rounded-md p-3 text-center">
                  <div className="text-2xl font-bold text-red-700">{result.failed}</div>
                  <div className="text-xs text-red-800">Failed</div>
                </div>
              </div>

              {/* Per-URL results */}
              <ul className="divide-y divide-gray-100 border border-gray-200 rounded-md">
                {result.results.map((item) => {
                  const style = STATUS_STYLES[item.status] ?? STATUS_STYLES.failed;
                  return (
                    <li key={item.url} className="px-3 py-2 flex items-start gap-2">
                      <span>{style.icon}</span>
                      <div className="min-w-0 flex-1">
                        <div className="text-sm text-gray-900 truncate">
                          {item.role && item.company
                            ? `${item.role} at ${item.company}`
                            : item.url}
                        </div>
                        <div className="text-xs text-gray-500 truncate">{item.url}</div>
                        {item.error && (
                          <div className="text-xs text-red-600 mt-0.5">{item.error}</div>
                        )}
                      </div>
                      <span className={`text-xs px-2 py-0.5 rounded-full whitespace-nowrap ${style.badge}`}>
                        {style.label}
                      </span>
                    </li>
                  );
                })}
              </ul>
            </>
          )}
        </div>

        <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
          {!result ? (
            <>
              <button
                onClick={handleClose}
                disabled={submitting}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                disabled={submitting || urls.length === 0 || urls.length > 20}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {submitting ? 'Adding…' : `Add ${urls.length || ''} Job${urls.length === 1 ? '' : 's'}`}
              </button>
            </>
          ) : (
            <button
              onClick={handleClose}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Done
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
