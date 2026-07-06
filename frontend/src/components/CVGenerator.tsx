import { useEffect, useState } from 'react';
import { cvApi, API_BASE_URL } from '../services/api';
import type { CVGenerationResponse, BlockSuggestion } from '../services/api';
import type { Job } from '../types/job';

interface CVGeneratorProps {
  job: Job;
}

export default function CVGenerator({ job }: CVGeneratorProps) {
  const [suggestions, setSuggestions] = useState<BlockSuggestion[]>([]);
  const [result, setResult] = useState<CVGenerationResponse | null>(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showLatex, setShowLatex] = useState(false);

  useEffect(() => {
    let cancelled = false;
    cvApi
      .getCVSuggestions(job.id)
      .then((data) => { if (!cancelled) setSuggestions(data.suggestions.slice(0, 10)); })
      .catch((err) => console.error('CV suggestions error:', err));
    cvApi
      .getGeneratedCV(job.id)
      .then((existing) => { if (!cancelled && existing) setResult(existing); })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [job.id]);

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    try {
      setResult(await cvApi.generateCV(job.id));
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } }; message?: string };
      setError(e.response?.data?.detail || e.message || 'CV generation failed.');
      console.error('CV generation error:', err);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-4">
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-900">
          Generates a tailored 2-page CV (moderncv LaTeX → PDF) from your candidate profile
          and the best-matching achievement blocks, with an automatic review pass and
          page-count verification. Takes a minute or two.
        </p>
      </div>

      {suggestions.length > 0 && !result && (
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-2">Top matching blocks</h4>
          <ul className="space-y-1 text-sm text-gray-700">
            {suggestions.map((s) => (
              <li key={s.block_id} className="flex justify-between gap-4">
                <span className="truncate">{s.block?.title ?? `Block ${s.block_id}`}</span>
                <span className="text-gray-400 shrink-0">{Math.round(s.relevance_score)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {result && (
        <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-3">
          <div className="flex items-center gap-3 flex-wrap">
            <h4 className="font-semibold text-gray-900">Generated CV</h4>
            {result.checks &&
              Object.entries(result.checks).map(([check, passed]) => (
                <span
                  key={check}
                  className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                    passed ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}
                >
                  {passed ? '✓' : '✗'} {check.replace(/_/g, ' ')}
                </span>
              ))}
            {result.page_count != null && (
              <span className="text-sm text-gray-500">{result.page_count} page(s)</span>
            )}
          </div>
          {result.pdf_path && (
            <a
              href={`${API_BASE_URL}/${result.pdf_path}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
            >
              📄 Open PDF
            </a>
          )}
          <button
            onClick={() => setShowLatex(!showLatex)}
            className="ml-2 px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300"
          >
            {showLatex ? 'Hide LaTeX' : 'Show LaTeX'}
          </button>
          {showLatex && (
            <pre className="bg-gray-900 text-gray-100 rounded-md p-4 text-xs overflow-x-auto max-h-96">
              {result.latex}
            </pre>
          )}
        </div>
      )}

      <button
        onClick={handleGenerate}
        disabled={generating}
        className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-medium disabled:opacity-50"
      >
        {generating ? 'Generating (draft → review → compile)…' : result ? 'Regenerate CV' : 'Generate CV'}
      </button>
    </div>
  );
}
