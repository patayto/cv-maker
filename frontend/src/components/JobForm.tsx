import { useState, useEffect } from 'react';
import { jobsApi } from '../services/api';
import type { Job, JobCreate } from '../types/job';
import { Tabs, TabPanel } from './Tabs';
import { Badge } from './Badge';
import { TagInput } from './TagInput';
import { EditableList } from './EditableList';
import { SalaryRangeInput } from './SalaryRangeInput';

interface JobFormProps {
  job: Job | null;
  onSuccess: () => void;
  onCancel: () => void;
  /** When set (e.g. importing from search), the URL is parsed automatically on mount */
  initialParseUrl?: string;
  /** Called when the user opts to open an already-tracked duplicate */
  onOpenExisting?: (job: Job) => void;
}

export default function JobForm({ job, onSuccess, onCancel, initialParseUrl, onOpenExisting }: JobFormProps) {
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

    // Extended fields - parsed from job postings
    parsed_skills: undefined,
    parsed_requirements: undefined,
    parsed_responsibilities: undefined,

    // Salary structure
    salary_min: undefined,
    salary_max: undefined,
    salary_currency: undefined,
    net_salary_yearly: undefined,
    net_salary_monthly: undefined,

    // Metadata
    experience_level: undefined,
    workplace_type: undefined,
    employment_type: undefined,

    // Generated content references
    generated_cv_id: undefined,
    generated_cover_letter_id: undefined,

    // Recruiter information
    recruiter_name: '',
    recruiter_email: '',
    recruiter_linkedin: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [parsing, setParsing] = useState(false);
  const [parseUrl, setParseUrl] = useState('');
  const [parseHtml, setParseHtml] = useState('');
  const [parseMode, setParseMode] = useState<'url' | 'html'>('url');
  const [missingFields, setMissingFields] = useState<string[]>([]);
  const [parsedFields, setParsedFields] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState('basic');
  const [rawParserData, setRawParserData] = useState<Record<string, unknown> | null>(null);
  const [duplicateJobId, setDuplicateJobId] = useState<number | null>(null);

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

        // Extended fields
        parsed_skills: job.parsed_skills || undefined,
        parsed_requirements: job.parsed_requirements || undefined,
        parsed_responsibilities: job.parsed_responsibilities || undefined,

        // Salary structure
        salary_min: job.salary_min || undefined,
        salary_max: job.salary_max || undefined,
        salary_currency: job.salary_currency || undefined,
        net_salary_yearly: job.net_salary_yearly || undefined,
        net_salary_monthly: job.net_salary_monthly || undefined,

        // Metadata
        experience_level: job.experience_level || undefined,
        workplace_type: job.workplace_type || undefined,
        employment_type: job.employment_type || undefined,

        // Generated content references
        generated_cv_id: job.generated_cv_id || undefined,
        generated_cover_letter_id: job.generated_cover_letter_id || undefined,

        // Recruiter information
        recruiter_name: job.recruiter_name || '',
        recruiter_email: job.recruiter_email || '',
        recruiter_linkedin: job.recruiter_linkedin || '',
      });
    }
  }, [job]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setDuplicateJobId(null);

    try {
      // On update, cleared fields must be sent as null so the backend clears them;
      // undefined keys are dropped from the JSON payload and the old value survives.
      // On create, drop empty fields entirely.
      const emptyValue = job ? null : undefined;
      const cleanData: JobCreate = Object.fromEntries(
        Object.entries(formData).map(([key, value]) => [key, value === '' ? emptyValue : value])
      );

      if (job) {
        await jobsApi.updateJob(job.id, cleanData);
      } else {
        await jobsApi.createJob(cleanData);
      }
      onSuccess();
    } catch (err: unknown) {
      const error = err as {
        response?: {
          status?: number;
          data?: { detail?: string | { message?: string; existing_job_id?: number } };
        };
      };
      const detail = error.response?.data?.detail;
      if (error.response?.status === 409 && typeof detail === 'object' && detail) {
        setError(detail.message || 'This job is already tracked.');
        setDuplicateJobId(detail.existing_job_id ?? null);
      } else {
        setError(typeof detail === 'string' ? detail : 'Failed to save job');
      }
      console.error('Error saving job:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenExisting = async () => {
    if (!duplicateJobId || !onOpenExisting) return;
    try {
      const existing = await jobsApi.getJob(duplicateJobId);
      onOpenExisting(existing);
    } catch (err) {
      setError('Failed to load the existing job.');
      console.error('Error loading existing job:', err);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  // Handlers for array fields
  const handleSkillsChange = (skills: string[]) => {
    setFormData(prev => ({ ...prev, parsed_skills: skills }));
  };

  const handleRequirementsChange = (requirements: string[]) => {
    setFormData(prev => ({ ...prev, parsed_requirements: requirements }));
  };

  const handleResponsibilitiesChange = (responsibilities: string[]) => {
    setFormData(prev => ({ ...prev, parsed_responsibilities: responsibilities }));
  };

  // Handler for salary fields
  const handleSalaryChange = (data: { min?: number; max?: number; currency?: string }) => {
    setFormData(prev => ({
      ...prev,
      salary_min: data.min,
      salary_max: data.max,
      salary_currency: data.currency,
    }));
  };

  // Auto-parse when arriving from the search view with a job URL
  useEffect(() => {
    if (initialParseUrl && !job) {
      setParseUrl(initialParseUrl);
      handleParseUrl(initialParseUrl);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialParseUrl]);

  const handleParseUrl = async (overrideUrl?: string) => {
    const urlToParse = overrideUrl ?? parseUrl;
    if (parseMode === 'url' && !urlToParse.trim()) {
      setError('Please enter a URL to parse');
      return;
    }
    if (parseMode === 'html' && !parseHtml.trim()) {
      setError('Please paste HTML content to parse');
      return;
    }

    setParsing(true);
    setError(null);
    setMissingFields([]);
    setParsedFields([]);

    try {
      const result = await jobsApi.parseJobUrl(
        parseMode === 'url' ? urlToParse : '',
        true,
        parseMode === 'html' ? parseHtml : undefined
      );

      if (result.success && result.data) {
        // Store raw parser data for debug tab
        setRawParserData(result.data);

        // Track which fields were successfully parsed
        const parsed: string[] = [];

        // Update form data with parsed info
        // CRITICAL FIX: Accept ALL fields from parser, not just those in formData
        const updatedData = { ...formData } as Record<string, unknown>;
        Object.entries(result.data).forEach(([key, value]) => {
          if (value !== null && value !== undefined) {
            updatedData[key] = value;
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
    } catch (err: unknown) {
      const error = err as { response?: { data?: { error?: string } } };
      setError(error.response?.data?.error || 'Failed to parse URL');
    } finally {
      setParsing(false);
    }
  };

  // Define tabs
  const tabs = [
    { id: 'basic', label: 'Basic Info', icon: '📝' },
    {
      id: 'skills',
      label: 'Skills & Requirements',
      icon: '⚡',
      badge: formData.parsed_skills?.length || undefined,
    },
    { id: 'salary', label: 'Salary Details', icon: '💰' },
    { id: 'recruiter', label: 'Recruiter Contact', icon: '👤' },
    {
      id: 'debug',
      label: 'Debug Info',
      icon: '🐛',
      badge: parsedFields.length > 0 ? parsedFields.length : undefined,
    },
  ];

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
          {duplicateJobId !== null && onOpenExisting && (
            <button
              type="button"
              onClick={handleOpenExisting}
              className="mt-2 px-4 py-1.5 bg-red-600 text-white text-sm rounded-md hover:bg-red-700 transition-colors"
            >
              Open existing job →
            </button>
          )}
        </div>
      )}

      {/* URL Parser Section */}
      {!job && (
        <>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <h3 className="text-lg font-semibold text-blue-900 mb-3">
              {parseMode === 'url' ? '🔗' : '📋'} Auto-fill from Job {parseMode === 'url' ? 'URL' : 'HTML'}
            </h3>

            {/* Mode Toggle */}
            <div className="flex gap-4 mb-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="parseMode"
                  value="url"
                  checked={parseMode === 'url'}
                  onChange={(e) => setParseMode(e.target.value as 'url' | 'html')}
                  className="w-4 h-4 text-blue-600"
                />
                <span className="text-sm font-medium text-blue-900">🔗 URL</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="parseMode"
                  value="html"
                  checked={parseMode === 'html'}
                  onChange={(e) => setParseMode(e.target.value as 'url' | 'html')}
                  className="w-4 h-4 text-blue-600"
                />
                <span className="text-sm font-medium text-blue-900">📋 HTML</span>
              </label>
            </div>

            {parseMode === 'url' ? (
              <>
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
                    onClick={() => handleParseUrl()}
                    disabled={parsing}
                    className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400 transition-colors whitespace-nowrap"
                  >
                    {parsing ? 'Parsing...' : 'Parse URL'}
                  </button>
                </div>
              </>
            ) : (
              <>
                <p className="text-sm text-blue-700 mb-3">
                  Paste the raw HTML source of a job posting (right-click → Inspect → copy HTML) and we'll extract the details using AI.
                </p>
                <textarea
                  value={parseHtml}
                  onChange={(e) => setParseHtml(e.target.value)}
                  placeholder="<html>...</html>"
                  className="w-full border border-blue-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-xs h-32"
                  disabled={parsing}
                />
                <button
                  type="button"
                  onClick={() => handleParseUrl()}
                  disabled={parsing}
                  className="mt-2 bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
                >
                  {parsing ? 'Parsing...' : 'Parse HTML'}
                </button>
              </>
            )}

            {parsedFields.length > 0 && (
              <div className="mt-3 text-sm text-green-700">
                ✓ Successfully parsed: {parsedFields.join(', ')}
              </div>
            )}
          </div>
        </>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Tab Navigation */}
        <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

        {/* Tab 1: Basic Info */}
        <TabPanel id="basic" activeTab={activeTab}>
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
        </TabPanel>

        {/* Tab 2: Skills & Requirements */}
        <TabPanel id="skills" activeTab={activeTab}>
          <div className="space-y-6">
            {/* Metadata Badges */}
            <div className="flex flex-wrap gap-2">
              {formData.experience_level && (
                <Badge variant="info" icon="🎯">
                  {formData.experience_level}
                </Badge>
              )}
              {formData.workplace_type && (
                <Badge variant="success" icon="🏢">
                  {formData.workplace_type}
                </Badge>
              )}
              {formData.employment_type && (
                <Badge variant="purple" icon="⏰">
                  {formData.employment_type}
                </Badge>
              )}
            </div>

            {/* Skills */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Required Skills</h3>
              <TagInput
                value={formData.parsed_skills || []}
                onChange={handleSkillsChange}
                placeholder="Add a skill..."
              />
              {parsedFields.includes('parsed_skills') && (
                <p className="mt-2 text-sm text-green-600">
                  ✓ Auto-extracted from job posting
                </p>
              )}
            </div>

            {/* Requirements */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Requirements & Qualifications</h3>
              <EditableList
                items={formData.parsed_requirements || []}
                onChange={handleRequirementsChange}
                placeholder="Add a requirement..."
              />
              {parsedFields.includes('parsed_requirements') && (
                <p className="mt-2 text-sm text-green-600">
                  ✓ Auto-extracted from job posting
                </p>
              )}
            </div>

            {/* Responsibilities */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Key Responsibilities</h3>
              <EditableList
                items={formData.parsed_responsibilities || []}
                onChange={handleResponsibilitiesChange}
                placeholder="Add a responsibility..."
              />
              {parsedFields.includes('parsed_responsibilities') && (
                <p className="mt-2 text-sm text-green-600">
                  ✓ Auto-extracted from job posting
                </p>
              )}
            </div>
          </div>
        </TabPanel>

        {/* Tab 3: Salary Details */}
        <TabPanel id="salary" activeTab={activeTab}>
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Salary Information</h3>
              <SalaryRangeInput
                min={formData.salary_min}
                max={formData.salary_max}
                currency={formData.salary_currency}
                onChange={handleSalaryChange}
              />
              {parsedFields.includes('salary_min') && (
                <p className="mt-3 text-sm text-green-600">
                  ✓ Auto-extracted from job posting
                </p>
              )}
            </div>

            {/* Net Salary Display (read-only) */}
            {formData.net_salary_yearly && (
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-2">Take-Home Pay (After Tax)</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">Yearly Net</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {formData.salary_currency === 'GBP' && '£'}
                      {formData.salary_currency === 'USD' && '$'}
                      {formData.salary_currency === 'EUR' && '€'}
                      {formData.net_salary_yearly?.toLocaleString('en-GB')}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Monthly Net</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {formData.salary_currency === 'GBP' && '£'}
                      {formData.salary_currency === 'USD' && '$'}
                      {formData.salary_currency === 'EUR' && '€'}
                      {formData.net_salary_monthly?.toLocaleString('en-GB')}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </TabPanel>

        {/* Tab 4: Recruiter Contact */}
        <TabPanel id="recruiter" activeTab={activeTab}>
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Recruiter Information</h3>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Recruiter Name
                {parsedFields.includes('recruiter_name') && (
                  <span className="ml-2 text-xs text-green-600">✓ Auto-filled</span>
                )}
              </label>
              <input
                type="text"
                name="recruiter_name"
                value={formData.recruiter_name}
                onChange={handleChange}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., John Smith"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                type="email"
                name="recruiter_email"
                value={formData.recruiter_email}
                onChange={handleChange}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="recruiter@company.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                LinkedIn Profile
                {parsedFields.includes('recruiter_linkedin') && (
                  <span className="ml-2 text-xs text-green-600">✓ Auto-filled</span>
                )}
              </label>
              <input
                type="url"
                name="recruiter_linkedin"
                value={formData.recruiter_linkedin}
                onChange={handleChange}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="https://linkedin.com/in/..."
              />
              {formData.recruiter_linkedin && (
                <a
                  href={formData.recruiter_linkedin}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-2 inline-block text-sm text-blue-600 hover:text-blue-800 hover:underline"
                >
                  View LinkedIn Profile →
                </a>
              )}
            </div>
          </div>
        </TabPanel>

        {/* Tab 5: Debug Info */}
        <TabPanel id="debug" activeTab={activeTab}>
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Parser Debug Information</h3>

            {/* Parse Status */}
            {parsedFields.length > 0 ? (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <p className="text-green-800 font-medium">
                  ✓ Successfully parsed {parsedFields.length} fields
                </p>
                <p className="text-sm text-green-700 mt-1">
                  {parsedFields.join(', ')}
                </p>
              </div>
            ) : (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <p className="text-gray-600">
                  No parsing data available. Use the "Parse URL" feature to extract job details.
                </p>
              </div>
            )}

            {/* Missing Fields */}
            {missingFields.length > 0 && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-yellow-800 font-medium">
                  ⚠ Missing {missingFields.length} fields
                </p>
                <p className="text-sm text-yellow-700 mt-1">
                  {missingFields.join(', ')}
                </p>
              </div>
            )}

            {/* Raw Parser Output */}
            {rawParserData && (
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Raw Parser Output</h4>
                <details className="bg-gray-900 text-green-400 rounded-lg overflow-hidden">
                  <summary className="px-4 py-2 cursor-pointer hover:bg-gray-800 font-mono text-sm">
                    Click to expand JSON ({Object.keys(rawParserData).length} fields)
                  </summary>
                  <pre className="p-4 overflow-auto max-h-96 text-xs">
                    {JSON.stringify(rawParserData, null, 2)}
                  </pre>
                </details>
              </div>
            )}

            {/* Re-parse Button */}
            {parseUrl && (
              <button
                type="button"
                onClick={() => handleParseUrl()}
                disabled={parsing}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
              >
                {parsing ? 'Re-parsing...' : 'Re-parse URL'}
              </button>
            )}
          </div>
        </TabPanel>

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
