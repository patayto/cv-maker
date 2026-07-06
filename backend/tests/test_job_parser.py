"""
Unit tests for job_parser.py.

Tests job parsing functionality:
- HTML fetching and parsing
- Basic info extraction
- LLM-based enhancement
- Salary parsing
- Experience level detection
- Skills/requirements/responsibilities extraction
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from job_parser import JobParser


# ==================== INITIALIZATION TESTS ====================

@pytest.mark.unit
@pytest.mark.parser
def test_job_parser_init_with_api_key():
    """Test JobParser initialization with an OpenRouter API key."""
    with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test-key-123'}):
        parser = JobParser()

        assert parser.llm_client is not None


@pytest.mark.unit
@pytest.mark.parser
def test_job_parser_init_without_api_key():
    """Test JobParser initialization without an API key."""
    with patch.dict('os.environ', {}, clear=True):
        parser = JobParser()

        assert parser.llm_client is None


# ==================== SALARY PARSING TESTS ====================

@pytest.mark.unit
@pytest.mark.parser
def test_parse_salary_range_dollars():
    """Test parsing salary range in USD format."""
    parser = JobParser()

    min_sal, max_sal, currency = parser.parse_salary("$80,000 - $120,000")

    assert min_sal == 80000
    assert max_sal == 120000
    assert currency == "USD"


@pytest.mark.unit
@pytest.mark.parser
def test_parse_salary_range_pounds():
    """Test parsing salary range in GBP format."""
    parser = JobParser()

    min_sal, max_sal, currency = parser.parse_salary("£50,000 - £70,000")

    assert min_sal == 50000
    assert max_sal == 70000
    assert currency == "GBP"


@pytest.mark.unit
@pytest.mark.parser
def test_parse_salary_k_notation():
    """Test parsing salary with 'k' notation."""
    parser = JobParser()

    min_sal, max_sal, currency = parser.parse_salary("$80k - $120k")

    assert min_sal == 80000
    assert max_sal == 120000
    assert currency == "USD"


@pytest.mark.unit
@pytest.mark.parser
def test_parse_salary_single_value():
    """Test parsing single salary value."""
    parser = JobParser()

    min_sal, max_sal, currency = parser.parse_salary("£60,000")

    assert min_sal == 60000
    assert max_sal == 60000
    assert currency == "GBP"


@pytest.mark.unit
@pytest.mark.parser
def test_parse_salary_hourly_rate():
    """Test parsing hourly rate (converts to yearly)."""
    parser = JobParser()

    # $50/hour should convert to yearly (50 * 40 * 52 = 104,000)
    min_sal, max_sal, currency = parser.parse_salary("$50 per hour")

    assert min_sal == 104000
    assert max_sal == 104000
    assert currency == "USD"


@pytest.mark.unit
@pytest.mark.parser
def test_parse_salary_euros():
    """Test parsing salary in EUR format."""
    parser = JobParser()

    min_sal, max_sal, currency = parser.parse_salary("€45,000 - €65,000")

    assert min_sal == 45000
    assert max_sal == 65000
    assert currency == "EUR"


@pytest.mark.unit
@pytest.mark.parser
def test_parse_salary_empty_string():
    """Test parsing empty salary string."""
    parser = JobParser()

    min_sal, max_sal, currency = parser.parse_salary("")

    assert min_sal is None
    assert max_sal is None
    assert currency is None


@pytest.mark.unit
@pytest.mark.parser
def test_parse_salary_no_numbers():
    """Test parsing salary string with no numbers."""
    parser = JobParser()

    min_sal, max_sal, currency = parser.parse_salary("Competitive salary")

    assert min_sal is None
    assert max_sal is None
    assert currency is None


# ==================== EXPERIENCE LEVEL DETECTION TESTS ====================

@pytest.mark.unit
@pytest.mark.parser
def test_determine_experience_level_junior():
    """Test detecting junior level from keywords."""
    parser = JobParser()

    text = "We are looking for a junior developer with entry level experience."
    level = parser.determine_experience_level(text)

    assert level == "junior"


@pytest.mark.unit
@pytest.mark.parser
def test_determine_experience_level_mid():
    """Test detecting mid-level from keywords."""
    parser = JobParser()

    text = "Mid-level engineer needed with 3-5 years of experience."
    level = parser.determine_experience_level(text)

    assert level == "mid"


@pytest.mark.unit
@pytest.mark.parser
def test_determine_experience_level_senior():
    """Test detecting senior level from keywords."""
    parser = JobParser()

    text = "Senior Software Engineer position available for experienced developers."
    level = parser.determine_experience_level(text)

    assert level == "senior"


@pytest.mark.unit
@pytest.mark.parser
def test_determine_experience_level_staff():
    """Test detecting staff level from keywords."""
    parser = JobParser()

    text = "Staff Engineer role for technical leaders."
    level = parser.determine_experience_level(text)

    assert level == "staff"


@pytest.mark.unit
@pytest.mark.parser
def test_determine_experience_level_principal():
    """Test detecting principal level from keywords."""
    parser = JobParser()

    text = "Principal Engineer position for distinguished technical leaders."
    level = parser.determine_experience_level(text)

    assert level == "principal"


@pytest.mark.unit
@pytest.mark.parser
def test_determine_experience_level_from_years():
    """Test determining level from years of experience mentioned."""
    parser = JobParser()

    test_cases = [
        ("1-2 years of experience required", "junior"),
        ("3-5 years of experience", "mid"),
        ("7+ years of experience", "senior"),
        ("10+ years of experience", "staff"),
    ]

    for text, expected_level in test_cases:
        level = parser.determine_experience_level(text)
        assert level == expected_level


@pytest.mark.unit
@pytest.mark.parser
def test_determine_experience_level_default():
    """Test default to mid when level is unclear."""
    parser = JobParser()

    text = "Software Engineer position available."
    level = parser.determine_experience_level(text)

    assert level == "mid"


# ==================== BASIC INFO PARSING TESTS ====================

@pytest.mark.unit
@pytest.mark.parser
def test_parse_basic_info_from_html(mock_linkedin_html):
    """Test extracting basic info from HTML."""
    parser = JobParser()
    url = "https://example.com/jobs/123"

    job_data = parser.parse_basic_info(mock_linkedin_html, "Software Engineer at TechCorp", url)

    assert job_data['url'] == url
    assert job_data['role'] == "Software Engineer"
    assert job_data['company'] == "TechCorp"


@pytest.mark.unit
@pytest.mark.parser
def test_parse_basic_info_with_salary():
    """Test extracting salary from text."""
    parser = JobParser()
    html = "<html><body><p>Great job! Salary: $80,000 - $100,000</p></body></html>"
    text = "Great job! Salary: $80,000 - $100,000"

    job_data = parser.parse_basic_info(html, text, "https://example.com/job")

    assert job_data['salary'] == "$80,000 - $100,000"


@pytest.mark.unit
@pytest.mark.parser
def test_parse_basic_info_with_location():
    """Test extracting location from text."""
    parser = JobParser()
    html = "<html><body><p>Location: San Francisco, CA</p></body></html>"
    text = "Location: San Francisco, CA. Great opportunity!"

    job_data = parser.parse_basic_info(html, text, "https://example.com/job")

    assert "San Francisco, CA" in job_data['location']


# ==================== MISSING FIELDS DETECTION TESTS ====================

@pytest.mark.unit
@pytest.mark.parser
def test_get_missing_fields_all_present():
    """Test when all important fields are present."""
    parser = JobParser()

    job_data = {
        'role': 'Software Engineer',
        'company': 'TechCorp',
        'location': 'London, UK'
    }

    missing = parser._get_missing_fields(job_data)

    assert missing == []


@pytest.mark.unit
@pytest.mark.parser
def test_get_missing_fields_some_missing():
    """Test identifying missing fields."""
    parser = JobParser()

    job_data = {
        'role': 'Software Engineer',
        'company': None,
        'location': None
    }

    missing = parser._get_missing_fields(job_data)

    assert 'company' in missing
    assert 'location' in missing
    assert 'role' not in missing


@pytest.mark.unit
@pytest.mark.parser
def test_get_missing_fields_all_missing():
    """Test when all important fields are missing."""
    parser = JobParser()

    job_data = {
        'role': None,
        'company': None,
        'location': None
    }

    missing = parser._get_missing_fields(job_data)

    assert len(missing) == 3
    assert 'role' in missing
    assert 'company' in missing
    assert 'location' in missing


# ==================== EDGE CASES ====================

@pytest.mark.unit
@pytest.mark.parser
def test_parse_salary_weird_formats():
    """Test parsing various edge case salary formats."""
    parser = JobParser()

    test_cases = [
        ("$80,000 to $120,000", 80000, 120000, "USD"),
        ("80k-120k USD", 80000, 120000, "USD"),
        ("GBP 50000-70000", 50000, 70000, "GBP"),
        ("€45k", 45000, 45000, "EUR"),
    ]

    for salary_str, expected_min, expected_max, expected_currency in test_cases:
        min_sal, max_sal, currency = parser.parse_salary(salary_str)
        assert min_sal == expected_min
        assert max_sal == expected_max
        assert currency == expected_currency


@pytest.mark.unit
@pytest.mark.parser
def test_determine_experience_level_mixed_keywords():
    """Test experience level when multiple keywords are present."""
    parser = JobParser()

    # "Senior" appears first, should take precedence
    text = "Senior Software Engineer position, leading junior developers."
    level = parser.determine_experience_level(text)

    assert level == "senior"


# ==================== LLM EXTRACTION TESTS (MOCKED) ====================

LLM_RESPONSE = """{
  "role": "Backend Engineer",
  "company": "LLMCorp",
  "department": null,
  "location": "Remote",
  "salary": "\u00a360,000 - \u00a380,000",
  "notes": "Backend role.",
  "workplace_type": "Remote",
  "employment_type": "Full-time",
  "parsed_skills": [%s],
  "parsed_requirements": ["5+ years backend experience"],
  "parsed_responsibilities": ["Build APIs"]
}""" % ", ".join(f'"Skill{i}"' for i in range(25))


def _parser_with_mock_llm():
    parser = JobParser()
    parser.llm_client = Mock()
    return parser


@pytest.mark.unit
@pytest.mark.parser
def test_extract_with_llm_fills_missing_fields():
    """One structured call fills missing fields and caps list lengths."""
    parser = _parser_with_mock_llm()
    existing = {"url": "https://example.com", "role": None, "company": "ParsedCo"}

    with patch("job_parser.llm.complete", return_value=LLM_RESPONSE):
        result = parser.extract_with_llm("Job description text", existing)

    assert result["role"] == "Backend Engineer"
    # Never overwrites what site-specific parsing already found
    assert result["company"] == "ParsedCo"
    assert result["location"] == "Remote"
    assert result["employment_type"] == "Full-time"
    assert len(result["parsed_skills"]) == 20  # capped
    assert result["parsed_requirements"] == ["5+ years backend experience"]


@pytest.mark.unit
@pytest.mark.parser
def test_extract_with_llm_invalid_json():
    """Malformed LLM output leaves job_data unchanged."""
    parser = _parser_with_mock_llm()
    existing = {"url": "https://example.com", "role": None}

    with patch("job_parser.llm.complete", return_value="not json at all"):
        result = parser.extract_with_llm("text", existing)

    assert result == existing


@pytest.mark.unit
@pytest.mark.parser
def test_extract_with_llm_api_error():
    """LLM errors leave job_data unchanged."""
    parser = _parser_with_mock_llm()
    existing = {"url": "https://example.com", "role": None}

    with patch("job_parser.llm.complete", side_effect=RuntimeError("rate limited")):
        result = parser.extract_with_llm("text", existing)

    assert result == existing


@pytest.mark.unit
@pytest.mark.parser
def test_extract_with_llm_without_client():
    """No API key configured means job_data passes through untouched."""
    with patch.dict('os.environ', {}, clear=True):
        parser = JobParser()
    existing = {"url": "https://example.com", "role": None}

    assert parser.extract_with_llm("text", existing) == existing


@pytest.mark.unit
@pytest.mark.parser
def test_extract_with_llm_truncates_long_text():
    """Very long postings are truncated before hitting the LLM."""
    parser = _parser_with_mock_llm()

    with patch("job_parser.llm.complete", return_value="{}") as mock_complete:
        parser.extract_with_llm("x" * 20000, {"url": "u"})

    prompt = mock_complete.call_args[0][1]
    assert "(truncated)" in prompt
    assert len(prompt) < 15000
