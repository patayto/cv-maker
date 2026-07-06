/**
 * Utility functions for field validation and formatting
 */

/**
 * Format salary for display with currency symbol and thousands separator
 */
export function formatSalary(
  min: number | null | undefined,
  max: number | null | undefined,
  currency: string | null | undefined
): string {
  if (!min || !max || !currency) {
    return '';
  }

  const currencySymbol = {
    GBP: '£',
    USD: '$',
    EUR: '€',
  }[currency] || currency;

  const formatter = new Intl.NumberFormat('en-GB', {
    maximumFractionDigits: 0,
  });

  return `${currencySymbol}${formatter.format(min)} - ${currencySymbol}${formatter.format(max)}`;
}

/**
 * Format a single salary amount with currency
 */
export function formatSingleSalary(
  amount: number | null | undefined,
  currency: string | null | undefined
): string {
  if (!amount || !currency) {
    return '';
  }

  const currencySymbol = {
    GBP: '£',
    USD: '$',
    EUR: '€',
  }[currency] || currency;

  const formatter = new Intl.NumberFormat('en-GB', {
    maximumFractionDigits: 0,
  });

  return `${currencySymbol}${formatter.format(amount)}`;
}

/**
 * Parse salary string to extract min, max, and currency
 * Examples: "$80k - $120k", "£50,000 - £80,000", "100000-150000 USD"
 */
export function parseSalaryString(str: string): {
  min: number | null;
  max: number | null;
  currency: string | null;
} {
  if (!str) {
    return { min: null, max: null, currency: null };
  }

  // Detect currency
  let currency: string | null = null;
  if (str.includes('£') || str.toUpperCase().includes('GBP')) {
    currency = 'GBP';
  } else if (str.includes('$') || str.toUpperCase().includes('USD')) {
    currency = 'USD';
  } else if (str.includes('€') || str.toUpperCase().includes('EUR')) {
    currency = 'EUR';
  }

  // Extract numbers (remove commas, currency symbols, etc.)
  const numbers = str.match(/\d+(?:,\d{3})*(?:\.\d+)?/g);
  if (!numbers || numbers.length === 0) {
    return { min: null, max: null, currency };
  }

  // Parse numbers and handle 'k' notation
  const parsedNumbers = numbers.map(num => {
    const value = parseFloat(num.replace(/,/g, ''));
    // If original string contains 'k' and number is small, multiply by 1000
    if (str.toLowerCase().includes('k') && value < 1000) {
      return value * 1000;
    }
    return value;
  });

  if (parsedNumbers.length >= 2) {
    return {
      min: Math.min(...parsedNumbers),
      max: Math.max(...parsedNumbers),
      currency,
    };
  } else if (parsedNumbers.length === 1) {
    return {
      min: parsedNumbers[0],
      max: parsedNumbers[0],
      currency,
    };
  }

  return { min: null, max: null, currency };
}

/**
 * Validate email address
 */
export function isValidEmail(email: string): boolean {
  if (!email) return false;
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Validate LinkedIn URL
 */
export function isValidLinkedInUrl(url: string): boolean {
  if (!url) return false;
  return url.includes('linkedin.com/in/') || url.includes('linkedin.com/company/');
}

/**
 * Validate LinkedIn job posting URL
 */
export function isLinkedInJobUrl(url: string): boolean {
  if (!url) return false;
  return url.includes('linkedin.com/jobs');
}

/**
 * Clean and validate URL
 */
export function cleanUrl(url: string): string {
  if (!url) return '';
  const trimmed = url.trim();
  if (!trimmed.startsWith('http://') && !trimmed.startsWith('https://')) {
    return `https://${trimmed}`;
  }
  return trimmed;
}

/**
 * Format date for display
 */
export function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return '';
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  } catch {
    return dateString;
  }
}

/**
 * Calculate days between two dates
 */
export function daysBetween(date1: string | Date, date2: string | Date): number {
  const d1 = new Date(date1);
  const d2 = new Date(date2);
  const diffTime = Math.abs(d2.getTime() - d1.getTime());
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}

/**
 * Capitalize first letter of each word
 */
export function capitalizeWords(str: string): string {
  if (!str) return '';
  return str
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

/**
 * Truncate text to specified length
 */
export function truncate(text: string, maxLength: number): string {
  if (!text || text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}

/**
 * Format experience level for display
 */
export function formatExperienceLevel(level: string | null | undefined): string {
  if (!level) return '';
  const mapping: Record<string, string> = {
    junior: 'Junior',
    mid: 'Mid-Level',
    senior: 'Senior',
    staff: 'Staff',
    principal: 'Principal',
  };
  return mapping[level.toLowerCase()] || capitalizeWords(level);
}

/**
 * Get color variant for experience level badge
 */
export function getExperienceLevelColor(level: string | null | undefined): 'default' | 'success' | 'warning' | 'info' | 'purple' {
  if (!level) return 'default';
  const levelLower = level.toLowerCase();
  if (levelLower === 'junior') return 'info';
  if (levelLower === 'mid') return 'success';
  if (levelLower === 'senior') return 'warning';
  if (levelLower === 'staff' || levelLower === 'principal') return 'purple';
  return 'default';
}

/**
 * Parse array from comma-separated string
 */
export function parseCommaSeparated(str: string): string[] {
  if (!str) return [];
  return str
    .split(',')
    .map(item => item.trim())
    .filter(item => item.length > 0);
}

/**
 * Join array to comma-separated string
 */
export function joinWithCommas(arr: string[] | null | undefined): string {
  if (!arr || arr.length === 0) return '';
  return arr.join(', ');
}
