"""Job fit evaluation - scores a job against the candidate profile.

Rubric adapted from ai-job-search (04-job-evaluation.md, MIT):
4 scored dimensions (0-100) with weights, plus location pass/fail.
The LLM scores the dimensions; the weighted overall score and verdict
are computed here so they stay deterministic.
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict

import llm

logger = logging.getLogger(__name__)

PROFILE_PATH = Path(__file__).parent / "profile" / "profile.md"

WEIGHTS = {
    "technical_skills": 0.30,
    "experience_match": 0.25,
    "behavioral_fit": 0.15,
    "career_alignment": 0.30,
}

VERDICT_BANDS = [
    (75, "Strong Fit"),
    (60, "Good Fit"),
    (45, "Moderate Fit"),
    (30, "Weak Fit"),
    (0, "Poor Fit"),
]


def read_profile() -> str:
    if PROFILE_PATH.exists():
        return PROFILE_PATH.read_text(encoding="utf-8")
    return ""


def write_profile(content: str) -> None:
    PROFILE_PATH.parent.mkdir(exist_ok=True)
    PROFILE_PATH.write_text(content, encoding="utf-8")


def verdict_for(score: int) -> str:
    for threshold, verdict in VERDICT_BANDS:
        if score >= threshold:
            return verdict
    return "Poor Fit"


def _format_job(job) -> str:
    parts = [
        f"Role: {job.role}",
        f"Company: {job.company}",
        f"Location: {job.location or 'unknown'}",
        f"Workplace type: {job.workplace_type or 'unknown'}",
        f"Experience level: {job.experience_level or 'unknown'}",
        f"Salary: {job.salary or 'not stated'}",
    ]
    if job.parsed_skills:
        parts.append(f"Required skills: {', '.join(job.parsed_skills)}")
    if job.parsed_requirements:
        parts.append("Requirements:\n- " + "\n- ".join(job.parsed_requirements))
    if job.parsed_responsibilities:
        parts.append("Responsibilities:\n- " + "\n- ".join(job.parsed_responsibilities))
    if job.notes:
        parts.append(f"Notes: {job.notes}")
    return "\n".join(parts)


def evaluate_fit(job) -> Dict:
    """Score the job against the candidate profile. Raises on failure."""
    client = llm.get_client()
    if not client:
        raise RuntimeError("OPENROUTER_API_KEY not configured - fit evaluation needs the LLM")

    profile = read_profile().strip()
    if not profile:
        raise ValueError(
            "Candidate profile is empty. Fill it in first (Profile editor or backend/profile/profile.md)."
        )

    prompt = f"""You are a career advisor scoring how well a candidate fits a job posting.

CANDIDATE PROFILE:
---
{profile}
---

JOB POSTING:
---
{_format_job(job)}
---

Score each dimension 0-100 using this rubric:
- technical_skills: 80-100 core requirements are the candidate's primary skills; 60-79 most match with 1-2 learnable gaps; 40-59 partial match needing significant upskilling; 0-39 fundamental mismatch.
- experience_match: 80-100 direct experience in same domain and role type; 60-79 related experience with clear transferable skills; 40-59 adjacent experience where a case must be made; 0-39 unrelated.
- behavioral_fit: how well the role and likely culture match the candidate's stated working preferences (60-79 if mixed signals, be conservative when the posting says little).
- career_alignment: 80-100 strongly aligned with the candidate's stated career direction with a clear growth path; 40-59 decent job that doesn't build toward their goals; 0-39 dead end or backwards step.
- location_pass: false only if the job clearly requires relocation or on-site presence incompatible with the candidate's stated location constraints; true otherwise.

Base every score on evidence from the profile. Do not invent skills or preferences.

Respond with ONLY a valid JSON object (no explanation, no markdown fences):
{{
  "technical_skills": 0,
  "experience_match": 0,
  "behavioral_fit": 0,
  "career_alignment": 0,
  "location_pass": true,
  "key_strengths": ["2-4 specific strengths for this role, grounded in the profile"],
  "gaps": ["2-4 specific gaps to address, grounded in the posting"]
}}"""

    response_text = llm.complete(client, prompt)
    json_match = re.search(r"\{[\s\S]*\}", response_text)
    if not json_match:
        raise ValueError(f"LLM returned no JSON: {response_text[:200]}")
    scores = json.loads(json_match.group())

    result = {}
    for dim in WEIGHTS:
        value = scores.get(dim)
        if not isinstance(value, (int, float)) or not 0 <= value <= 100:
            raise ValueError(f"LLM returned invalid score for {dim}: {value!r}")
        result[dim] = int(value)

    result["location_pass"] = bool(scores.get("location_pass", True))
    result["overall_score"] = round(sum(result[dim] * w for dim, w in WEIGHTS.items()))
    result["verdict"] = verdict_for(result["overall_score"])
    result["key_strengths"] = [str(s) for s in scores.get("key_strengths", [])][:6]
    result["gaps"] = [str(g) for g in scores.get("gaps", [])][:6]
    return result
