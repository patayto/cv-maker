import { useState, useEffect } from 'react';
import { jobsApi } from '../services/api';
import type { Job, JobCreate, ApplicationStatus } from '../types/job';

interface JobFormProps {
  job: Job | null;
  onSuccess: () => void;
  onCancel: () => void;
}

export default function JobForm({ job, onSuccess, onCancel }: JobFormProps) {
  const [formData, setFormData] = useState<JobCreate>({
    role: '',
    company: '',
    department: '',
    opening_date: '',
    closing_date: '',
    application_date: '',
    status: undefined,
    url: '',
    location: '',
    salary: '',
    notes: '',
    cv: '',
    cover_letter: '',
    other_questions: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [parsing, setParsing] = useState(false);
  const [parseUrl, setParseUrl] = useState('');
  const [missingFields, setMissingFields] = useState<string[]>([]);
  const [parsedFields, setParsedFields] = useState<string[]>([]);

  useEffect(() => {
    if (job) {
      setFormData({
        role: job.role || '',
        company: job.company || '',
        department: job.department || '',
        opening_date: job.opening_date || '',
        closing_date: job.closing_date || '',
        application_date: job.application_date || '',
        status: job.status || undefined,
        url: job.url || '',
        location: job.location || '',
        salary: job.salary || '',
        notes: job.notes || '',
        cv: job.cv || '',
        cover_letter: job.cover_letter || '',
        other_questions: job.other_questions || '',
      });
    }
  }, [job]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Clean up empty strings to undefined
      const cleanData: JobCreate = Object.fromEntries(
        Object.entries(formData).map(([key, value]) => [key, value === '' ? undefined : value])
      );

      if (job) {
        await jobsApi.updateJob(job.id, cleanData);
      } else {
        await jobsApi.createJob(cleanData);
      }
      onSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save job');
      console.error('Error saving job:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleParseUrl = async () => {
    if (!parseUrl.trim()) {
      setError('Please enter a URL to parse');
      return;
    }

    setParsing(true);
    setError(null);
    setMissingFields([]);
    setParsedFields([]);

    try {
      const result = await jobsApi.parseJobUrl(parseUrl, true);

      if (result.success && result.data) {
        // Track which fields were successfully parsed
        const parsed: string[] = [];

        // Update form data with parsed info
        const updatedData = { ...formData };
        Object.entries(result.data).forEach(([key, value]) => {
          if (value && key in updatedData) {
            (updatedData as any)[key] = value;
            parsed.push(key);
          }
        });

        setFormData(updatedData);
        setParsedFields(parsed);
        setMissingFields(result.missing_fields || []);

        if (result.missing_fields && result.missing_fields.length > 0) {
          setError(`Successfully parsed! Missing fields: ${result.missing_fields.join(', ')}. Please fill them in manually.`);
        }
      } else {
        setError(result.error || 'Failed to parse URL');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to parse URL');
    } finally {
      setParsing(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold mb-6">
        {job ? 'Edit Job Application' : 'New Job Application'}
      </h2>

      {error && (
        <div className={`border rounded-lg p-4 mb-4 ${
          missingFields.length > 0 && parsedFields.length > 0
            ? 'bg-yellow-50 border-yellow-200'
            : 'bg-red-50 border-red-200'
        }`}>
          <p className={missingFields.length > 0 && parsedFields.length > 0 ? 'text-yellow-800' : 'text-red-800'}>
            {error}
          </p>
        </div>
      )}

      {/* URL Parser Section */}
      {!job && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">
            🔗 Auto-fill from Job URL
          </h3>
          <p className="text-sm text-blue-700 mb-3">
            Paste a job posting URL and we'll automatically extract the details for you using AI.
          </p>
          <div className="flex gap-2">
            <input
              type="url"
              value={parseUrl}
              onChange={(e) => setParseUrl(e.target.value)}
              placeholder="https://example.com/careers/job-posting"
              className="flex-1 border border-blue-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={parsing}
            />
            <button
              type="button"
              onClick={handleParseUrl}
              disabled={parsing}
              className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400 transition-colors whitespace-nowrap"
            >
              {parsing ? 'Parsing...' : 'Parse URL'}
            </button>
          </div>
          {parsedFields.length > 0 && (
            <div className="mt-3 text-sm text-green-700">
              ✓ Successfully parsed: {parsedFields.join(', ')}
            </div>
          )}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Role */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Role / Position *
              {parsedFields.includes('role') && <span className="ml-2 text-xs text-green-600">✓ Auto-filled</span>}
              {missingFields.includes('role') && <span className="ml-2 text-xs text-red-600">⚠ Missing</span>}
            </label>
            <input
              type="text"
              name="role"
              value={formData.role}
              onChange={handleChange}
              required
              className={`w-full border rounded-md px-3 py-2 focus:outline-none focus:ring-2 ${
                parsedFields.includes('role')
                  ? 'border-green-300 bg-green-50 focus:ring-green-500'
                  : missingFields.includes('role')
                  ? 'border-red-300 bg-red-50 focus:ring-red-500'
                  : 'border-gray-300 focus:ring-blue-500'
              }`}
              placeholder="e.g., Senior Software Engineer"
            />
          </div>

          {/* Company */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Company *
              {parsedFields.includes('company') && <span className="ml-2 text-xs text-green-600">✓ Auto-filled</span>}
              {missingFields.includes('company') && <span className="ml-2 text-xs text-red-600">⚠ Missing</span>}
            </label>
            <input
              type="text"
              name="company"
              value={formData.company}
              onChange={handleChange}
              required
              className={`w-full border rounded-md px-3 py-2 focus:outline-none focus:ring-2 ${
                parsedFields.includes('company')
                  ? 'border-green-300 bg-green-50 focus:ring-green-500'
                  : missingFields.includes('company')
                  ? 'border-red-300 bg-red-50 focus:ring-red-500'
                  : 'border-gray-300 focus:ring-blue-500'
              }`}
              placeholder="e.g., TechCorp"
            />
          </div>

          {/* Department */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Department
            </label>
            <input
              type="text"
              name="department"
              value={formData.department}
              onChange={handleChange}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., Engineering"
            />
          </div>

          {/* Location */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Location
              {parsedFields.includes('location') && <span className="ml-2 text-xs text-green-600">✓ Auto-filled</span>}
              {missingFields.includes('location') && <span className="ml-2 text-xs text-red-600">⚠ Missing</span>}
            </label>
            <input
              type="text"
              name="location"
              value={formData.location}
              onChange={handleChange}
              className={`w-full border rounded-md px-3 py-2 focus:outline-none focus:ring-2 ${
                parsedFields.includes('location')
                  ? 'border-green-300 bg-green-50 focus:ring-green-500'
                  : missingFields.includes('location')
                  ? 'border-red-300 bg-red-50 focus:ring-red-500'
                  : 'border-gray-300 focus:ring-blue-500'
              }`}
              placeholder="e.g., San Francisco, CA or Remote"
            />
          </div>

          {/* Status */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Status
            </label>
            <select
              name="status"
              value={formData.status || ''}
              onChange={handleChange}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select status...</option>
              <option value="yet_to_apply">Yet to Apply</option>
              <option value="applied_waiting">Applied - Waiting</option>
              <option value="job_offered">Job Offered</option>
              <option value="job_accepted">Job Accepted</option>
              <option value="application_rejected">Application Rejected</option>
              <option value="job_rejected">Job Rejected</option>
            </select>
          </div>

          {/* Salary */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Salary
            </label>
            <input
              type="text"
              name="salary"
              value={formData.salary}
              onChange={handleChange}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., $120k - $150k"
            />
          </div>

          {/* Opening Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Opening Date
            </label>
            <input
              type="date"
              name="opening_date"
              value={formData.opening_date}
              onChange={handleChange}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Closing Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Closing Date
            </label>
            <input
              type="date"
              name="closing_date"
              value={formData.closing_date}
              onChange={handleChange}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Application Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Application Date
            </label>
            <input
              type="date"
              name="application_date"
              value={formData.application_date}
              onChange={handleChange}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* URL */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Job Posting URL
          </label>
          <input
            type="url"
            name="url"
            value={formData.url}
            onChange={handleChange}
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="https://..."
          />
        </div>

        {/* Notes */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Notes
          </label>
          <textarea
            name="notes"
            value={formData.notes}
            onChange={handleChange}
            rows={3}
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Add any notes about this application..."
          />
        </div>

        {/* CV */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            CV / Resume Info
          </label>
          <textarea
            name="cv"
            value={formData.cv}
            onChange={handleChange}
            rows={2}
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Which CV version did you use?"
          />
        </div>

        {/* Cover Letter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Cover Letter
          </label>
          <textarea
            name="cover_letter"
            value={formData.cover_letter}
            onChange={handleChange}
            rows={2}
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Cover letter details..."
          />
        </div>

        {/* Other Questions */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Other Questions / Responses
          </label>
          <textarea
            name="other_questions"
            value={formData.other_questions}
            onChange={handleChange}
            rows={2}
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Any other questions or screening responses..."
          />
        </div>

        {/* Buttons */}
        <div className="flex gap-3 pt-4">
          <button
            type="submit"
            disabled={loading}
            className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
          >
            {loading ? 'Saving...' : (job ? 'Update Job' : 'Create Job')}
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 bg-gray-200 text-gray-800 py-2 px-4 rounded-md hover:bg-gray-300 transition-colors"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
