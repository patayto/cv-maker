"""Skill gap analysis across tracked jobs.

Approach adapted from ai-job-search's upskill skill (MIT):
Pass 1 - hard skill diff: frequency map of required skills across all tracked
jobs, each job weighted by (100 - fit_score) / 100 so lower-fit jobs contribute
more to the gap signal; skills already in the candidate profile are dropped.
Pass 2 - LLM synthesis: domain/soft/tooling/credential gaps the keyword diff
misses, combined with pass 1 into a priority heatmap. Degrades to pass 1 only
when no LLM is configured.
"""

import json
import logging
import re
from collections import defaultdict
from typing import Dict, List

import fit_evaluator
import llm
import models

logger = logging.getLogger(__name__)

DEFAULT_FIT = 50  # weight for jobs without a fit evaluation


def _hard_skill_gaps(jobs: List, profile: str) -> List[Dict]:
    profile_lower = profile.lower()
    scores: Dict[str, float] = defaultdict(float)
    counts: Dict[str, int] = defaultdict(int)
    display: Dict[str, str] = {}

    for job in jobs:
        weight = (100 - (job.fit_score if job.fit_score is not None else DEFAULT_FIT)) / 100
        for skill in job.parsed_skills or []:
            key = skill.strip().lower()
            if not key:
                continue
            scores[key] += weight
            counts[key] += 1
            display.setdefault(key, skill.strip())

    gaps = [
        {"skill": display[key], "score": round(score, 2), "job_count": counts[key]}
        for key, score in scores.items()
        # generous diff: substring match counts as "already have it"
        if key not in profile_lower
    ]
    gaps.sort(key=lambda g: g["score"], reverse=True)
    return gaps


def _priority_from_score(score: float, max_score: float) -> str:
    if max_score <= 0:
        return "Low"
    ratio = score / max_score
    if ratio >= 0.75:
        return "Critical"
    if ratio >= 0.5:
        return "High"
    if ratio >= 0.25:
        return "Medium"
    return "Low"


def analyze_gaps(jobs: List) -> Dict:
    """Build the gap heatmap from tracked jobs and the candidate profile."""
    profile = fit_evaluator.read_profile().strip()
    if not profile:
        raise ValueError(
            "Candidate profile is empty. Fill it in first (Profile editor or backend/profile/profile.md)."
        )

    relevant_jobs = [job for job in jobs if job.parsed_skills or job.parsed_requirements]
    if not relevant_jobs:
        raise ValueError("No tracked jobs with parsed skills/requirements yet. Parse some job postings first.")

    hard_gaps = _hard_skill_gaps(relevant_jobs, profile)
    max_score = hard_gaps[0]["score"] if hard_gaps else 0.0

    heatmap = [
        {
            "priority": _priority_from_score(gap["score"], max_score),
            "area": gap["skill"],
            "type": "hard",
            "source": f"{gap['job_count']} job(s), score {gap['score']}",
        }
        for gap in hard_gaps[:20]
    ]

    # Pass 2: LLM synthesis for gaps the keyword diff misses
    client = llm.get_client()
    if client:
        requirements = []
        for job in relevant_jobs:
            for req in job.parsed_requirements or []:
                requirements.append(f"[{job.role} @ {job.company}] {req}")

        prompt = f"""You are analyzing a candidate's skill gaps across the jobs they are tracking.

CANDIDATE PROFILE:
---
{profile[:6000]}
---

REQUIREMENTS ACROSS TRACKED JOBS:
---
{chr(10).join(requirements[:80])}
---

HARD SKILL GAPS ALREADY IDENTIFIED (do not repeat these):
{", ".join(g["skill"] for g in hard_gaps[:20]) or "none"}

Identify up to 6 additional gaps the keyword diff missed: domain knowledge, soft skills,
tooling/process (CI/CD, cloud, ways of working), or credentials repeatedly asked for.
Only include genuine gaps (not covered by the profile). Assign each a priority:
Critical (blocks most tracked jobs), High (recurring), Medium (occasional), Low (nice-to-have).

Respond with ONLY a JSON array:
[{{"priority": "High", "area": "...", "type": "domain|soft|tooling|credential", "source": "one-line reason"}}]"""

        try:
            response = llm.complete(client, prompt)
            match = re.search(r"\[[\s\S]*\]", response)
            if match:
                for entry in json.loads(match.group())[:6]:
                    if isinstance(entry, dict) and entry.get("area"):
                        heatmap.append({
                            "priority": str(entry.get("priority", "Medium")),
                            "area": str(entry["area"]),
                            "type": str(entry.get("type", "domain")),
                            "source": str(entry.get("source", "LLM synthesis")),
                        })
        except Exception as e:
            logger.warning(f"Gap synthesis pass failed, returning hard gaps only: {e}")

    priority_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    heatmap.sort(key=lambda e: priority_order.get(e["priority"], 4))

    return {
        "jobs_analyzed": len(relevant_jobs),
        "hard_gaps": hard_gaps,
        "heatmap": heatmap,
    }
