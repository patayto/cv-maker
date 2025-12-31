"""
LinkedIn-specific job posting parser.

Uses LinkedIn's HTML structure to extract job details with high accuracy.
"""

from bs4 import BeautifulSoup
from typing import Dict, Optional, Tuple
import re


class LinkedInParser:
    """Parse LinkedIn job postings using specific CSS selectors"""

    @staticmethod
    def is_linkedin_url(url: str) -> bool:
        """Check if URL is a LinkedIn job posting"""
        return 'linkedin.com/jobs' in url.lower()

    def parse(self, html: str, text: str, url: str) -> Dict[str, Optional[any]]:
        """
        Parse LinkedIn job posting using specific selectors.

        Args:
            html: Raw HTML content
            text: Plain text content
            url: Job posting URL

        Returns:
            Dictionary with extracted job data
        """
        soup = BeautifulSoup(html, 'html.parser')

        job_data = {
            'url': url,
            'role': self._extract_role(soup),
            'company': self._extract_company(soup),
            'location': self._extract_location(soup),
            'workplace_type': None,  # Will be set by _extract_job_criteria
            'employment_type': None,  # Will be set by _extract_job_criteria
            'department': None,
            'salary': self._extract_salary(soup),
            'notes': None,
        }

        # Extract workplace type and employment type
        workplace, employment = self._extract_job_criteria(soup)
        job_data['workplace_type'] = workplace
        job_data['employment_type'] = employment

        # Extract structured data from job description
        desc_data = self._extract_from_description(soup)
        job_data.update(desc_data)

        # Extract recruiter information
        recruiter_info = self._extract_recruiter_info(soup)
        job_data.update(recruiter_info)

        # Check if LinkedIn blocked the request (no job content found)
        if not job_data['role'] and not job_data['company']:
            # Build diagnostic info
            debug_info = []
            debug_info.append(f"HTML: {len(html)} chars")
            debug_info.append(f"Text: {len(text)} chars")

            html_lower = html.lower() if html else ''
            text_lower = text.lower() if text else ''

            # Detect what type of page we received
            if 'authwall' in html_lower:
                debug_info.append("authwall detected")
            if 'captcha' in html_lower or 'challenge' in html_lower:
                debug_info.append("captcha/challenge detected")
            if 'rate limit' in text_lower or 'too many requests' in text_lower:
                debug_info.append("rate limited")

            debug_str = f" | Debug: {', '.join(debug_info)}"

            # Check for signs of blocked/login page
            if any(indicator in text_lower for indicator in ['sign in', 'join now', 'log in', 'authwall']):
                job_data['notes'] = f'LinkedIn requires authentication. Add your li_at cookie to .env file (LINKEDIN_LI_AT), or copy the job details manually.{debug_str}'
            else:
                job_data['notes'] = f'Could not extract job details from LinkedIn. The page structure may have changed or the job may no longer be available.{debug_str}'

        return job_data

    def _extract_role(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract job title from LinkedIn posting"""
        # Try main job title selector
        title_elem = soup.select_one('.job-details-jobs-unified-top-card__job-title h1')
        if title_elem:
            return title_elem.get_text(strip=True)

        # Fallback to alternative selectors
        title_elem = soup.select_one('h1.t-24.t-bold')
        if title_elem:
            return title_elem.get_text(strip=True)

        # Try sticky header
        title_elem = soup.select_one('.job-details-jobs-unified-top-card__sticky-header-job-title strong')
        if title_elem:
            return title_elem.get_text(strip=True)

        return None

    def _extract_company(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract company name from LinkedIn posting"""
        company_elem = soup.select_one('.job-details-jobs-unified-top-card__company-name a')
        if company_elem:
            return company_elem.get_text(strip=True)

        # Fallback
        company_elem = soup.select_one('.job-details-jobs-unified-top-card__company-name')
        if company_elem:
            return company_elem.get_text(strip=True)

        return None

    def _extract_location(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract location from LinkedIn posting"""
        # Primary location selector
        location_elem = soup.select_one('.job-details-jobs-unified-top-card__tertiary-description-container .tvm__text')
        if location_elem:
            location = location_elem.get_text(strip=True)
            # Clean up - LinkedIn often includes extra metadata
            # Keep only the location part (before any bullet points or extra info)
            if '·' in location:
                location = location.split('·')[0].strip()
            return location

        # Alternative selector
        location_elems = soup.select('.job-details-jobs-unified-top-card__tertiary-description span')
        for elem in location_elems:
            text = elem.get_text(strip=True)
            # Look for location patterns
            if any(indicator in text.lower() for indicator in ['remote', 'hybrid', 'on-site']) or ',' in text:
                if '·' in text:
                    text = text.split('·')[0].strip()
                return text

        return None

    def _extract_job_criteria(self, soup: BeautifulSoup) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract workplace type and employment type from job criteria section.

        Returns:
            (workplace_type, employment_type) tuple
        """
        workplace_type = None
        employment_type = None

        # LinkedIn shows these as buttons in the fit-level-preferences section
        fit_buttons = soup.select('.job-details-fit-level-preferences button span')

        for btn in fit_buttons:
            text = btn.get_text(strip=True)

            # Check for workplace type
            if text in ['Remote', 'Hybrid', 'On-site']:
                workplace_type = text

            # Check for employment type
            elif text in ['Full-time', 'Part-time', 'Contract', 'Temporary', 'Internship', 'Volunteer']:
                employment_type = text

        return workplace_type, employment_type

    def _extract_salary(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract salary information if available"""
        # LinkedIn salary div (often empty)
        salary_elem = soup.select_one('#SALARY')
        if salary_elem:
            salary_text = salary_elem.get_text(strip=True)
            if salary_text:
                return salary_text

        # Alternative: look in job description for salary mentions
        desc_elem = soup.select_one('#job-details')
        if desc_elem:
            desc_text = desc_elem.get_text()
            # Look for salary patterns
            salary_pattern = r'[£$€][\d,]+(?:\s*-\s*[£$€]?[\d,]+)?(?:\s*(?:per|/)\s*(?:year|yr|hour|hr|annum|month))?'
            matches = re.findall(salary_pattern, desc_text[:2000])  # Search first 2000 chars
            if matches:
                return matches[0]

        return None

    def _extract_recruiter_info(self, soup: BeautifulSoup) -> Dict[str, Optional[str]]:
        """
        Extract recruiter information from LinkedIn posting.

        Returns:
            Dictionary with recruiter_name, recruiter_linkedin, recruiter_email (all Optional[str])
        """
        recruiter_info = {
            'recruiter_name': None,
            'recruiter_linkedin': None,
            'recruiter_email': None
        }

        # Look for "Meet the hiring team" section
        # Try .jobs-poster__profile-link selector
        poster_link = soup.select_one('.jobs-poster__profile-link')
        if poster_link:
            # Extract name from .jobs-poster__name
            name_elem = poster_link.select_one('.jobs-poster__name')
            if name_elem:
                recruiter_info['recruiter_name'] = name_elem.get_text(strip=True)

            # Extract LinkedIn profile URL from href
            href = poster_link.get('href')
            if href and 'linkedin.com/in/' in href:
                # Clean up URL (remove query params)
                if '?' in href:
                    href = href.split('?')[0]
                recruiter_info['recruiter_linkedin'] = href

        # Try .hirer-card__hirer-information selector as alternative
        if not recruiter_info['recruiter_name']:
            hirer_card = soup.select_one('.hirer-card__hirer-information')
            if hirer_card:
                # Extract name from .hirer-card__name
                name_elem = hirer_card.select_one('.hirer-card__name')
                if name_elem:
                    recruiter_info['recruiter_name'] = name_elem.get_text(strip=True)

                # Look for LinkedIn profile link in parent elements
                parent_link = hirer_card.find_parent('a')
                if parent_link:
                    href = parent_link.get('href')
                    if href and 'linkedin.com/in/' in href:
                        if '?' in href:
                            href = href.split('?')[0]
                        recruiter_info['recruiter_linkedin'] = href

        # Note: Email extraction is typically not available on public LinkedIn job pages
        # LinkedIn doesn't publicly display recruiter emails for privacy reasons
        # This field is left as None but available for future enhancement

        return recruiter_info

    def _extract_from_description(self, soup: BeautifulSoup) -> Dict[str, any]:
        """
        Extract skills, requirements, and responsibilities from job description.

        Returns:
            Dictionary with parsed_skills, parsed_requirements, parsed_responsibilities
        """
        desc_elem = soup.select_one('#job-details')
        if not desc_elem:
            desc_elem = soup.select_one('.jobs-box__html-content')

        if not desc_elem:
            return {
                'parsed_skills': [],
                'parsed_requirements': [],
                'parsed_responsibilities': [],
                'notes': None
            }

        skills = []
        requirements = []
        responsibilities = []

        # Track current section based on headers
        current_section = None

        # Iterate through all elements in the description
        for elem in desc_elem.find_all(['h2', 'h3', 'strong', 'b', 'ul', 'li', 'p']):
            text = elem.get_text(strip=True)
            text_lower = text.lower()

            # Identify section headers
            if elem.name in ['h2', 'h3', 'strong', 'b']:
                # Requirements/Qualifications section
                if any(keyword in text_lower for keyword in [
                    'what you\'ll need', 'requirements', 'qualifications',
                    'what we\'re looking for', 'you should have', 'must have',
                    'required skills', 'required qualifications'
                ]):
                    current_section = 'requirements'
                    continue

                # Responsibilities section
                elif any(keyword in text_lower for keyword in [
                    'what you\'ll do', 'responsibilities', 'you will',
                    'role responsibilities', 'your role', 'day to day',
                    'what you will do', 'your responsibilities'
                ]):
                    current_section = 'responsibilities'
                    continue

                # Skills/Technologies section
                elif any(keyword in text_lower for keyword in [
                    'skills', 'technologies', 'technical requirements',
                    'tech stack', 'tools', 'preferred skills'
                ]):
                    current_section = 'skills'
                    continue

            # Extract list items based on current section
            if elem.name == 'li' and text and len(text) > 2:  # Ignore empty or very short items
                item_text = text

                # Add to appropriate section
                if current_section == 'skills':
                    skills.append(item_text)
                elif current_section == 'requirements':
                    requirements.append(item_text)
                elif current_section == 'responsibilities':
                    responsibilities.append(item_text)
                else:
                    # If no section identified, try to categorize by content
                    # Skills often mention specific technologies
                    if any(tech in text_lower for tech in ['python', 'java', 'javascript', 'aws', 'docker', 'kubernetes', 'sql', 'react', 'node']):
                        skills.append(item_text)
                    # Responsibilities often start with action verbs
                    elif any(text_lower.startswith(verb) for verb in ['develop', 'design', 'build', 'create', 'implement', 'manage', 'lead', 'collaborate', 'work with']):
                        responsibilities.append(item_text)
                    else:
                        requirements.append(item_text)

        # Generate brief notes from first paragraph
        notes = None
        first_p = desc_elem.find('p')
        if first_p:
            first_text = first_p.get_text(strip=True)
            if first_text and len(first_text) > 20:
                # Truncate to ~150 chars for notes
                notes = first_text[:150] + ('...' if len(first_text) > 150 else '')

        return {
            'parsed_skills': skills[:20],  # Limit to top 20
            'parsed_requirements': requirements[:15],  # Limit to top 15
            'parsed_responsibilities': responsibilities[:15],  # Limit to top 15
            'notes': notes
        }
