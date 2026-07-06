export const ApplicationStatus = {
  YET_TO_APPLY: "yet_to_apply",
  APPLIED_WAITING: "applied_waiting",
  JOB_OFFERED: "job_offered",
  JOB_ACCEPTED: "job_accepted",
  APPLICATION_REJECTED: "application_rejected",
  JOB_REJECTED: "job_rejected",
} as const;

export type ApplicationStatus = typeof ApplicationStatus[keyof typeof ApplicationStatus];

export interface Job {
  id: number;
  role: string | null;
  company: string | null;
  department: string | null;
  opening_date: string | null;
  closing_date: string | null;
  application_date: string | null;
  last_update: string | null;
  status: ApplicationStatus | null;
  url: string | null;
  cv: string | null;
  cover_letter: string | null;
  other_questions: string | null;
  location: string | null;
  salary: string | null;
  notes: string | null;
  recruiter_name: string | null;
  recruiter_email: string | null;
  recruiter_linkedin: string | null;

  // Extended fields - parsed from job postings
  parsed_skills: string[] | null;
  parsed_requirements: string[] | null;
  parsed_responsibilities: string[] | null;

  // Salary structure
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string | null;
  net_salary_yearly: number | null;
  net_salary_monthly: number | null;

  // Metadata
  experience_level: string | null;
  workplace_type: string | null;
  employment_type: string | null;

  // Generated content references
  generated_cv_id: number | null;
  generated_cover_letter_id: number | null;

  // From the most recent fit evaluation, if any
  fit_score?: number | null;
  fit_verdict?: string | null;
}

export interface FitEvaluation {
  id: number;
  job_id: number;
  technical_skills: number;
  experience_match: number;
  behavioral_fit: number;
  career_alignment: number;
  location_pass: boolean;
  overall_score: number;
  verdict: string;
  key_strengths: string[] | null;
  gaps: string[] | null;
  created_at: string;
}

export interface JobCreate {
  role?: string;
  company?: string;
  department?: string;
  opening_date?: string;
  closing_date?: string;
  application_date?: string;
  last_update?: string;
  status?: ApplicationStatus;
  url?: string;
  cv?: string;
  cover_letter?: string;
  other_questions?: string;
  location?: string;
  salary?: string;
  notes?: string;

  // Extended fields - parsed from job postings
  parsed_skills?: string[];
  parsed_requirements?: string[];
  parsed_responsibilities?: string[];

  // Salary structure
  salary_min?: number;
  salary_max?: number;
  salary_currency?: string;
  net_salary_yearly?: number;
  net_salary_monthly?: number;

  // Metadata
  experience_level?: string;
  workplace_type?: string;
  employment_type?: string;

  // Generated content references
  generated_cv_id?: number;
  generated_cover_letter_id?: number;

  // Recruiter information
  recruiter_name?: string;
  recruiter_email?: string;
  recruiter_linkedin?: string;
}

export type JobUpdate = JobCreate;

export interface ContactHistory {
  id: number;
  job_id: number;
  contacted_at: string;
  contact_method: 'email' | 'linkedin' | 'phone' | 'other';
  message_content: string | null;
  notes: string | null;
  created_at: string;
}

export interface StalenessInfo {
  days_since_update: number | null;
  staleness_level: 'green' | 'yellow' | 'orange' | 'red' | 'gray';
  contact_count: number;
  last_contact_date: string | null;
}

export interface FollowUpMessage {
  message: string;
  subject: string | null;
  recipient_name: string;
  recipient_email: string | null;
  recipient_linkedin: string | null;
}
