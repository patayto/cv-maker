export enum ApplicationStatus {
  YET_TO_APPLY = "yet_to_apply",
  APPLIED_WAITING = "applied_waiting",
  JOB_OFFERED = "job_offered",
  JOB_ACCEPTED = "job_accepted",
  APPLICATION_REJECTED = "application_rejected",
  JOB_REJECTED = "job_rejected",
}

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
}

export interface JobUpdate extends JobCreate {}

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
