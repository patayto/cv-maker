"""Unit tests for the LinkedIn jobs-guest client (linkedin_guest.py)."""

import pytest

import linkedin_guest as lg

SEARCH_HTML = """
<li>
  <div class="base-card" data-entity-urn="urn:li:jobPosting:4425875965">
    <a class="base-card__full-link" href="https://uk.linkedin.com/jobs/view/python-software-engineer-at-abound-4425875965?position=1&amp;pageNum=0">
      <span class="sr-only">Python Software Engineer</span>
    </a>
    <div class="base-search-card__info">
      <h3 class="base-search-card__title"> Python Software Engineer </h3>
      <h4 class="base-search-card__subtitle">
        <a href="https://uk.linkedin.com/company/getabound?trk=public_jobs">Abound</a>
      </h4>
      <div class="base-search-card__metadata">
        <span class="job-search-card__location">London, England, United Kingdom</span>
        <time class="job-search-card__listdate" datetime="2026-07-01">3 days ago</time>
      </div>
    </div>
  </div>
</li>
<li>
  <div class="base-card" data-entity-urn="urn:li:jobPosting:1111111111">
    <span class="sr-only">Broken card without title h3</span>
  </div>
</li>
"""

DETAIL_HTML = """
<div class="top-card-layout__entity-info">
  <h1 class="top-card-layout__title">Python Software Engineer</h1>
  <a class="topcard__org-name-link" href="https://uk.linkedin.com/company/getabound?trk=x">Abound</a>
  <span class="topcard__flavor topcard__flavor--bullet">London, England, United Kingdom</span>
</div>
<a class="topcard__link" href="https://example.com/apply?ref=li">Apply</a>
<div class="show-more-less-html__markup">
  <p>About the role.</p>
  <ul><li>Build APIs</li><li>Ship &amp; iterate</li></ul>
</div>
<ul class="description__job-criteria-list">
  <li><h3 class="description__job-criteria-subheader"> Seniority level </h3>
      <span class="description__job-criteria-text"> Mid-Senior level </span></li>
  <li><h3 class="description__job-criteria-subheader"> Employment type </h3>
      <span class="description__job-criteria-text"> Full-time </span></li>
</ul>
"""


@pytest.mark.unit
def test_parse_job_cards():
    cards = lg.parse_job_cards(SEARCH_HTML)

    # Second card has no h3 title, but the sr-only fallback still yields one
    assert len(cards) == 2
    assert cards[1].title == "Broken card without title h3"
    card = cards[0]
    assert card.id == "4425875965"
    assert card.title == "Python Software Engineer"
    assert card.company == "Abound"
    assert card.company_url == "https://uk.linkedin.com/company/getabound"
    assert card.location == "London, England, United Kingdom"
    assert card.date == "2026-07-01"
    assert card.url == "https://uk.linkedin.com/jobs/view/python-software-engineer-at-abound-4425875965"


def test_parse_job_cards_empty():
    assert lg.parse_job_cards("") == []
    assert lg.parse_job_cards("<html><body>No jobs</body></html>") == []


@pytest.mark.unit
def test_parse_job_detail():
    detail = lg.parse_job_detail(DETAIL_HTML, "4425875965")

    assert detail.title == "Python Software Engineer"
    assert detail.company == "Abound"
    assert detail.location == "London, England, United Kingdom"
    assert detail.seniority == "Mid-Senior level"
    assert detail.employment_type == "Full-time"
    assert detail.apply_url == "https://example.com/apply"
    assert "About the role." in detail.description
    assert "Ship & iterate" in detail.description
    assert detail.url == "https://www.linkedin.com/jobs/view/4425875965"


@pytest.mark.unit
def test_id_from_url():
    assert lg.id_from_url("https://www.linkedin.com/jobs/view/python-dev-at-x-4425875965?a=1") == "4425875965"
    assert lg.id_from_url("https://www.linkedin.com/jobs/view/4425875965") == "4425875965"
    assert lg.id_from_url("https://www.linkedin.com/jobs/") is None


@pytest.mark.unit
def test_build_search_url():
    url = lg.build_search_url(
        query="python developer", location="London, United Kingdom",
        jobage_days=7, remote="remote", page=2,
    )
    assert url.startswith(lg.SEARCH_URL)
    assert "keywords=python+developer" in url
    assert "location=London%2C+United+Kingdom" in url
    assert "f_TPR=r604800" in url
    assert "f_WT=2" in url
    assert "start=10" in url
