import { useEffect, useState } from 'react';
import { gapApi } from '../services/api';
import type { GapAnalysisResponse } from '../services/api';

const priorityColors: Record<string, string> = {
  Critical: 'bg-red-100 text-red-800',
  High: 'bg-orange-100 text-orange-800',
  Medium: 'bg-yellow-100 text-yellow-800',
  Low: 'bg-gray-100 text-gray-800',
};

export default function GapAnalysis() {
  const [report, setReport] = useState<GapAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    gapApi
      .getGapAnalysis()
      .then(setReport)
      .catch((err: { response?: { data?: { detail?: string } } }) => {
        setError(err.response?.data?.detail || 'Gap analysis failed.');
        console.error('Gap analysis error:', err);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="text-gray-500 py-8 text-center">Analyzing skill gaps across your tracked jobs…</div>;
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error}</p>
      </div>
    );
  }

  if (!report) return null;

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-1">Skill Gap Heatmap</h2>
        <p className="text-sm text-gray-500 mb-4">
          Across {report.jobs_analyzed} tracked job(s), weighted toward the postings you fit least —
          those are where the gaps bite. Skills already in your profile are excluded.
        </p>

        {report.heatmap.length === 0 ? (
          <p className="text-gray-500">No gaps found — your profile covers everything the tracked jobs ask for.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b border-gray-200">
                <th className="py-2 pr-4">Priority</th>
                <th className="py-2 pr-4">Skill / Area</th>
                <th className="py-2 pr-4">Type</th>
                <th className="py-2">Source</th>
              </tr>
            </thead>
            <tbody>
              {report.heatmap.map((entry, i) => (
                <tr key={i} className="border-b border-gray-100 last:border-b-0">
                  <td className="py-2 pr-4">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${priorityColors[entry.priority] ?? priorityColors.Low}`}>
                      {entry.priority}
                    </span>
                  </td>
                  <td className="py-2 pr-4 font-medium text-gray-900">{entry.area}</td>
                  <td className="py-2 pr-4 text-gray-600">{entry.type}</td>
                  <td className="py-2 text-gray-500">{entry.source}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
