import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional, List, Tuple
from anthropic import Anthropic
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
import re
from parsers.linkedin_parser import LinkedInParser
from browser_fetcher import BrowserFetcher

# Load environment variables
load_dotenv()

# Configure logging for debug mode
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JobParser:
    def __init__(self):
        self.anthropic_client = None
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            self.anthropic_client = Anthropic(api_key=api_key)

        # Create session for requests (enables cookie persistence)
        self.session = requests.Session()

        # Load LinkedIn cookie if available (for authenticated scraping)
        linkedin_cookie = os.getenv("LINKEDIN_LI_AT")
        if linkedin_cookie:
            self.session.cookies.set("li_at", linkedin_cookie, domain=".linkedin.com")

        # Create browser fetcher for JavaScript-rendered pages (e.g., LinkedIn)
        self.browser_fetcher = BrowserFetcher()

    def fetch_page_content(self, url: str) -> tuple[Optional[str], Optional[str]]:
        """Fetch the HTML content and text from a URL"""
        debug_mode = os.getenv("DEBUG_SCRAPING", "").lower() == "true"

        # Use browser fetcher for LinkedIn (JavaScript-rendered content)
        if 'linkedin.com/jobs' in url.lower():
            if debug_mode:
                logger.info("Using browser fetcher for LinkedIn URL")
            return self.browser_fetcher.fetch(url)

        # Use regular HTTP requests for other sites
        try:
            # Use comprehensive headers to avoid being blocked by LinkedIn and other sites
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            }
            response = self.session.get(url, headers=headers, timeout=15, allow_redirects=True)

            # Debug logging
            if debug_mode:
                logger.info("=" * 60)
                logger.info(f"DEBUG: Fetching URL: {url}")
                logger.info(f"Status Code: {response.status_code}")
                logger.info(f"Final URL: {response.url}")
                if response.history:
                    logger.info(f"Redirect chain: {[r.url for r in response.history]}")
                logger.info(f"Response headers: {dict(response.headers)}")
                logger.info(f"Cookies in session: {dict(self.session.cookies)}")

                # Save raw HTML to debug file
                debug_dir = Path(__file__).parent / "debug"
                debug_dir.mkdir(exist_ok=True)
                debug_file = debug_dir / "last_response.html"
                debug_file.write_text(response.text, encoding='utf-8')
                logger.info(f"Raw HTML saved to: {debug_file.absolute()}")
                logger.info(f"HTML length: {len(response.text)} chars")
                logger.info("=" * 60)

            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Get text
            text = soup.get_text(separator='\n', strip=True)
            # Clean up whitespace
            text = re.sub(r'\n\s*\n', '\n\n', text)

            return response.text, text
        except Exception as e:
            if debug_mode:
                logger.error(f"Error fetching URL: {e}")
            else:
                print(f"Error fetching URL: {e}")
            return None, None

    def parse_basic_info(self, html: str, text: str, url: str) -> Dict[str, Optional[str]]:
        """Parse basic job information from HTML/text using simple heuristics"""
        soup = BeautifulSoup(html, 'html.parser')

        job_data = {
            'url': url,
            'role': None,
            'company': None,
            'location': None,
            'department': None,
            'salary': None,
        }

        # Try to find job title
        # Look in common places: h1, title, meta tags
        title_candidates = []

        # Check meta tags
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            title_candidates.append(og_title['content'])

        # Check title tag
        if soup.title and soup.title.string:
            title_candidates.append(soup.title.string)

        # Check h1 tags
        h1_tags = soup.find_all('h1', limit=3)
        for h1 in h1_tags:
            if h1.get_text(strip=True):
                title_candidates.append(h1.get_text(strip=True))

        # Try to identify which is the job title
        for candidate in title_candidates:
            # Skip if too long or too short
            if 5 < len(candidate) < 100:
                # Remove common suffixes
                cleaned = re.sub(r'\s*[-|]\s*(Careers?|Jobs?|Apply Now|Company Name).*$', '', candidate, flags=re.IGNORECASE)
                if cleaned:
                    job_data['role'] = cleaned.strip()
                    break

        # Try to find company name
        company_patterns = [
            soup.find('meta', property='og:site_name'),
            soup.find('meta', attrs={'name': 'author'}),
        ]

        for pattern in company_patterns:
            if pattern and pattern.get('content'):
                job_data['company'] = pattern['content']
                break

        # Try to find location (look for common location patterns)
        location_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2}|Remote|Hybrid)\b'
        location_matches = re.findall(location_pattern, text[:2000])  # Search first 2000 chars
        if location_matches:
            job_data['location'] = location_matches[0]

        # Try to find salary
        salary_pattern = r'\$[\d,]+(?:\s*-\s*\$?[\d,]+)?(?:\s*(?:per|/)\s*(?:year|yr|hour|hr|annum))?'
        salary_matches = re.findall(salary_pattern, text[:3000])
        if salary_matches:
            job_data['salary'] = salary_matches[0]

        return job_data

    def parse_with_llm(self, text: str, url: str, basic_info: Dict) -> Dict[str, Optional[str]]:
        """Use Claude to extract job details from the page text"""
        if not self.anthropic_client:
            return basic_info

        # Truncate text if too long (keep first 8000 chars)
        if len(text) > 8000:
            text = text[:8000] + "\n... (truncated)"

        prompt = f"""You are parsing a job posting webpage. Extract the following information from the text below.

Text from job posting:
---
{text}
---

Please extract the following fields. If a field cannot be found, respond with null:

1. role: The job title/position name
2. company: The company name
3. department: The department or team (if mentioned)
4. location: The job location (city, state, or "Remote"/"Hybrid")
5. salary: The salary range or compensation (if mentioned)
6. notes: A brief 1-2 sentence summary of what makes this role interesting or key requirements

Respond ONLY with a valid JSON object in this exact format:
{{
  "role": "job title here",
  "company": "company name",
  "department": "department name or null",
  "location": "location",
  "salary": "salary range or null",
  "notes": "brief summary or null"
}}

Do not include any explanation, just the JSON object."""

        try:
            message = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response_text = message.content[0].text.strip()

            # Extract JSON from response (in case there's extra text)
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            if json_match:
                import json
                llm_data = json.loads(json_match.group())

                # Merge with basic info, preferring LLM data when available
                result = basic_info.copy()
                for key, value in llm_data.items():
                    if value and value != "null" and key in result:
                        result[key] = value

                return result

        except Exception as e:
            print(f"Error parsing with LLM: {e}")

        return basic_info

    def parse_job_url(self, url: str, use_llm: bool = True) -> tuple[Dict[str, Optional[str]], List[str]]:
        """
        Parse a job posting URL and return job details

        Returns:
            (job_data, missing_fields)
        """
        html, text = self.fetch_page_content(url)

        if not html or not text:
            return {
                'url': url,
                'role': None,
                'company': None,
                'location': None,
                'department': None,
                'salary': None,
                'notes': 'Failed to fetch page content'
            }, ['role', 'company', 'location', 'department', 'salary']

        # Check if LinkedIn URL and use specialized parser
        if LinkedInParser.is_linkedin_url(url):
            linkedin_parser = LinkedInParser()
            job_data = linkedin_parser.parse(html, text, url)
        else:
            # Use generic parsing for other sites
            job_data = self.parse_basic_info(html, text, url)

        # Process non-AI fields (regex and keyword matching - always runs)
        if text:
            # Parse salary into structured format (regex-based, no AI)
            if job_data.get('salary'):
                salary_min, salary_max, salary_currency = self.parse_salary(job_data['salary'])
                job_data['salary_min'] = salary_min
                job_data['salary_max'] = salary_max
                job_data['salary_currency'] = salary_currency

            # Determine experience level (keyword matching, no AI)
            if not job_data.get('experience_level'):
                job_data['experience_level'] = self.determine_experience_level(text)

        # OPTIONAL AI Enhancement: Only use AI for non-LinkedIn sites when API is available
        # LinkedIn parser already extracts skills/requirements/responsibilities from HTML
        if use_llm and self.anthropic_client and text:
            # For non-LinkedIn sites, use AI to extract detailed fields
            if not LinkedInParser.is_linkedin_url(url):
                if not job_data.get('parsed_skills'):
                    job_data['parsed_skills'] = self.extract_skills(text)
                if not job_data.get('parsed_requirements'):
                    job_data['parsed_requirements'] = self.extract_requirements(text)
                if not job_data.get('parsed_responsibilities'):
                    job_data['parsed_responsibilities'] = self.extract_responsibilities(text)

        # Use LLM for missing critical fields (role, company) - optional enhancement
        # Only call AI if we're missing critical fields AND have API access
        if use_llm and self.anthropic_client and text:
            if not job_data.get('role') or not job_data.get('company'):
                job_data = self.parse_with_llm(text, url, job_data)

        # Identify missing fields
        missing_fields = self._get_missing_fields(job_data)

        return job_data, missing_fields

    def _get_missing_fields(self, job_data: Dict) -> List[str]:
        """Identify which important fields are missing from job data"""
        missing = []
        important_fields = ['role', 'company', 'location']

        for field in important_fields:
            if not job_data.get(field):
                missing.append(field)

        return missing

    def extract_skills(self, text: str) -> List[str]:
        """Extract required technical skills from job description using Claude AI"""
        if not self.anthropic_client:
            return []

        if len(text) > 8000:
            text = text[:8000] + "\n... (truncated)"

        prompt = f"""Extract the required technical skills from this job description.
Focus on specific technologies, programming languages, frameworks, and tools.

Job Description:
{text}

Respond with ONLY a JSON array of skill strings, like: ["Python", "AWS", "Docker"]
No explanation, just the JSON array."""

        try:
            message = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text.strip()
            # Extract JSON array from response
            if "[" in response_text:
                json_str = response_text[response_text.find("["):response_text.rfind("]")+1]
                import json
                skills = json.loads(json_str)
                return skills[:20]  # Limit to 20 skills

        except Exception as e:
            print(f"Error extracting skills: {e}")

        return []

    def extract_requirements(self, text: str) -> List[str]:
        """Extract job requirements/qualifications using Claude AI"""
        if not self.anthropic_client:
            return []

        if len(text) > 8000:
            text = text[:8000] + "\n... (truncated)"

        prompt = f"""Extract the key requirements and qualifications from this job description.
Focus on experience requirements, educational background, and must-have qualifications.

Job Description:
{text}

Respond with ONLY a JSON array of requirement strings.
No explanation, just the JSON array."""

        try:
            message = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text.strip()
            if "[" in response_text:
                json_str = response_text[response_text.find("["):response_text.rfind("]")+1]
                import json
                requirements = json.loads(json_str)
                return requirements[:15]  # Limit to 15 requirements

        except Exception as e:
            print(f"Error extracting requirements: {e}")

        return []

    def extract_responsibilities(self, text: str) -> List[str]:
        """Extract job responsibilities using Claude AI"""
        if not self.anthropic_client:
            return []

        if len(text) > 8000:
            text = text[:8000] + "\n... (truncated)"

        prompt = f"""Extract the key responsibilities and duties from this job description.
Focus on what the person will actually be doing in the role.

Job Description:
{text}

Respond with ONLY a JSON array of responsibility strings.
No explanation, just the JSON array."""

        try:
            message = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text.strip()
            if "[" in response_text:
                json_str = response_text[response_text.find("["):response_text.rfind("]")+1]
                import json
                responsibilities = json.loads(json_str)
                return responsibilities[:15]  # Limit to 15 responsibilities

        except Exception as e:
            print(f"Error extracting responsibilities: {e}")

        return []

    def parse_salary(self, salary_str: str) -> Tuple[Optional[int], Optional[int], Optional[str]]:
        """
        Parse salary string into min, max, and currency.

        Returns:
            (min_salary, max_salary, currency) tuple
        """
        if not salary_str:
            return (None, None, None)

        # Detect currency
        currency = None
        if '£' in salary_str or 'GBP' in salary_str.upper():
            currency = 'GBP'
        elif '$' in salary_str or 'USD' in salary_str.upper():
            currency = 'USD'
        elif '€' in salary_str or 'EUR' in salary_str.upper():
            currency = 'EUR'

        # Extract numbers (handle formats like $80k-$120k or £50,000)
        numbers = re.findall(r'[\d,]+', salary_str)
        if not numbers:
            return (None, None, currency)

        # Convert to integers
        salary_values = []
        for num_str in numbers:
            num = int(num_str.replace(',', ''))
            # Handle 'k' notation (e.g., 80k = 80000)
            if 'k' in salary_str.lower():
                num = num * 1000
            salary_values.append(num)

        # If hourly rate, convert to yearly (assume 40h/week, 52 weeks)
        if any(indicator in salary_str.lower() for indicator in ['/hour', 'per hour', '/hr', 'hourly']):
            salary_values = [int(val * 40 * 52) for val in salary_values]

        # Determine min and max
        if len(salary_values) >= 2:
            return (min(salary_values), max(salary_values), currency)
        elif len(salary_values) == 1:
            return (salary_values[0], salary_values[0], currency)

        return (None, None, currency)

    def determine_experience_level(self, text: str) -> Optional[str]:
        """
        Classify experience level from job description.

        Returns:
            One of: junior, mid, senior, staff, principal
        """
        text_lower = text.lower()

        # Check for explicit level keywords
        if any(keyword in text_lower for keyword in ['junior', 'entry level', 'graduate', 'early career']):
            return 'junior'
        elif any(keyword in text_lower for keyword in ['staff engineer', 'staff software']):
            return 'staff'
        elif any(keyword in text_lower for keyword in ['principal', 'distinguished']):
            return 'principal'
        elif any(keyword in text_lower for keyword in ['senior', 'sr.', 'lead']):
            return 'senior'
        elif any(keyword in text_lower for keyword in ['mid-level', 'intermediate', 'mid level']):
            return 'mid'

        # Check years of experience mentioned
        years_match = re.search(r'(\d+)\+?\s*years?\s*(?:of)?\s*experience', text_lower)
        if years_match:
            years = int(years_match.group(1))
            if years <= 2:
                return 'junior'
            elif years <= 5:
                return 'mid'
            elif years <= 8:
                return 'senior'
            else:
                return 'staff'

        # Default to mid if unclear
        return 'mid'


# Singleton instance
job_parser = JobParser()
