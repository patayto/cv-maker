import React from 'react';
import { pdf } from '@react-pdf/renderer';
import { CVTemplate, type CVTemplateProps } from '../components/pdf/CVTemplate';
import { CoverLetterTemplate, type CoverLetterTemplateProps } from '../components/pdf/CoverLetterTemplate';

/**
 * Generate a CV PDF blob from the given data
 */
export async function generateCVPDF(data: CVTemplateProps): Promise<Blob> {
  // Cast needed because pdf() types expect ReactElement<DocumentProps> but our template wraps <Document>
  const blob = await pdf(React.createElement(CVTemplate, data) as React.ReactElement<any>).toBlob();
  return blob;
}

/**
 * Generate and download a CV PDF
 */
export async function downloadCVPDF(
  data: CVTemplateProps,
  filename?: string
): Promise<void> {
  const blob = await generateCVPDF(data);
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');

  // Generate filename from job details
  const defaultFilename = [
    'CV',
    data.job.company?.replace(/\s+/g, '_'),
    data.job.role?.replace(/\s+/g, '_'),
  ]
    .filter(Boolean)
    .join('_') + '.pdf';

  link.href = url;
  link.download = filename || defaultFilename;
  link.click();

  // Cleanup
  URL.revokeObjectURL(url);
}

/**
 * Generate a cover letter PDF blob from the given data
 */
export async function generateCoverLetterPDF(data: CoverLetterTemplateProps): Promise<Blob> {
  const blob = await pdf(React.createElement(CoverLetterTemplate, data) as React.ReactElement<any>).toBlob();
  return blob;
}

/**
 * Generate and download a cover letter PDF
 */
export async function downloadCoverLetterPDF(
  data: CoverLetterTemplateProps,
  filename?: string
): Promise<void> {
  const blob = await generateCoverLetterPDF(data);
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');

  // Generate filename from job details
  const defaultFilename = [
    'CoverLetter',
    data.job.company?.replace(/\s+/g, '_'),
    data.job.role?.replace(/\s+/g, '_'),
  ]
    .filter(Boolean)
    .join('_') + '.pdf';

  link.href = url;
  link.download = filename || defaultFilename;
  link.click();

  // Cleanup
  URL.revokeObjectURL(url);
}
