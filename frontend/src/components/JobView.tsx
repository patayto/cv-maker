import { useState } from 'react';
import type { Job } from '../types/job';
import SalaryCalculator from './SalaryCalculator';
import CVGenerator from './CVGenerator';
import CoverLetterEditor from './CoverLetterEditor';

interface JobViewProps {
  job: Job;
  onEdit: () => void;
  onClose: () => void;
  onDelete: () => void;
}

type TabType = 'details' | 'salary' | 'cv' | 'coverLetter';

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

export default function JobView({ job, onEdit, onClose, onDelete }: JobViewProps) {
  const [activeTab, setActiveTab] = useState<TabType>('details');

  const handleDelete = () => {
    if (confirm('Are you sure you want to delete this job application?')) {
      onDelete();
    }
  };

  const InfoRow = ({ label, value, link }: { label: string; value: string | null; link?: boolean }) => {
    if (!value) return null;

    return (
      <div className="py-3 border-b border-gray-200 last:border-b-0">
        <dt className="text-sm font-medium text-gray-500 mb-1">{label}</dt>
        <dd className="text-base text-gray-900">
          {link && value.startsWith('http') ? (
            <a
              href={value}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 hover:underline"
            >
              {value}
            </a>
          ) : link && value.startsWith('uploads/') ? (
            <a
              href={`http://127.0.0.1:8000/${value}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 hover:underline inline-flex items-center gap-1"
            >
              📄 View File
            </a>
          ) : (
            value
          )}
        </dd>
      </div>
    );
  };

  const DetailsTab = () => (
    <>
      {/* Job Details */}
      <dl className="bg-gray-50 rounded-lg p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Job Details</h3>
        <InfoRow label="Location" value={job.location} />
        <InfoRow label="Salary" value={job.salary} />
        <InfoRow label="Job Posting URL" value={job.url} link />
      </dl>

      {/* Dates */}
      {(job.opening_date || job.closing_date || job.application_date) && (
        <dl className="bg-gray-50 rounded-lg p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Important Dates</h3>
          <InfoRow label="Opening Date" value={job.opening_date} />
          <InfoRow label="Closing Date" value={job.closing_date} />
          <InfoRow label="Application Date" value={job.application_date} />
          <InfoRow label="Last Updated" value={job.last_update} />
        </dl>
      )}

      {/* Application Documents */}
      {(job.cv || job.cover_letter || job.other_questions) && (
        <dl className="bg-gray-50 rounded-lg p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Application Documents</h3>
          <InfoRow label="CV / Resume" value={job.cv} link />
          <InfoRow label="Cover Letter" value={job.cover_letter} link />
          <InfoRow label="Additional Questions/Responses" value={job.other_questions} link />
        </dl>
      )}

      {/* Notes */}
      {job.notes && (
        <div className="bg-gray-50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Notes</h3>
          <p className="text-gray-700 whitespace-pre-wrap">{job.notes}</p>
        </div>
      )}
    </>
  );

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div className="flex-1">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            {job.role || 'Untitled Position'}
          </h2>
          <p className="text-xl text-gray-600">
            {job.company || 'Unknown Company'}
            {job.department && ` • ${job.department}`}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={onEdit}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Edit
          </button>
          <button
            onClick={handleDelete}
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
          >
            Delete
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition-colors"
          >
            Close
          </button>
        </div>
      </div>

      {/* Status Badge */}
      {job.status && (
        <div className="mb-6">
          <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${statusColors[job.status]}`}>
            {statusLabels[job.status]}
          </span>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex gap-4" aria-label="Tabs">
          <button
            onClick={() => setActiveTab('details')}
            className={`pb-3 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'details'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Details
          </button>
          <button
            onClick={() => setActiveTab('salary')}
            className={`pb-3 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'salary'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Salary Analysis
          </button>
          <button
            onClick={() => setActiveTab('cv')}
            className={`pb-3 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'cv'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            CV Generator
          </button>
          <button
            onClick={() => setActiveTab('coverLetter')}
            className={`pb-3 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'coverLetter'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Cover Letter
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'details' && <DetailsTab />}
        {activeTab === 'salary' && <SalaryCalculator initialSalary={job.salary || undefined} />}
        {activeTab === 'cv' && <CVGenerator job={job} />}
        {activeTab === 'coverLetter' && <CoverLetterEditor job={job} />}
      </div>
    </div>
  );
}
