import { useState, useEffect } from 'react';
import { jobsApi, contactApi } from '../services/api';
import type { Job, ApplicationStatus, StalenessInfo } from '../types/job';
import { StalenessIndicator } from './StalenessIndicator';
import { FollowUpModal } from './FollowUpModal';

interface JobListProps {
  onView: (job: Job) => void;
  onEdit: (job: Job) => void;
  refreshTrigger: number;
}

const statusColors: Record<string, string> = {
  yet_to_apply: 'bg-gray-100 text-gray-800',
  applied_waiting: 'bg-blue-100 text-blue-800',
  job_offered: 'bg-green-100 text-green-800',
  job_accepted: 'bg-emerald-100 text-emerald-800',
  application_rejected: 'bg-red-100 text-red-800',
  job_rejected: 'bg-orange-100 text-orange-800',
};

const statusLabels: Record<string, string> = {
  yet_to_apply: 'Yet to Apply',
  applied_waiting: 'Applied - Waiting',
  job_offered: 'Job Offered',
  job_accepted: 'Job Accepted',
  application_rejected: 'Application Rejected',
  job_rejected: 'Job Rejected',
};

export default function JobList({ onView, onEdit, refreshTrigger }: JobListProps) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<ApplicationStatus | ''>('');
  const [filterCompany, setFilterCompany] = useState('');
  const [stalenessMap, setStalenessMap] = useState<Record<number, StalenessInfo>>({});
  const [followUpJob, setFollowUpJob] = useState<Job | null>(null);

  useEffect(() => {
    fetchJobs();
  }, [refreshTrigger, filterStatus, filterCompany]);

  const fetchJobs = async () => {
    try {
      setLoading(true);
      setError(null);
      const params: any = {};
      if (filterStatus) params.status = filterStatus;
      if (filterCompany) params.company = filterCompany;

      const data = await jobsApi.getJobs(params);
      setJobs(data);

      // Load staleness info for each job
      loadStalenessInfo(data);
    } catch (err) {
      setError('Failed to fetch jobs. Make sure the backend server is running.');
      console.error('Error fetching jobs:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadStalenessInfo = async (jobsList: Job[]) => {
    const stalenessData: Record<number, StalenessInfo> = {};

    await Promise.all(
      jobsList.map(async (job) => {
        try {
          const info = await contactApi.getStaleness(job.id);
          stalenessData[job.id] = info;
        } catch (err) {
          console.error(`Failed to load staleness for job ${job.id}:`, err);
          // Provide default staleness if API fails
          stalenessData[job.id] = {
            days_since_update: null,
            staleness_level: 'gray',
            contact_count: 0,
            last_contact_date: null
          };
        }
      })
    );

    setStalenessMap(stalenessData);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this job application?')) return;

    try {
      await jobsApi.deleteJob(id);
      setJobs(jobs.filter(job => job.id !== id));
    } catch (err) {
      alert('Failed to delete job');
      console.error('Error deleting job:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-600">Loading jobs...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Filter by Status
            </label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as ApplicationStatus | '')}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Statuses</option>
              <option value="yet_to_apply">Yet to Apply</option>
              <option value="applied_waiting">Applied - Waiting</option>
              <option value="job_offered">Job Offered</option>
              <option value="job_accepted">Job Accepted</option>
              <option value="application_rejected">Application Rejected</option>
              <option value="job_rejected">Job Rejected</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Filter by Company
            </label>
            <input
              type="text"
              value={filterCompany}
              onChange={(e) => setFilterCompany(e.target.value)}
              placeholder="Search company..."
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Job List */}
      {jobs.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <p className="text-gray-500">No jobs found. Add your first job application!</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {jobs.map((job) => (
            <div key={job.id} className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-6">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-xl font-semibold text-gray-900">
                      {job.role || 'Untitled Position'}
                    </h3>
                    {job.status && (
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[job.status]}`}>
                        {statusLabels[job.status]}
                      </span>
                    )}
                    {stalenessMap[job.id] && (
                      <StalenessIndicator
                        daysSinceUpdate={stalenessMap[job.id].days_since_update}
                        level={stalenessMap[job.id].staleness_level}
                        contactCount={stalenessMap[job.id].contact_count}
                      />
                    )}
                  </div>
                  <p className="text-gray-600 mb-2">
                    {job.company || 'Unknown Company'}
                    {job.department && ` • ${job.department}`}
                  </p>
                  {job.location && (
                    <p className="text-sm text-gray-500 mb-2">📍 {job.location}</p>
                  )}
                  {job.salary && (
                    <p className="text-sm text-gray-500 mb-2">💰 {job.salary}</p>
                  )}
                  {job.application_date && (
                    <p className="text-sm text-gray-500">Applied: {job.application_date}</p>
                  )}
                  {job.notes && (
                    <p className="text-sm text-gray-600 mt-3 italic">{job.notes}</p>
                  )}
                </div>
                <div className="flex gap-2 ml-4">
                  <button
                    onClick={() => setFollowUpJob(job)}
                    className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
                    title="Send follow-up message"
                  >
                    Follow Up
                  </button>
                  <button
                    onClick={() => onView(job)}
                    className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
                  >
                    View
                  </button>
                  <button
                    onClick={() => onEdit(job)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(job.id)}
                    className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
                  >
                    Delete
                  </button>
                </div>
              </div>
              {job.url && (
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <a
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-600 hover:text-blue-800 hover:underline"
                  >
                    View Job Posting →
                  </a>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Follow-Up Modal */}
      {followUpJob && (
        <FollowUpModal
          job={followUpJob}
          onClose={() => setFollowUpJob(null)}
          onContactRecorded={() => {
            setFollowUpJob(null);
            fetchJobs(); // Refresh to update staleness indicators
          }}
        />
      )}
    </div>
  );
}
