import { useState } from 'react';
import JobList from './components/JobList';
import JobForm from './components/JobForm';
import JobView from './components/JobView';
import { jobsApi } from './services/api';
import type { Job } from './types/job';

type ViewMode = 'list' | 'view' | 'edit' | 'create';

function App() {
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [currentJob, setCurrentJob] = useState<Job | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleNewJob = () => {
    setCurrentJob(null);
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
    setRefreshTrigger(prev => prev + 1);
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
        setViewMode('list');
        setCurrentJob(null);
        setRefreshTrigger(prev => prev + 1);
      } catch (err) {
        alert('Failed to delete job');
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
            {viewMode === 'list' && (
              <button
                onClick={handleNewJob}
                className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition-colors font-medium"
              >
                + Add New Job
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {viewMode === 'list' && (
          <JobList
            onView={handleViewJob}
            onEdit={handleEditJob}
            refreshTrigger={refreshTrigger}
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
        {(viewMode === 'edit' || viewMode === 'create') && (
          <JobForm
            job={currentJob}
            onSuccess={handleFormSuccess}
            onCancel={handleFormCancel}
          />
        )}
      </main>

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
