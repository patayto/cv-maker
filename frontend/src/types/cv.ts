import type { LegoBlock } from './legoBlock';

export interface CVGenerationOptions {
  maxBlocks: number;
  includeCategories: string[];
  excludeCategories: string[];
  prioritizeSkills: string[];
}

export interface GeneratedCV {
  id: number;
  jobId: number;
  selectedBlocks: number[];
  customizations: Record<string, string>;
  pdfPath?: string;
  createdAt: string;
}

export interface BlockSuggestion {
  block: LegoBlock;
  relevanceScore: number;
  matchedSkills: string[];
  reason: string;
}
