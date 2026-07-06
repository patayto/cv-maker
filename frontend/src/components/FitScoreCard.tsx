import { useEffect, useState } from 'react';
import { fitApi } from '../services/api';
import type { FitEvaluation } from '../types/job';

interface FitScoreCardProps {
  jobId: number;
}

const DIMENSIONS: { key: keyof FitEvaluation; label: string; weight: string }[] = [
  { key: 'technical_skills', label: 'Technical skills', weight: '30%' },
  { key: 'experience_match', label: 'Experience match', weight: '25%' },
  { key: 'behavioral_fit', label: 'Behavioral fit', weight: '15%' },
  { key: 'career_alignment', label: 'Career alignment', weight: '30%' },
];

const verdictColor = (verdict: string): string => {
  if (verdict === 'Strong Fit') return 'bg-green-100 text-green-800';
  if (verdict === 'Good Fit') return 'bg-emerald-100 text-emerald-800';
  if (verdict === 'Moderate Fit') return 'bg-yellow-100 text-yellow-800';
  if (verdict === 'Weak Fit') return 'bg-orange-100 text-orange-800';
  return 'bg-red-100 text-red-800';
};

const barColor = (score: number): string => {
  if (score >= 75) return 'bg-green-500';
  if (score >= 60) return 'bg-emerald-500';
  if (score >= 45) return 'bg-yellow-500';
  return 'bg-red-500';
};

export default function FitScoreCard({ jobId }: FitScoreCardProps) {
  const [evaluation, setEvaluation] = useState<FitEvaluation | null>(null);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fitApi
      .getFit(jobId)
      .then((data) => { if (!cancelled) setEvaluation(data); })
      .catch(() => { /* 404 = not evaluated yet */ })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [jobId]);

  const handleEvaluate = async () => {
    setEvaluating(true);
    setError(null);
    try {
      setEvaluation(await fitApi.evaluateFit(jobId));
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e.response?.data?.detail || 'Fit evaluation failed.');
      console.error('Fit evaluation error:', err);
    } finally {
      setEvaluating(false);
    }
  };

  if (loading) {
    return <div className="text-gray-500 py-8 text-center">Loading fit evaluation…</div>;
  }

  return (
    <div className="space-y-4">
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {evaluation ? (
        <>
          <div className="flex items-center gap-4">
            <div className="text-4xl font-bold text-gray-900">{evaluation.overall_score}</div>
            <div>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${verdictColor(evaluation.verdict)}`}>
                {evaluation.verdict}
              </span>
              {!evaluation.location_pass && (
                <span className="ml-2 px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800">
                  ⚠ Location fail
                </span>
              )}
              <p className="text-xs text-gray-500 mt-1">
                Evaluated {new Date(evaluation.created_at).toLocaleDateString('en-GB')}
              </p>
            </div>
          </div>

          <div className="space-y-3">
            {DIMENSIONS.map(({ key, label, weight }) => {
              const score = evaluation[key] as number;
              return (
                <div key={key}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-700">{label} <span className="text-gray-400">({weight})</span></span>
                    <span className="font-medium text-gray-900">{score}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${barColor(score)}`}
                      style={{ width: `${score}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {evaluation.key_strengths && evaluation.key_strengths.length > 0 && (
              <div className="bg-green-50 rounded-lg p-4">
                <h4 className="font-semibold text-green-900 mb-2">Key strengths</h4>
                <ul className="list-disc list-inside text-sm text-green-800 space-y-1">
                  {evaluation.key_strengths.map((s, i) => <li key={i}>{s}</li>)}
                </ul>
              </div>
            )}
            {evaluation.gaps && evaluation.gaps.length > 0 && (
              <div className="bg-orange-50 rounded-lg p-4">
                <h4 className="font-semibold text-orange-900 mb-2">Gaps to address</h4>
                <ul className="list-disc list-inside text-sm text-orange-800 space-y-1">
                  {evaluation.gaps.map((g, i) => <li key={i}>{g}</li>)}
                </ul>
              </div>
            )}
          </div>
        </>
      ) : (
        <p className="text-gray-500">
          Not evaluated yet. Scoring compares this job against your candidate profile.
        </p>
      )}

      <button
        onClick={handleEvaluate}
        disabled={evaluating}
        className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-medium disabled:opacity-50"
      >
        {evaluating ? 'Evaluating…' : evaluation ? 'Re-evaluate' : 'Evaluate fit'}
      </button>
    </div>
  );
}
