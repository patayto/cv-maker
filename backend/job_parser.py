import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

import linkedin_guest
import llm
from parsers.linkedin_parser import LinkedInParser

# Load environment variables
load_dotenv()

# Configure logging for debug mode
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class JobParser:
    def __init__(self):
        self.llm_client = llm.get_client()
        if self.llm_client:
            logger.info("OpenRouter LLM client initialized.")
        else:
            logger.warning("No OPENROUTER_API_KEY found. Proceeding without AI.")

        # Create session for requests (enables cookie persistence)
        self.session = requests.Session()

    def fetch_page_content(self, url: str) -> tuple[Optional[str], Optional[str]]:
        """Fetch the HTML content and text from a URL"""
        debug_mode = os.getenv("DEBUG_SCRAPING", "").lower() == "true"

        try:
            # Use comprehensive headers to avoid being blocked by LinkedIn and other sites
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Cache-Control": "max-age=0",
            }
            response = self.session.get(
                url, headers=headers, timeout=15, allow_redirects=True
            )

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
                debug_file.write_text(response.text, encoding="utf-8")
                logger.info(f"Raw HTML saved to: {debug_file.absolute()}")
                logger.info(f"HTML length: {len(response.text)} chars")
                logger.info("=" * 60)

            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Get text
            text = soup.get_text(separator="\n", strip=True)
            # Clean up whitespace
            text = re.sub(r"\n\s*\n", "\n\n", text)

            return response.text, text
        except Exception as e:
            if debug_mode:
                logger.error(f"Error fetching URL: {e}")
            else:
                print(f"Error fetching URL: {e}")
            return None, None

    def parse_basic_info(
        self, html: str, text: str, url: str
    ) -> Dict[str, Optional[str]]:
        """Parse basic job information from HTML/text using simple heuristics"""
        soup = BeautifulSoup(html, "html.parser")

        job_data = {
            "url": url,
            "role": None,
            "company": None,
            "location": None,
            "department": None,
            "salary": None,
        }

        # Try to find job title
        # Look in common places: h1, title, meta tags
        title_candidates = []

        # Check meta tags
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title_candidates.append(og_title["content"])

        # Check title tag
        if soup.title and soup.title.string:
            title_candidates.append(soup.title.string)

        # Check h1 tags
        h1_tags = soup.find_all("h1", limit=3)
        for h1 in h1_tags:
            if h1.get_text(strip=True):
                title_candidates.append(h1.get_text(strip=True))

        # Try to identify which is the job title
        company_from_title = None
        for candidate in title_candidates:
            # Skip if too long or too short
            if 5 < len(candidate) < 100:
                # Cut site-name separators ("Role at X | LinkedIn") and
                # trailing " at Company", then legacy careers-page suffixes
                cleaned = re.split(r"\s+[|·–]\s+", candidate)[0]
                at_company = re.search(r"\s+at\s+([A-Z][\w&.' -]*)$", cleaned)
                if at_company:
                    company_from_title = at_company.group(1).strip()
                    cleaned = cleaned[: at_company.start()]
                cleaned = re.sub(
                    r"\s*[-|]\s*(Careers?|Jobs?|Apply Now|Company Name).*$",
                    "",
                    cleaned,
                    flags=re.IGNORECASE,
                )
                if cleaned:
                    job_data["role"] = cleaned.strip()
                    break

        # Try to find company name
        company_patterns = [
            soup.find("meta", property="og:site_name"),
            soup.find("meta", attrs={"name": "author"}),
        ]

        for pattern in company_patterns:
            if pattern and pattern.get("content"):
                job_data["company"] = pattern["content"]
                break

        if not job_data["company"] and company_from_title:
            job_data["company"] = company_from_title

        # Try to find location (look for common location patterns)
        location_pattern = (
            r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2}|Remote|Hybrid)\b"
        )
        location_matches = re.findall(
            location_pattern, text[:2000]
        )  # Search first 2000 chars
        if location_matches:
            job_data["location"] = location_matches[0]

        # Try to find salary
        salary_pattern = r"\$[\d,]+(?:\s*-\s*\$?[\d,]+)?(?:\s*(?:per|/)\s*(?:year|yr|hour|hr|annum))?"
        salary_matches = re.findall(salary_pattern, text[:3000])
        if salary_matches:
            job_data["salary"] = salary_matches[0]

        return job_data

    # Fields the LLM may fill in, with limits for the list-valued ones
    LLM_FIELDS = {
        "role": None,
        "company": None,
        "department": None,
        "location": None,
        "salary": None,
        "notes": None,
        "workplace_type": None,
        "employment_type": None,
        "parsed_skills": 20,
        "parsed_requirements": 15,
        "parsed_responsibilities": 15,
    }

    def extract_with_llm(self, text: str, job_data: Dict) -> Dict:
        """One structured LLM call that fills in whatever fields are still missing.

        Never overwrites fields already extracted by site-specific parsing.
        Returns job_data unchanged on any LLM/JSON failure.
        """
        if not self.llm_client:
            return job_data

        if len(text) > 12000:
            text = text[:12000] + "\n... (truncated)"

        prompt = f"""You are parsing a job posting. Extract the following from the text below.

Job posting text:
---
{text}
---

Respond with ONLY a valid JSON object (no explanation, no markdown fences) with exactly these keys, using null when a value cannot be found:

{{
  "role": "job title",
  "company": "company name",
  "department": "department or team",
  "location": "city/country, or Remote/Hybrid",
  "salary": "salary range as written in the posting",
  "notes": "1-2 sentence summary of the role",
  "workplace_type": "Remote, Hybrid, or On-site",
  "employment_type": "Full-time, Part-time, Contract, Temporary, or Internship",
  "parsed_skills": ["specific technologies, languages, frameworks, tools"],
  "parsed_requirements": ["experience, education, and must-have qualifications"],
  "parsed_responsibilities": ["what the person will actually do in the role"]
}}"""

        try:
            response_text = llm.complete(self.llm_client, prompt)
            json_match = re.search(r"\{[\s\S]*\}", response_text)
            if not json_match:
                return job_data

            import json

            llm_data = json.loads(json_match.group())

            result = job_data.copy()
            for key, limit in self.LLM_FIELDS.items():
                value = llm_data.get(key)
                if not value or value == "null" or result.get(key):
                    continue
                if limit is not None:
                    if not isinstance(value, list):
                        continue
                    value = [str(v) for v in value[:limit]]
                result[key] = value
            return result

        except Exception as e:
            logger.warning(f"LLM extraction failed: {e}")
            return job_data

    def parse_job_url(
        self, url: str, use_llm: bool = True, html: Optional[str] = None
    ) -> tuple[Dict[str, Optional[str]], List[str]]:
        """
        Parse a job posting from URL or raw HTML and return job details

        Args:
            url: URL of the job posting (used for metadata if html provided)
            use_llm: Whether to use the LLM for enhanced parsing
            html: Optional raw HTML content (bypasses fetching if provided)

        Returns:
            (job_data, missing_fields)
        """
        job_data = None

        # HTML mode: Use provided HTML
        if html:
            soup = BeautifulSoup(html, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Get text
            text = soup.get_text(separator="\n", strip=True)
            # Clean up whitespace
            text = re.sub(r"\n\s*\n", "\n\n", text)
        elif LinkedInParser.is_linkedin_url(url):
            # LinkedIn URL mode: use the public jobs-guest API (no auth, no
            # browser). Replaces the old Playwright/cookie fetcher, which
            # LinkedIn's bot detection blocked.
            job_id = linkedin_guest.id_from_url(url)
            detail = linkedin_guest.fetch_job_detail(job_id) if job_id else None
            if not detail:
                return {
                    "url": url,
                    "role": None,
                    "company": None,
                    "location": None,
                    "department": None,
                    "salary": None,
                    "notes": "Could not fetch this LinkedIn job via the public API. "
                    "The posting may be closed; try pasting the page HTML instead.",
                }, ["role", "company", "location", "department", "salary"]
            job_data = {
                "url": url,
                "role": detail.title if detail.title != "(untitled)" else None,
                "company": detail.company,
                "location": detail.location,
                "department": detail.job_function,
                "salary": None,
                "employment_type": detail.employment_type,
            }
            text = "\n".join(p for p in [detail.title, detail.description] if p)
        else:
            # URL mode: Fetch page content
            html, text = self.fetch_page_content(url)

        if job_data is None:
            if not html or not text:
                return {
                    "url": url,
                    "role": None,
                    "company": None,
                    "location": None,
                    "department": None,
                    "salary": None,
                    "notes": "Failed to fetch page content"
                    if not html
                    else "Empty HTML provided",
                }, ["role", "company", "location", "department", "salary"]

            # Check if LinkedIn HTML (paste mode) and use specialized parser
            if LinkedInParser.is_linkedin_url(url):
                linkedin_parser = LinkedInParser()
                job_data = linkedin_parser.parse(html, text, url)
            else:
                # Use generic parsing for other sites
                job_data = self.parse_basic_info(html, text, url)

        # Process non-AI fields (regex and keyword matching - always runs)
        if text:
            # Parse salary into structured format (regex-based, no AI)
            if job_data.get("salary"):
                salary_min, salary_max, salary_currency = self.parse_salary(
                    job_data["salary"]
                )
                job_data["salary_min"] = salary_min
                job_data["salary_max"] = salary_max
                job_data["salary_currency"] = salary_currency

            # Determine experience level (keyword matching, no AI)
            if not job_data.get("experience_level"):
                job_data["experience_level"] = self.determine_experience_level(text)

        # OPTIONAL AI Enhancement: one structured call fills whatever the
        # site-specific parsing didn't already extract (paste-mode LinkedIn
        # fills skills/requirements/responsibilities from the DOM)
        if use_llm and self.llm_client and text:
            if any(not job_data.get(field) for field in self.LLM_FIELDS):
                job_data = self.extract_with_llm(text, job_data)

            # LLM may have found a salary string the regexes missed
            if job_data.get("salary") and not job_data.get("salary_min"):
                salary_min, salary_max, salary_currency = self.parse_salary(
                    job_data["salary"]
                )
                job_data["salary_min"] = salary_min
                job_data["salary_max"] = salary_max
                job_data["salary_currency"] = salary_currency

        # Identify missing fields
        missing_fields = self._get_missing_fields(job_data)

        return job_data, missing_fields

    def _get_missing_fields(self, job_data: Dict) -> List[str]:
        """Identify which important fields are missing from job data"""
        missing = []
        important_fields = ["role", "company", "location"]

        for field in important_fields:
            if not job_data.get(field):
                missing.append(field)

        return missing

    def parse_salary(
        self, salary_str: str
    ) -> Tuple[Optional[int], Optional[int], Optional[str]]:
        """
        Parse salary string into min, max, and currency.

        Returns:
            (min_salary, max_salary, currency) tuple
        """
        if not salary_str:
            return (None, None, None)

        # Detect currency
        currency = None
        if "£" in salary_str or "GBP" in salary_str.upper():
            currency = "GBP"
        elif "$" in salary_str or "USD" in salary_str.upper():
            currency = "USD"
        elif "€" in salary_str or "EUR" in salary_str.upper():
            currency = "EUR"

        # Extract numbers (handle formats like $80k-$120k or £50,000)
        numbers = re.findall(r"[\d,]+", salary_str)
        if not numbers:
            return (None, None, currency)

        # Convert to integers
        salary_values = []
        for num_str in numbers:
            num = int(num_str.replace(",", ""))
            # Handle 'k' notation (e.g., 80k = 80000)
            if "k" in salary_str.lower():
                num = num * 1000
            salary_values.append(num)

        # If hourly rate, convert to yearly (assume 40h/week, 52 weeks)
        if any(
            indicator in salary_str.lower()
            for indicator in ["/hour", "per hour", "/hr", "hourly"]
        ):
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

        # Earliest keyword in the text wins, so a "Senior..." title beats a
        # later mention of "junior developers" in the description (and vice versa)
        level_keywords = {
            "junior": ["junior", "entry level", "graduate", "early career"],
            "staff": ["staff engineer", "staff software"],
            "principal": ["principal", "distinguished"],
            "senior": ["senior", "sr.", "lead"],
            "mid": ["mid-level", "intermediate", "mid level"],
        }
        hits = [
            (text_lower.find(keyword), level)
            for level, keywords in level_keywords.items()
            for keyword in keywords
            if keyword in text_lower
        ]
        if hits:
            return min(hits)[1]

        # Check years of experience mentioned
        years_match = re.search(r"(\d+)\+?\s*years?\s*(?:of)?\s*experience", text_lower)
        if years_match:
            years = int(years_match.group(1))
            if years <= 2:
                return "junior"
            elif years <= 5:
                return "mid"
            elif years <= 8:
                return "senior"
            else:
                return "staff"

        # Default to mid if unclear
        return "mid"


# Singleton instance
job_parser = JobParser()
