import { useState } from 'react';
import JobList from './components/JobList';
import JobForm from './components/JobForm';
import JobView from './components/JobView';
import JobSearch from './components/JobSearch';
import BulkAddModal from './components/BulkAddModal';
import ProfileEditor from './components/ProfileEditor';
import GapAnalysis from './components/GapAnalysis';
import { jobsApi } from './services/api';
import type { Job } from './types/job';

type ViewMode = 'list' | 'view' | 'edit' | 'create' | 'search' | 'profile' | 'gaps';

function App() {
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [currentJob, setCurrentJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [importUrl, setImportUrl] = useState<string | null>(null);
  const [showBulkAdd, setShowBulkAdd] = useState(false);
  const [jobListKey, setJobListKey] = useState(0);

  const handleBulkAddClose = (createdAny: boolean) => {
    setShowBulkAdd(false);
    if (createdAny) {
      setJobListKey((k) => k + 1); // Remount JobList so new entries appear
    }
  };

  const handleNewJob = () => {
    setCurrentJob(null);
    setImportUrl(null);
    setViewMode('create');
  };

  const handleImportFromSearch = (jobUrl: string) => {
    setCurrentJob(null);
    setImportUrl(jobUrl);
    setViewMode('create');
  };

  const handleViewJob = (job: Job) => {
    setCurrentJob(job);
    setViewMode('view');
  };

  const handleEditJob = (job: Job) => {
    setCurrentJob(job);
    setViewMode('edit');
  };

  const handleFormSuccess = () => {
    setViewMode('list');
    setCurrentJob(null);
  };

  const handleFormCancel = () => {
    setViewMode('list');
    setCurrentJob(null);
  };

  const handleViewClose = () => {
    setViewMode('list');
    setCurrentJob(null);
  };

  const handleViewEdit = () => {
    if (currentJob) {
      setViewMode('edit');
    }
  };

  const handleViewDelete = async () => {
    if (currentJob) {
      try {
        await jobsApi.deleteJob(currentJob.id);
        setError(null);
        setViewMode('list');
        setCurrentJob(null);
      } catch (err) {
        setError('Failed to delete job. Please try again.');
        console.error('Error deleting job:', err);
      }
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold text-gray-900">
              CV Maker - Job Application Tracker
            </h1>
            {(viewMode === 'list' || viewMode === 'search') && (
              <div className="flex gap-3">
                <button
                  onClick={() => setViewMode('gaps')}
                  className="bg-gray-600 text-white px-6 py-2 rounded-md hover:bg-gray-700 transition-colors font-medium"
                >
                  📊 Gaps
                </button>
                <button
                  onClick={() => setViewMode('profile')}
                  className="bg-gray-600 text-white px-6 py-2 rounded-md hover:bg-gray-700 transition-colors font-medium"
                >
                  👤 Profile
                </button>
                <button
                  onClick={() => setViewMode(viewMode === 'search' ? 'list' : 'search')}
                  className="bg-gray-600 text-white px-6 py-2 rounded-md hover:bg-gray-700 transition-colors font-medium"
                >
                  {viewMode === 'search' ? '← My Jobs' : '🔍 Search Jobs'}
                </button>
                <button
                  onClick={() => setShowBulkAdd(true)}
                  className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition-colors font-medium"
                >
                  📥 Bulk Add
                </button>
                <button
                  onClick={handleNewJob}
                  className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition-colors font-medium"
                >
                  + Add New Job
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
            <p className="text-red-800">{error}</p>
          </div>
        )}
        {viewMode === 'list' && (
          <JobList
            key={jobListKey}
            onView={handleViewJob}
            onEdit={handleEditJob}
          />
        )}
        {viewMode === 'view' && currentJob && (
          <JobView
            job={currentJob}
            onEdit={handleViewEdit}
            onClose={handleViewClose}
            onDelete={handleViewDelete}
          />
        )}
        {viewMode === 'search' && (
          <JobSearch onImport={handleImportFromSearch} />
        )}
        {viewMode === 'profile' && (
          <ProfileEditor onClose={() => setViewMode('list')} />
        )}
        {viewMode === 'gaps' && (
          <div className="space-y-4">
            <button
              onClick={() => setViewMode('list')}
              className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300"
            >
              ← Back to jobs
            </button>
            <GapAnalysis />
          </div>
        )}
        {(viewMode === 'edit' || viewMode === 'create') && (
          <JobForm
            job={currentJob}
            onSuccess={handleFormSuccess}
            onCancel={handleFormCancel}
            initialParseUrl={importUrl ?? undefined}
            onOpenExisting={handleViewJob}
          />
        )}
      </main>

      {showBulkAdd && <BulkAddModal onClose={handleBulkAddClose} />}

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 text-center text-gray-500 text-sm">
          CV Maker - Track your job applications efficiently
        </div>
      </footer>
    </div>
  );
}

export default App;
