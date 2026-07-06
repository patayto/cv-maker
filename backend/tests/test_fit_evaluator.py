"""Unit tests for fit_evaluator.py."""

import json
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

import fit_evaluator


def _job(**overrides):
    base = dict(
        role="Backend Engineer", company="TechCorp", location="London",
        workplace_type="Hybrid", experience_level="senior", salary=None,
        parsed_skills=["Python"], parsed_requirements=None,
        parsed_responsibilities=None, notes=None,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


LLM_SCORES = json.dumps({
    "technical_skills": 90,
    "experience_match": 80,
    "behavioral_fit": 60,
    "career_alignment": 70,
    "location_pass": True,
    "key_strengths": ["Python depth"],
    "gaps": ["No Kubernetes"],
})


@pytest.mark.unit
def test_verdict_bands():
    assert fit_evaluator.verdict_for(75) == "Strong Fit"
    assert fit_evaluator.verdict_for(74) == "Good Fit"
    assert fit_evaluator.verdict_for(60) == "Good Fit"
    assert fit_evaluator.verdict_for(45) == "Moderate Fit"
    assert fit_evaluator.verdict_for(30) == "Weak Fit"
    assert fit_evaluator.verdict_for(29) == "Poor Fit"


@pytest.mark.unit
def test_evaluate_fit_weighted_score():
    with patch("fit_evaluator.llm.get_client", return_value=Mock()), \
         patch("fit_evaluator.read_profile", return_value="a profile"), \
         patch("fit_evaluator.llm.complete", return_value=LLM_SCORES):
        result = fit_evaluator.evaluate_fit(_job())

    # 90*.30 + 80*.25 + 60*.15 + 70*.30 = 77
    assert result["overall_score"] == 77
    assert result["verdict"] == "Strong Fit"
    assert result["location_pass"] is True
    assert result["key_strengths"] == ["Python depth"]


@pytest.mark.unit
def test_evaluate_fit_empty_profile():
    with patch("fit_evaluator.llm.get_client", return_value=Mock()), \
         patch("fit_evaluator.read_profile", return_value="  "):
        with pytest.raises(ValueError, match="profile is empty"):
            fit_evaluator.evaluate_fit(_job())


@pytest.mark.unit
def test_evaluate_fit_invalid_scores():
    bad = json.dumps({"technical_skills": "high", "experience_match": 80,
                      "behavioral_fit": 60, "career_alignment": 70})
    with patch("fit_evaluator.llm.get_client", return_value=Mock()), \
         patch("fit_evaluator.read_profile", return_value="a profile"), \
         patch("fit_evaluator.llm.complete", return_value=bad):
        with pytest.raises(ValueError, match="invalid score"):
            fit_evaluator.evaluate_fit(_job())


@pytest.mark.unit
def test_evaluate_fit_no_client():
    with patch("fit_evaluator.llm.get_client", return_value=None):
        with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
            fit_evaluator.evaluate_fit(_job())
