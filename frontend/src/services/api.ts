import axios from 'axios';
import type { Job, JobCreate, JobUpdate, ApplicationStatus, ContactHistory, StalenessInfo, FollowUpMessage, FitEvaluation } from '../types/job';

export interface LinkedInJobCard {
  id: string;
  title: string;
  company: string | null;
  company_url: string | null;
  location: string | null;
  date: string | null;
  url: string;
  tracked?: boolean;
}

// Use environment variable for API URL, fallback to local development
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8192';

// Check if we're in local development (connecting to localhost)
const isLocalDevelopment = API_BASE_URL.includes('localhost') || API_BASE_URL.includes('127.0.0.1');

// HTTP Basic auth credentials (only used in production)
// TODO: Replace with proper login flow in future
const AUTH_USERNAME = 'admin';
const AUTH_PASSWORD = 'changeme';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Include credentials in cross-origin requests
});

// Add axios interceptor to include HTTP Basic auth in production requests
api.interceptors.request.use(
  (config) => {
    // Only add auth header in production (not local development)
    if (!isLocalDevelopment) {
      const credentials = btoa(`${AUTH_USERNAME}:${AUTH_PASSWORD}`);
      config.headers.Authorization = `Basic ${credentials}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export const jobsApi = {
  // Get all jobs with optional filters
  getJobs: async (params?: {
    skip?: number;
    limit?: number;
    status?: ApplicationStatus;
    company?: string;
  }): Promise<Job[]> => {
    const response = await api.get<Job[]>('/jobs', { params });
    return response.data;
  },

  // Get a single job by ID
  getJob: async (id: number): Promise<Job> => {
    const response = await api.get<Job>(`/jobs/${id}`);
    return response.data;
  },

  // Create a new job
  createJob: async (job: JobCreate): Promise<Job> => {
    const response = await api.post<Job>('/jobs', job);
    return response.data;
  },

  // Update an existing job
  updateJob: async (id: number, job: JobUpdate): Promise<Job> => {
    const response = await api.put<Job>(`/jobs/${id}`, job);
    return response.data;
  },

  // Delete a job
  deleteJob: async (id: number): Promise<void> => {
    await api.delete(`/jobs/${id}`);
  },

  // Test database connection
  testConnection: async (): Promise<{ status: string; message: string; jobs_count: number }> => {
    const response = await api.get('/db-test');
    return response.data;
  },

  // Parse job URL or HTML
  parseJobUrl: async (url: string, useLlm: boolean = true, html?: string): Promise<{
    success: boolean;
    data?: Record<string, any>;
    missing_fields?: string[];
    error?: string;
  }> => {
    const response = await api.post('/parse-job-url', {
      url,
      html,
      use_llm: useLlm,
    });
    return response.data;
  },

  // Search LinkedIn public job listings
  searchLinkedIn: async (params: {
    keywords?: string;
    location?: string;
    jobage?: number;
    remote?: string;
    page?: number;
  }): Promise<{ results: LinkedInJobCard[]; page: number }> => {
    const response = await api.get('/linkedin/search', { params });
    return response.data;
  },

  // Upload file
  uploadFile: async (file: File): Promise<{
    success: boolean;
    filename: string;
    path: string;
    url: string;
  }> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/upload-file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Delete file
  deleteFile: async (filename: string): Promise<void> => {
    await api.delete(`/delete-file/${filename}`);
  },
};


// ==================== SALARY CALCULATOR API ====================

export interface SalaryCalculationRequest {
  gross_yearly: number;
  pension_pct?: number;
  include_student_loan?: boolean;
  student_loan_plan?: string;
}

export interface TaxBreakdown {
  personal_allowance: number;
  taxable_income: number;
  basic_rate_amount: number;
  higher_rate_amount: number;
  additional_rate_amount: number;
}

export interface BudgetRecommendation {
  needs_50: number;
  wants_30: number;
  savings_20: number;
}

export interface SalaryCalculationResponse {
  gross_yearly: number;
  gross_monthly: number;
  net_yearly: number;
  net_monthly: number;
  income_tax: number;
  national_insurance: number;
  student_loan: number;
  pension: number;
  effective_tax_rate: number;
  tax_breakdown: TaxBreakdown;
  budget_recommendation: BudgetRecommendation;
}

export const salaryApi = {
  calculateSalary: async (request: SalaryCalculationRequest): Promise<SalaryCalculationResponse> => {
    const response = await api.post<SalaryCalculationResponse>('/calculate-salary', request);
    return response.data;
  },
};


// ==================== LEGO BLOCKS API ====================

export interface LegoBlockFilters {
  category?: string;
  skill?: string;
  role_type?: string;
  strength_level?: number;
}

export interface LegoBlockImportResponse {
  success: boolean;
  imported_count: number;
  skipped_count: number;
  message: string;
}

export const legoBlocksApi = {
  getLegoBlocks: async (filters?: LegoBlockFilters): Promise<any[]> => {
    const response = await api.get('/lego-blocks', { params: filters });
    return response.data;
  },

  importLegoBlocks: async (): Promise<LegoBlockImportResponse> => {
    const response = await api.post<LegoBlockImportResponse>('/lego-blocks/import');
    return response.data;
  },
};


// ==================== CV GENERATION API ====================

export interface BlockSuggestion {
  block_id: number;
  block: any;
  relevance_score: number;
}

export interface CVSuggestionsResponse {
  job_id: number;
  suggestions: BlockSuggestion[];
}

export interface CVGenerationRequest {
  max_blocks?: number;
}

export interface CVGenerationResponse {
  cv_id: number;
  selected_blocks: any[];
  latex: string;
  pdf_path: string | null;
  page_count: number | null;
  checks: Record<string, boolean> | null;
}

// Generation runs for minutes on the backend, so the POST endpoints return a
// task id immediately and we poll until the task finishes.
export interface GenerationTaskCreated {
  task_id: string;
  status: string;
}

export interface GenerationTaskStatus {
  task_id: string;
  kind: string;
  status: 'running' | 'done' | 'failed';
  error: string | null;
  result: unknown;
}

const GENERATION_POLL_INTERVAL_MS = 4000;
const GENERATION_POLL_TIMEOUT_MS = 30 * 60 * 1000;

async function pollGenerationTask<T>(taskId: string): Promise<T> {
  const deadline = Date.now() + GENERATION_POLL_TIMEOUT_MS;
  while (Date.now() < deadline) {
    await new Promise((resolve) => setTimeout(resolve, GENERATION_POLL_INTERVAL_MS));
    const { data } = await api.get<GenerationTaskStatus>(`/generation-tasks/${taskId}`);
    if (data.status === 'done') return data.result as T;
    if (data.status === 'failed') throw new Error(data.error ?? 'Generation failed.');
  }
  throw new Error('Generation timed out after 30 minutes.');
}

export const cvApi = {
  getCVSuggestions: async (jobId: number): Promise<CVSuggestionsResponse> => {
    const response = await api.get<CVSuggestionsResponse>(`/jobs/${jobId}/cv-suggestions`);
    return response.data;
  },

  getGeneratedCV: async (jobId: number): Promise<CVGenerationResponse | null> => {
    try {
      const response = await api.get<CVGenerationResponse>(`/jobs/${jobId}/generated-cv`);
      return response.data;
    } catch {
      return null;
    }
  },

  generateCV: async (jobId: number, request: CVGenerationRequest = {}): Promise<CVGenerationResponse> => {
    const response = await api.post<GenerationTaskCreated>(`/jobs/${jobId}/generate-cv`, request);
    return pollGenerationTask<CVGenerationResponse>(response.data.task_id);
  },
};


// ==================== COVER LETTER API ====================

export interface CoverLetterGenerationRequest {
  style?: string; // professional, enthusiastic, technical
}

export interface CoverLetterGenerationResponse {
  letter_id: number;
  content: string;
  pdf_path: string | null;
  page_count: number | null;
  checks: Record<string, boolean> | null;
}

export interface CoverLetterUpdateRequest {
  instructions: string;
}

export const coverLetterApi = {
  getGeneratedCoverLetter: async (jobId: number): Promise<CoverLetterGenerationResponse | null> => {
    try {
      const response = await api.get<CoverLetterGenerationResponse>(`/jobs/${jobId}/generated-cover-letter`);
      return response.data;
    } catch {
      return null;
    }
  },

  generateCoverLetter: async (
    jobId: number,
    request: CoverLetterGenerationRequest = {}
  ): Promise<CoverLetterGenerationResponse> => {
    const response = await api.post<GenerationTaskCreated>(
      `/jobs/${jobId}/generate-cover-letter`,
      request
    );
    return pollGenerationTask<CoverLetterGenerationResponse>(response.data.task_id);
  },

  updateCoverLetter: async (
    letterId: number,
    request: CoverLetterUpdateRequest
  ): Promise<CoverLetterGenerationResponse> => {
    const response = await api.put<CoverLetterGenerationResponse>(
      `/generated-cover-letters/${letterId}`,
      request
    );
    return response.data;
  },
};


// ==================== CONTACT TRACKING API ====================

export interface ContactHistoryCreate {
  contact_method: 'email' | 'linkedin' | 'phone' | 'other';
  message_content?: string;
  notes?: string;
}

export const fitApi = {
  // Run a fit evaluation for a job (LLM-backed)
  evaluateFit: async (jobId: number): Promise<FitEvaluation> => {
    const response = await api.post<FitEvaluation>(`/jobs/${jobId}/evaluate-fit`);
    return response.data;
  },

  // Get the most recent fit evaluation (404 if none yet)
  getFit: async (jobId: number): Promise<FitEvaluation> => {
    const response = await api.get<FitEvaluation>(`/jobs/${jobId}/fit`);
    return response.data;
  },
};

export const profileApi = {
  getProfile: async (): Promise<string> => {
    const response = await api.get<{ content: string }>('/profile');
    return response.data.content;
  },

  updateProfile: async (content: string): Promise<void> => {
    await api.put('/profile', { content });
  },
};

export interface GapHeatmapEntry {
  priority: string;
  area: string;
  type: string;
  source: string;
}

export interface GapAnalysisResponse {
  jobs_analyzed: number;
  hard_gaps: { skill: string; score: number; job_count: number }[];
  heatmap: GapHeatmapEntry[];
}

export const gapApi = {
  getGapAnalysis: async (): Promise<GapAnalysisResponse> => {
    const response = await api.get<GapAnalysisResponse>('/gap-analysis');
    return response.data;
  },
};

export const contactApi = {
  getHistory: async (jobId: number): Promise<ContactHistory[]> => {
    const response = await api.get<ContactHistory[]>(`/jobs/${jobId}/contact-history`);
    return response.data;
  },

  recordContact: async (jobId: number, data: ContactHistoryCreate): Promise<ContactHistory> => {
    const response = await api.post<ContactHistory>(`/jobs/${jobId}/contact-history`, data);
    return response.data;
  },

  generateFollowUp: async (jobId: number, type: 'email' | 'linkedin'): Promise<FollowUpMessage> => {
    const response = await api.get<FollowUpMessage>(`/jobs/${jobId}/generate-followup`, {
      params: { message_type: type }
    });
    return response.data;
  },

  getStaleness: async (jobId: number): Promise<StalenessInfo> => {
    const response = await api.get<StalenessInfo>(`/jobs/${jobId}/staleness`);
    return response.data;
  },
};

export default api;
