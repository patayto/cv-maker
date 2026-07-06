"""Unit tests for gap_analyzer.py."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

import gap_analyzer


def _job(skills, fit_score=None, requirements=None):
    return SimpleNamespace(
        role="Role", company="Co", parsed_skills=skills,
        parsed_requirements=requirements or [], fit_score=fit_score,
    )


PROFILE = "Experienced Python developer. Solid PostgreSQL and Docker."


@pytest.mark.unit
def test_hard_gaps_diff_against_profile():
    jobs = [
        _job(["Python", "Kubernetes"], fit_score=80),
        _job(["Kubernetes", "Terraform"], fit_score=40),
    ]
    with patch("gap_analyzer.fit_evaluator.read_profile", return_value=PROFILE), \
         patch("gap_analyzer.llm.get_client", return_value=None):
        result = gap_analyzer.analyze_gaps(jobs)

    skills = {g["skill"]: g for g in result["hard_gaps"]}
    # Python is in the profile -> not a gap
    assert "Python" not in skills
    # Kubernetes: 0.2 (fit 80) + 0.6 (fit 40) = 0.8, in 2 jobs
    assert skills["Kubernetes"]["score"] == pytest.approx(0.8)
    assert skills["Kubernetes"]["job_count"] == 2
    # Terraform only in the low-fit job
    assert skills["Terraform"]["score"] == pytest.approx(0.6)
    # Highest score ranks first and gets Critical priority
    assert result["hard_gaps"][0]["skill"] == "Kubernetes"
    assert result["heatmap"][0]["priority"] == "Critical"


@pytest.mark.unit
def test_unevaluated_jobs_use_default_fit_weight():
    jobs = [_job(["Rust"])]  # no fit evaluation -> weight (100-50)/100
    with patch("gap_analyzer.fit_evaluator.read_profile", return_value=PROFILE), \
         patch("gap_analyzer.llm.get_client", return_value=None):
        result = gap_analyzer.analyze_gaps(jobs)

    assert result["hard_gaps"][0]["score"] == pytest.approx(0.5)


@pytest.mark.unit
def test_empty_profile_raises():
    with patch("gap_analyzer.fit_evaluator.read_profile", return_value=""):
        with pytest.raises(ValueError, match="profile is empty"):
            gap_analyzer.analyze_gaps([_job(["Rust"])])


@pytest.mark.unit
def test_no_parsed_jobs_raises():
    with patch("gap_analyzer.fit_evaluator.read_profile", return_value=PROFILE):
        with pytest.raises(ValueError, match="No tracked jobs"):
            gap_analyzer.analyze_gaps([SimpleNamespace(parsed_skills=None, parsed_requirements=None)])


@pytest.mark.unit
def test_llm_synthesis_appends_entries():
    jobs = [_job(["Kubernetes"], fit_score=50, requirements=["5 years fintech experience"])]
    synth = '[{"priority": "High", "area": "Fintech domain knowledge", "type": "domain", "source": "asked in 1 job"}]'
    with patch("gap_analyzer.fit_evaluator.read_profile", return_value=PROFILE), \
         patch("gap_analyzer.llm.get_client", return_value=object()), \
         patch("gap_analyzer.llm.complete", return_value=synth):
        result = gap_analyzer.analyze_gaps(jobs)

    areas = [e["area"] for e in result["heatmap"]]
    assert "Fintech domain knowledge" in areas
    assert "Kubernetes" in areas
