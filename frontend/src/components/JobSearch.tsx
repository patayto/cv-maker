import { useState } from 'react';
import { jobsApi } from '../services/api';
import type { LinkedInJobCard } from '../services/api';

interface JobSearchProps {
  onImport: (jobUrl: string) => void;
}

export default function JobSearch({ onImport }: JobSearchProps) {
  const [keywords, setKeywords] = useState('');
  const [location, setLocation] = useState('');
  const [jobage, setJobage] = useState('');
  const [remote, setRemote] = useState('');
  const [page, setPage] = useState(1);
  const [results, setResults] = useState<LinkedInJobCard[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const search = async (targetPage: number) => {
    setLoading(true);
    setError(null);
    try {
      const data = await jobsApi.searchLinkedIn({
        keywords: keywords || undefined,
        location: location || undefined,
        jobage: jobage ? Number(jobage) : undefined,
        remote: remote || undefined,
        page: targetPage,
      });
      setResults(data.results);
      setPage(targetPage);
    } catch (err) {
      setError('Search failed. LinkedIn may be rate limiting; wait a minute and try again.');
      console.error('LinkedIn search error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    search(1);
  };

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Search LinkedIn Jobs</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label htmlFor="search-keywords" className="block text-sm font-medium text-gray-700 mb-1">
              Keywords
            </label>
            <input
              id="search-keywords"
              type="text"
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
              placeholder="e.g. python developer"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label htmlFor="search-location" className="block text-sm font-medium text-gray-700 mb-1">
              Location
            </label>
            <input
              id="search-location"
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder='e.g. "London, United Kingdom"'
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label htmlFor="search-jobage" className="block text-sm font-medium text-gray-700 mb-1">
              Posted within (days)
            </label>
            <input
              id="search-jobage"
              type="number"
              min={1}
              value={jobage}
              onChange={(e) => setJobage(e.target.value)}
              placeholder="e.g. 7"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label htmlFor="search-remote" className="block text-sm font-medium text-gray-700 mb-1">
              Workplace
            </label>
            <select
              id="search-remote"
              value={remote}
              onChange={(e) => setRemote(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Any</option>
              <option value="remote">Remote</option>
              <option value="hybrid">Hybrid</option>
              <option value="onsite">On-site</option>
            </select>
          </div>
        </div>
        <button
          type="submit"
          disabled={loading}
          className="mt-4 bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition-colors font-medium disabled:opacity-50"
        >
          {loading ? 'Searching…' : 'Search'}
        </button>
      </form>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {results !== null && !error && (
        results.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <p className="text-gray-500">No results{page > 1 ? ' on this page' : ''}. Try broader keywords or location.</p>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow divide-y divide-gray-200">
            {results.map((card) => (
              <div key={card.id} className="p-4 flex justify-between items-center gap-4">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <a
                      href={card.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-medium text-blue-600 hover:underline"
                    >
                      {card.title}
                    </a>
                    {card.tracked && (
                      <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        ✓ Tracked
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 truncate">
                    {card.company || 'Unknown company'}
                    {card.location && ` • ${card.location}`}
                    {card.date && ` • posted ${card.date}`}
                  </p>
                </div>
                <button
                  onClick={() => onImport(card.url)}
                  disabled={card.tracked}
                  className="shrink-0 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {card.tracked ? 'Imported' : 'Import'}
                </button>
              </div>
            ))}
          </div>
        )
      )}

      {results !== null && (results.length > 0 || page > 1) && (
        <div className="flex justify-between items-center">
          <button
            onClick={() => search(page - 1)}
            disabled={loading || page <= 1}
            className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md disabled:opacity-50"
          >
            ← Previous
          </button>
          <span className="text-sm text-gray-500">Page {page}</span>
          <button
            onClick={() => search(page + 1)}
            disabled={loading || results.length === 0}
            className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md disabled:opacity-50"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
