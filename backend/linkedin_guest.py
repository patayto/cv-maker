"""LinkedIn public "jobs-guest" endpoints client. No authentication required.

Python port of ai-job-search's linkedin-search CLI (MIT, MadsLorentzen/ai-job-search).
Search returns an HTML list of job cards; detail returns a single job's HTML.
Both are parsed with regex: the markup is shallow and stable, and one malformed
card must not break the rest.

Personal use only — automated access is against LinkedIn's ToS; keep volume low.
"""

import html as html_lib
import random
import re
import time
from dataclasses import asdict, dataclass
from typing import Optional
from urllib.parse import urlencode

import requests

SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
DETAIL_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting"

_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
_HEADERS = {
    "User-Agent": _UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "X-Requested-With": "XMLHttpRequest",
}


@dataclass
class JobCard:
    id: str
    title: str
    company: Optional[str]
    company_url: Optional[str]
    location: Optional[str]
    date: Optional[str]
    url: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class JobDetail(JobCard):
    description: Optional[str] = None
    seniority: Optional[str] = None
    employment_type: Optional[str] = None
    job_function: Optional[str] = None
    industries: Optional[str] = None
    apply_url: Optional[str] = None


def html_fetch(url: str, timeout: int = 15) -> str:
    """Fetch HTML with exponential backoff on 429/5xx. Returns "" on a 404."""
    max_retries = 6
    delay = 0.5
    for attempt in range(max_retries + 1):
        response = requests.get(url, headers=_HEADERS, timeout=timeout, allow_redirects=True)
        if response.status_code == 429 or response.status_code >= 500:
            if attempt == max_retries:
                raise ConnectionError(f"Request failed: {response.status_code} {response.reason}")
            time.sleep(delay + random.random() * 0.5)
            delay = min(delay * 2, 8.0)
            continue
        if response.status_code == 404:
            return ""
        response.raise_for_status()
        return response.text
    raise ConnectionError("Request failed after max retries")


def _strip_tags(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


def _clean(html: str) -> str:
    return html_lib.unescape(_strip_tags(html))


def _decode_url(url: str) -> str:
    return html_lib.unescape(url).split("?")[0]


def id_from_url(url: str) -> Optional[str]:
    """Parse the job ID out of a LinkedIn job-view URL or URN."""
    m = re.search(r"-(\d{6,})(?:\?|$)", url) or re.search(r"(\d{6,})", url)
    return m.group(1) if m else None


def parse_job_cards(html: str) -> list[JobCard]:
    """Parse the search response: a flat list of <li> job cards."""
    results = []
    chunks = re.split(r'data-entity-urn="urn:li:jobPosting:', html)[1:]

    for chunk in chunks:
        id_match = re.match(r"^(\d+)", chunk)
        if not id_match:
            continue
        job_id = id_match.group(1)

        link = re.search(r'class="base-card__full-link[^"]*"[^>]*href="([^"]+)"', chunk, re.I)
        url = _decode_url(link.group(1)) if link else ""

        title = None
        h3 = re.search(r'class="base-search-card__title"[^>]*>([\s\S]*?)</h3>', chunk, re.I)
        if h3:
            title = _clean(h3.group(1))
        if not title:
            sr = re.search(r'class="sr-only"[^>]*>([\s\S]*?)</span>', chunk, re.I)
            if sr:
                title = _clean(sr.group(1))
        if not title:
            continue

        company = None
        company_url = None
        sub = re.search(r'class="base-search-card__subtitle"[^>]*>([\s\S]*?)</h4>', chunk, re.I)
        if sub:
            a = re.search(r'href="([^"]+)"', sub.group(1), re.I)
            if a:
                company_url = _decode_url(a.group(1))
            company = _clean(sub.group(1)) or None

        loc = re.search(r'class="job-search-card__location"[^>]*>([\s\S]*?)</span>', chunk, re.I)
        location = (_clean(loc.group(1)) or None) if loc else None
        dt = re.search(r'class="job-search-card__listdate[^"]*"[^>]*datetime="([^"]+)"', chunk, re.I)
        date = dt.group(1) if dt else None

        results.append(JobCard(
            id=job_id,
            title=title,
            company=company,
            company_url=company_url,
            location=location,
            date=date,
            url=url or f"https://www.linkedin.com/jobs/view/{job_id}",
        ))

    return results


def parse_job_detail(html: str, job_id: str) -> JobDetail:
    """Parse the single-job detail page."""
    title = re.search(
        r'class="(?:top-card-layout__title|topcard__title)[^"]*"[^>]*>([\s\S]*?)</h[12]>', html, re.I
    )
    org = re.search(
        r'class="topcard__org-name-link[^"]*"[^>]*href="([^"]+)"[^>]*>([\s\S]*?)</a>', html, re.I
    )
    company = (_clean(org.group(2)) or None) if org else None
    company_url = _decode_url(org.group(1)) if org else None

    loc = re.search(
        r'class="topcard__flavor topcard__flavor--bullet"[^>]*>([\s\S]*?)</span>', html, re.I
    )
    location = (_clean(loc.group(1)) or None) if loc else None

    # Rich description block; keep paragraph/line breaks as newlines
    description = None
    desc = re.search(
        r'class="(?:show-more-less-html__markup|description__text[^"]*)"[^>]*>([\s\S]*?)</div>', html, re.I
    )
    if desc:
        with_breaks = re.sub(r"<\s*br\s*/?>", "\n", desc.group(1), flags=re.I)
        with_breaks = re.sub(r"</(p|li|ul|ol|div|h\d)>", "\n", with_breaks, flags=re.I)
        text = html_lib.unescape(re.sub(r"<[^>]+>", " ", with_breaks))
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r" ?\n ?", "\n", text)
        description = re.sub(r"\n{3,}", "\n\n", text).strip() or None

    # Job-criteria items: subheader label -> text value
    criteria = {}
    for m in re.finditer(
        r'class="description__job-criteria-subheader"[^>]*>([\s\S]*?)</h3>[\s\S]*?'
        r'class="description__job-criteria-text[^"]*"[^>]*>([\s\S]*?)</span>',
        html, re.I,
    ):
        criteria[_clean(m.group(1)).lower()] = _clean(m.group(2))

    apply_match = re.search(r'class="topcard__link[^"]*"[^>]*href="([^"]+)"', html, re.I)

    return JobDetail(
        id=job_id,
        title=_clean(title.group(1)) if title else "(untitled)",
        company=company,
        company_url=company_url,
        location=location,
        date=None,
        url=f"https://www.linkedin.com/jobs/view/{job_id}",
        description=description,
        seniority=criteria.get("seniority level"),
        employment_type=criteria.get("employment type"),
        job_function=criteria.get("job function"),
        industries=criteria.get("industries"),
        apply_url=_decode_url(apply_match.group(1)) if apply_match else None,
    )


def _jobage_to_tpr(days: Optional[int]) -> Optional[str]:
    """Convert a job-age in days to LinkedIn's f_TPR seconds value."""
    if not days or days <= 0 or days >= 9999:
        return None
    return f"r{days * 86400}"


_WORK_TYPE_FLAGS = {"onsite": "1", "on-site": "1", "remote": "2", "hybrid": "3"}


def build_search_url(
    query: Optional[str] = None,
    location: Optional[str] = None,
    jobage_days: Optional[int] = None,
    remote: Optional[str] = None,
    page: int = 1,
) -> str:
    params = {}
    if query:
        params["keywords"] = query
    if location:
        params["location"] = location
    tpr = _jobage_to_tpr(jobage_days)
    if tpr:
        params["f_TPR"] = tpr
    wt = _WORK_TYPE_FLAGS.get((remote or "").lower())
    if wt:
        params["f_WT"] = wt
    params["start"] = str((page - 1) * 10)
    return f"{SEARCH_URL}?{urlencode(params)}"


def search_jobs(
    query: Optional[str] = None,
    location: Optional[str] = None,
    jobage_days: Optional[int] = None,
    remote: Optional[str] = None,
    page: int = 1,
) -> list[JobCard]:
    return parse_job_cards(html_fetch(build_search_url(query, location, jobage_days, remote, page)))


def fetch_job_detail(job_id: str) -> Optional[JobDetail]:
    html = html_fetch(f"{DETAIL_URL}/{job_id}")
    if not html:
        return None
    return parse_job_detail(html, job_id)
