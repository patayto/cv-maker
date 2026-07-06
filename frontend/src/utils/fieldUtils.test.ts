/**
 * Tests for fieldUtils.ts utility functions
 */

import { describe, it, expect } from 'vitest';
import {
  formatSalary,
  formatSingleSalary,
  parseSalaryString,
  isValidEmail,
  isValidLinkedInUrl,
  isLinkedInJobUrl,
  cleanUrl,
  formatDate,
  daysBetween,
  capitalizeWords,
  truncate,
  formatExperienceLevel,
  getExperienceLevelColor,
  parseCommaSeparated,
  joinWithCommas,
} from './fieldUtils';

// ==================== SALARY FORMATTING TESTS ====================

describe('formatSalary', () => {
  it('should format salary range with GBP', () => {
    const result = formatSalary(50000, 70000, 'GBP');
    expect(result).toBe('£50,000 - £70,000');
  });

  it('should format salary range with USD', () => {
    const result = formatSalary(80000, 120000, 'USD');
    expect(result).toBe('$80,000 - $120,000');
  });

  it('should format salary range with EUR', () => {
    const result = formatSalary(60000, 90000, 'EUR');
    expect(result).toBe('€60,000 - €90,000');
  });

  it('should return empty string when min is null', () => {
    const result = formatSalary(null, 70000, 'GBP');
    expect(result).toBe('');
  });

  it('should return empty string when max is null', () => {
    const result = formatSalary(50000, null, 'GBP');
    expect(result).toBe('');
  });

  it('should return empty string when currency is null', () => {
    const result = formatSalary(50000, 70000, null);
    expect(result).toBe('');
  });

  it('should use currency code as symbol for unknown currencies', () => {
    const result = formatSalary(50000, 70000, 'JPY');
    expect(result).toBe('JPY50,000 - JPY70,000');
  });

  it('should format large numbers with thousands separators', () => {
    const result = formatSalary(100000, 150000, 'USD');
    expect(result).toBe('$100,000 - $150,000');
  });
});

describe('formatSingleSalary', () => {
  it('should format single salary amount with GBP', () => {
    const result = formatSingleSalary(65000, 'GBP');
    expect(result).toBe('£65,000');
  });

  it('should format single salary amount with USD', () => {
    const result = formatSingleSalary(100000, 'USD');
    expect(result).toBe('$100,000');
  });

  it('should return empty string when amount is null', () => {
    const result = formatSingleSalary(null, 'GBP');
    expect(result).toBe('');
  });

  it('should return empty string when currency is null', () => {
    const result = formatSingleSalary(50000, null);
    expect(result).toBe('');
  });
});

// ==================== SALARY PARSING TESTS ====================

describe('parseSalaryString', () => {
  it('should parse USD range', () => {
    const result = parseSalaryString('$80,000 - $120,000');
    expect(result).toEqual({ min: 80000, max: 120000, currency: 'USD' });
  });

  it('should parse GBP range', () => {
    const result = parseSalaryString('£50,000 - £70,000');
    expect(result).toEqual({ min: 50000, max: 70000, currency: 'GBP' });
  });

  it('should parse EUR range', () => {
    const result = parseSalaryString('€45,000 - €65,000');
    expect(result).toEqual({ min: 45000, max: 65000, currency: 'EUR' });
  });

  it('should parse "k" notation', () => {
    const result = parseSalaryString('$80k - $120k');
    expect(result).toEqual({ min: 80000, max: 120000, currency: 'USD' });
  });

  it('should parse single value', () => {
    const result = parseSalaryString('£60,000');
    expect(result).toEqual({ min: 60000, max: 60000, currency: 'GBP' });
  });

  it('should handle currency code instead of symbol', () => {
    const result = parseSalaryString('50000-70000 GBP');
    expect(result).toEqual({ min: 50000, max: 70000, currency: 'GBP' });
  });

  it('should return nulls for empty string', () => {
    const result = parseSalaryString('');
    expect(result).toEqual({ min: null, max: null, currency: null });
  });

  it('should return nulls when no numbers found', () => {
    const result = parseSalaryString('Competitive salary');
    expect(result).toEqual({ min: null, max: null, currency: null });
  });

  it('should handle ranges without commas', () => {
    const result = parseSalaryString('$80000-$120000');
    expect(result).toEqual({ min: 80000, max: 120000, currency: 'USD' });
  });
});

// ==================== EMAIL VALIDATION TESTS ====================

describe('isValidEmail', () => {
  it('should validate correct email', () => {
    expect(isValidEmail('test@example.com')).toBe(true);
  });

  it('should validate email with subdomain', () => {
    expect(isValidEmail('user@mail.example.com')).toBe(true);
  });

  it('should validate email with plus sign', () => {
    expect(isValidEmail('user+tag@example.com')).toBe(true);
  });

  it('should reject email without @', () => {
    expect(isValidEmail('userexample.com')).toBe(false);
  });

  it('should reject email without domain', () => {
    expect(isValidEmail('user@')).toBe(false);
  });

  it('should reject email without user', () => {
    expect(isValidEmail('@example.com')).toBe(false);
  });

  it('should reject email with spaces', () => {
    expect(isValidEmail('user @example.com')).toBe(false);
  });

  it('should reject empty string', () => {
    expect(isValidEmail('')).toBe(false);
  });
});

// ==================== LINKEDIN URL VALIDATION TESTS ====================

describe('isValidLinkedInUrl', () => {
  it('should validate LinkedIn profile URL', () => {
    expect(isValidLinkedInUrl('https://linkedin.com/in/johndoe')).toBe(true);
  });

  it('should validate LinkedIn company URL', () => {
    expect(isValidLinkedInUrl('https://linkedin.com/company/techcorp')).toBe(true);
  });

  it('should validate URL with www', () => {
    expect(isValidLinkedInUrl('https://www.linkedin.com/in/janedoe')).toBe(true);
  });

  it('should reject non-LinkedIn URL', () => {
    expect(isValidLinkedInUrl('https://twitter.com/user')).toBe(false);
  });

  it('should reject empty string', () => {
    expect(isValidLinkedInUrl('')).toBe(false);
  });

  it('should reject partial LinkedIn URL', () => {
    expect(isValidLinkedInUrl('linkedin.com')).toBe(false);
  });
});

describe('isLinkedInJobUrl', () => {
  it('should validate LinkedIn job URL', () => {
    expect(isLinkedInJobUrl('https://linkedin.com/jobs/view/12345')).toBe(true);
  });

  it('should validate LinkedIn jobs search URL', () => {
    expect(isLinkedInJobUrl('https://www.linkedin.com/jobs/search')).toBe(true);
  });

  it('should reject LinkedIn profile URL', () => {
    expect(isLinkedInJobUrl('https://linkedin.com/in/user')).toBe(false);
  });

  it('should reject non-LinkedIn URL', () => {
    expect(isLinkedInJobUrl('https://example.com/jobs')).toBe(false);
  });

  it('should reject empty string', () => {
    expect(isLinkedInJobUrl('')).toBe(false);
  });
});

// ==================== URL CLEANING TESTS ====================

describe('cleanUrl', () => {
  it('should add https:// to URL without protocol', () => {
    const result = cleanUrl('example.com');
    expect(result).toBe('https://example.com');
  });

  it('should preserve https:// URLs', () => {
    const result = cleanUrl('https://example.com');
    expect(result).toBe('https://example.com');
  });

  it('should preserve http:// URLs', () => {
    const result = cleanUrl('http://example.com');
    expect(result).toBe('http://example.com');
  });

  it('should trim whitespace', () => {
    const result = cleanUrl('  example.com  ');
    expect(result).toBe('https://example.com');
  });

  it('should return empty string for empty input', () => {
    const result = cleanUrl('');
    expect(result).toBe('');
  });
});

// ==================== DATE FORMATTING TESTS ====================

describe('formatDate', () => {
  it('should format ISO date string', () => {
    const result = formatDate('2025-02-15');
    expect(result).toMatch(/15.*Feb.*2025/);
  });

  it('should return empty string for null', () => {
    const result = formatDate(null);
    expect(result).toBe('');
  });

  it('should return empty string for undefined', () => {
    const result = formatDate(undefined);
    expect(result).toBe('');
  });

  it('should handle invalid date gracefully', () => {
    const result = formatDate('not-a-date');
    // Invalid dates result in "Invalid Date" from toLocaleString
    expect(result).toContain('Invalid');
  });
});

describe('daysBetween', () => {
  it('should calculate days between two dates', () => {
    const days = daysBetween('2025-01-01', '2025-01-10');
    expect(days).toBe(9);
  });

  it('should handle Date objects', () => {
    const date1 = new Date('2025-01-01');
    const date2 = new Date('2025-01-10');
    const days = daysBetween(date1, date2);
    expect(days).toBe(9);
  });

  it('should return absolute difference (order independent)', () => {
    const days1 = daysBetween('2025-01-01', '2025-01-10');
    const days2 = daysBetween('2025-01-10', '2025-01-01');
    expect(days1).toBe(days2);
  });
});

// ==================== STRING FORMATTING TESTS ====================

describe('capitalizeWords', () => {
  it('should capitalize first letter of each word', () => {
    const result = capitalizeWords('hello world');
    expect(result).toBe('Hello World');
  });

  it('should handle all lowercase', () => {
    const result = capitalizeWords('software engineer');
    expect(result).toBe('Software Engineer');
  });

  it('should handle all uppercase', () => {
    const result = capitalizeWords('LOUD NOISES');
    expect(result).toBe('Loud Noises');
  });

  it('should return empty string for empty input', () => {
    const result = capitalizeWords('');
    expect(result).toBe('');
  });

  it('should handle single word', () => {
    const result = capitalizeWords('test');
    expect(result).toBe('Test');
  });
});

describe('truncate', () => {
  it('should truncate long text', () => {
    const result = truncate('This is a very long text', 10);
    expect(result).toBe('This is a ...');
  });

  it('should not truncate short text', () => {
    const result = truncate('Short', 10);
    expect(result).toBe('Short');
  });

  it('should handle exact length', () => {
    const result = truncate('Exactly 10', 10);
    expect(result).toBe('Exactly 10');
  });

  it('should handle empty string', () => {
    const result = truncate('', 10);
    expect(result).toBe('');
  });
});

// ==================== EXPERIENCE LEVEL TESTS ====================

describe('formatExperienceLevel', () => {
  it('should format junior level', () => {
    const result = formatExperienceLevel('junior');
    expect(result).toBe('Junior');
  });

  it('should format mid level', () => {
    const result = formatExperienceLevel('mid');
    expect(result).toBe('Mid-Level');
  });

  it('should format senior level', () => {
    const result = formatExperienceLevel('senior');
    expect(result).toBe('Senior');
  });

  it('should format staff level', () => {
    const result = formatExperienceLevel('staff');
    expect(result).toBe('Staff');
  });

  it('should format principal level', () => {
    const result = formatExperienceLevel('principal');
    expect(result).toBe('Principal');
  });

  it('should capitalize unknown levels', () => {
    const result = formatExperienceLevel('lead');
    expect(result).toBe('Lead');
  });

  it('should handle null', () => {
    const result = formatExperienceLevel(null);
    expect(result).toBe('');
  });

  it('should be case-insensitive', () => {
    const result = formatExperienceLevel('SENIOR');
    expect(result).toBe('Senior');
  });
});

describe('getExperienceLevelColor', () => {
  it('should return info for junior', () => {
    const result = getExperienceLevelColor('junior');
    expect(result).toBe('info');
  });

  it('should return success for mid', () => {
    const result = getExperienceLevelColor('mid');
    expect(result).toBe('success');
  });

  it('should return warning for senior', () => {
    const result = getExperienceLevelColor('senior');
    expect(result).toBe('warning');
  });

  it('should return purple for staff', () => {
    const result = getExperienceLevelColor('staff');
    expect(result).toBe('purple');
  });

  it('should return purple for principal', () => {
    const result = getExperienceLevelColor('principal');
    expect(result).toBe('purple');
  });

  it('should return default for unknown level', () => {
    const result = getExperienceLevelColor('lead');
    expect(result).toBe('default');
  });

  it('should return default for null', () => {
    const result = getExperienceLevelColor(null);
    expect(result).toBe('default');
  });

  it('should be case-insensitive', () => {
    const result = getExperienceLevelColor('JUNIOR');
    expect(result).toBe('info');
  });
});

// ==================== ARRAY PARSING TESTS ====================

describe('parseCommaSeparated', () => {
  it('should parse comma-separated string', () => {
    const result = parseCommaSeparated('Python, JavaScript, TypeScript');
    expect(result).toEqual(['Python', 'JavaScript', 'TypeScript']);
  });

  it('should trim whitespace', () => {
    const result = parseCommaSeparated('  Python  ,  JavaScript  ,  TypeScript  ');
    expect(result).toEqual(['Python', 'JavaScript', 'TypeScript']);
  });

  it('should filter empty strings', () => {
    const result = parseCommaSeparated('Python,, JavaScript, , TypeScript');
    expect(result).toEqual(['Python', 'JavaScript', 'TypeScript']);
  });

  it('should return empty array for empty string', () => {
    const result = parseCommaSeparated('');
    expect(result).toEqual([]);
  });

  it('should handle single item', () => {
    const result = parseCommaSeparated('Python');
    expect(result).toEqual(['Python']);
  });
});

describe('joinWithCommas', () => {
  it('should join array with commas', () => {
    const result = joinWithCommas(['Python', 'JavaScript', 'TypeScript']);
    expect(result).toBe('Python, JavaScript, TypeScript');
  });

  it('should handle single item', () => {
    const result = joinWithCommas(['Python']);
    expect(result).toBe('Python');
  });

  it('should return empty string for empty array', () => {
    const result = joinWithCommas([]);
    expect(result).toBe('');
  });

  it('should return empty string for null', () => {
    const result = joinWithCommas(null);
    expect(result).toBe('');
  });

  it('should return empty string for undefined', () => {
    const result = joinWithCommas(undefined);
    expect(result).toBe('');
  });
});
