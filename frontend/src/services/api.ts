import axios from 'axios';
import type { Job, JobCreate, JobUpdate, ApplicationStatus, ContactHistory, StalenessInfo, FollowUpMessage } from '../types/job';

// Use environment variable for API URL, fallback to local development
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

// HTTP Basic auth credentials (hardcoded for initial deployment)
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

// Add axios interceptor to include HTTP Basic auth in all requests
api.interceptors.request.use(
  (config) => {
    // Add Authorization header with Basic auth
    const credentials = btoa(`${AUTH_USERNAME}:${AUTH_PASSWORD}`);
    config.headers.Authorization = `Basic ${credentials}`;
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

  // Parse job URL
  parseJobUrl: async (url: string, useLlm: boolean = true): Promise<{
    success: boolean;
    data?: Record<string, any>;
    missing_fields?: string[];
    error?: string;
  }> => {
    const response = await api.post('/parse-job-url', {
      url,
      use_llm: useLlm,
    });
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
}

export const cvApi = {
  getCVSuggestions: async (jobId: number): Promise<CVSuggestionsResponse> => {
    const response = await api.get<CVSuggestionsResponse>(`/jobs/${jobId}/cv-suggestions`);
    return response.data;
  },

  generateCV: async (jobId: number, request: CVGenerationRequest = {}): Promise<CVGenerationResponse> => {
    const response = await api.post<CVGenerationResponse>(`/jobs/${jobId}/generate-cv`, request);
    return response.data;
  },
};


// ==================== COVER LETTER API ====================

export interface CoverLetterGenerationRequest {
  style?: string; // professional, enthusiastic, technical
}

export interface CoverLetterGenerationResponse {
  letter_id: number;
  content: string;
}

export interface CoverLetterUpdateRequest {
  instructions: string;
}

export const coverLetterApi = {
  generateCoverLetter: async (
    jobId: number,
    request: CoverLetterGenerationRequest = {}
  ): Promise<CoverLetterGenerationResponse> => {
    const response = await api.post<CoverLetterGenerationResponse>(
      `/jobs/${jobId}/generate-cover-letter`,
      request
    );
    return response.data;
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
