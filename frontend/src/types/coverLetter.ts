export interface GeneratedCoverLetter {
  id: number;
  jobId: number;
  content: string;
  templateUsed: string;
  createdAt: string;
}

export type CoverLetterStyle = 'professional' | 'enthusiastic' | 'concise' | 'storytelling';
