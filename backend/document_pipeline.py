"""CV / cover letter generation pipeline: draft -> review -> compile -> verify.

Single-process adaptation of ai-job-search's drafter-reviewer workflow (MIT):
1. Draft the full LaTeX document from the candidate profile + job + CV blocks.
2. Review pass: a second LLM call critiques and returns a revised document.
3. Compile (lualatex for CVs, xelatex for letters) and check the page count;
   on a compile error or wrong length, retry with targeted instructions
   (relevance-weighted cutting rather than chopping the oldest section).
"""

import logging
import re
import time
from pathlib import Path
from typing import Dict, List, Optional

import fit_evaluator
import latex_service
import llm

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"

MAX_FIX_ATTEMPTS = 2

STYLE_RULES = """Writing rules (non-negotiable):
- Never fabricate skills, experience, or achievements. Every claim must trace to the candidate profile or the provided CV blocks.
- No cliches ("passionate about", "leverage", "synergies", "hit the ground running").
- No apologetic language; state what the candidate brings and the evidence.
- First person, active voice. Demonstrate, don't assert."""

CUTTING_RULES = """When cutting content to fit, score each line by (a) relevance to this
posting's keywords and responsibilities, (b) uniqueness (is the claim made elsewhere?).
Cut the lowest-scoring lines first, regardless of section - do NOT mechanically drop the
oldest role. Prefer cutting duplicated claims and generic filler before unique, relevant evidence."""


def _extract_tex(response: str) -> str:
    """Pull the LaTeX document out of an LLM response (may be fenced or chatty)."""
    match = re.search(r"\\documentclass[\s\S]*\\end\{document\}", response)
    if not match:
        raise ValueError("LLM response contained no complete LaTeX document")
    return match.group(0)


def _job_context(job, blocks: Optional[List] = None) -> str:
    parts = [
        f"Role: {job.role}",
        f"Company: {job.company}",
        f"Location: {job.location or 'unknown'}",
    ]
    if job.parsed_skills:
        parts.append(f"Required skills: {', '.join(job.parsed_skills)}")
    if job.parsed_requirements:
        parts.append("Requirements:\n- " + "\n- ".join(job.parsed_requirements))
    if job.parsed_responsibilities:
        parts.append("Responsibilities:\n- " + "\n- ".join(job.parsed_responsibilities))
    if blocks:
        parts.append(
            "Most relevant CV achievement blocks (use these as evidence):\n- "
            + "\n- ".join(block.content for block in blocks)
        )
    return "\n".join(parts)


def _profile_or_raise() -> str:
    profile = fit_evaluator.read_profile().strip()
    if not profile:
        raise ValueError(
            "Candidate profile is empty. Fill it in first (Profile editor or backend/profile/profile.md)."
        )
    return profile


def _draft_review_compile(
    client, draft_prompt: str, context: str, stem: str, engine: str, expected_pages: int
) -> Dict:
    tex = _extract_tex(llm.complete(client, draft_prompt))

    # Review pass: fresh critique of the draft against the job context
    review_prompt = f"""You are reviewing a LaTeX application document before it is sent.

JOB CONTEXT AND CANDIDATE MATERIAL:
---
{context}
---

DRAFT DOCUMENT:
---
{tex}
---

Critique the draft for: missed keywords from the job context, generic or passive phrasing,
claims not supported by the candidate material (remove them), and inconsistent tone.
{STYLE_RULES}

Then produce the improved document. Respond with ONLY the complete revised LaTeX document,
starting at \\documentclass and ending at \\end{{document}}. Do not change the document class
or font setup."""
    try:
        tex = _extract_tex(llm.complete(client, review_prompt))
    except (ValueError, RuntimeError) as e:
        logger.warning(f"Review pass failed, keeping first draft: {e}")

    checks: Dict[str, bool] = {}
    pages = None
    tex_path = pdf_path = None
    for attempt in range(MAX_FIX_ATTEMPTS + 1):
        try:
            tex_path, pdf_path, pages = latex_service.compile_tex(tex, stem, engine)
        except latex_service.LatexCompileError as e:
            if attempt == MAX_FIX_ATTEMPTS:
                raise
            fix_prompt = f"""This LaTeX document fails to compile with {engine}. Fix the error and respond with
ONLY the corrected complete LaTeX document.

ERROR LOG (end):
---
{e.log_excerpt}
---

DOCUMENT:
---
{tex}
---"""
            tex = _extract_tex(llm.complete(client, fix_prompt))
            continue

        if pages == expected_pages or attempt == MAX_FIX_ATTEMPTS:
            break

        direction = "shorten" if pages > expected_pages else "expand"
        length_prompt = f"""This document compiled to {pages} page(s) but must be exactly {expected_pages} page(s).
{direction.capitalize()} it accordingly and respond with ONLY the complete revised LaTeX document.

{CUTTING_RULES if direction == "shorten" else "Expand with additional relevant, profile-supported detail - never fabricate."}

JOB CONTEXT AND CANDIDATE MATERIAL:
---
{context}
---

DOCUMENT:
---
{tex}
---"""
        tex = _extract_tex(llm.complete(client, length_prompt))

    checks["compiled"] = pdf_path is not None
    checks["page_count_ok"] = pages == expected_pages
    return {
        "latex": tex,
        "tex_path": tex_path,
        "pdf_path": pdf_path,
        "page_count": pages,
        "checks": checks,
    }


def generate_cv(job, blocks: List) -> Dict:
    """Generate, review, and compile a 2-page moderncv CV. Raises on failure."""
    client = llm.get_client()
    if not client:
        raise RuntimeError("OPENROUTER_API_KEY not configured - document generation needs the LLM")
    profile = _profile_or_raise()
    template = (TEMPLATES_DIR / "cv_example.tex").read_text(encoding="utf-8")
    context = f"CANDIDATE PROFILE:\n{profile}\n\nJOB POSTING:\n{_job_context(job, blocks)}"

    draft_prompt = f"""Write a complete, tailored 2-page CV in LaTeX for this candidate and job.

{context}

TEMPLATE (follow this structure and preamble exactly, replacing placeholder content;
compiles with lualatex):
---
{template}
---

Tailoring rules:
- Profile statement (3-4 lines) written for this specific role, not generic.
- Reframe experience bullets to hit the posting's keywords and responsibilities.
- Work the provided CV achievement blocks into the relevant roles.
- Page budget for exactly 2 pages: most recent role 4-5 bullets, previous role 2-3, older roles 2 one-liners.
{STYLE_RULES}

Respond with ONLY the complete LaTeX document."""

    stem = f"cv_{re.sub(r'[^A-Za-z0-9]+', '_', job.company or 'job')}_{job.id}_{int(time.time())}"
    return _draft_review_compile(client, draft_prompt, context, stem, "lualatex", expected_pages=2)


def generate_cover_letter(job, blocks: List) -> Dict:
    """Generate, review, and compile a 1-page cover.cls letter. Raises on failure."""
    client = llm.get_client()
    if not client:
        raise RuntimeError("OPENROUTER_API_KEY not configured - document generation needs the LLM")
    profile = _profile_or_raise()
    template = (TEMPLATES_DIR / "cover_example.tex").read_text(encoding="utf-8")
    context = f"CANDIDATE PROFILE:\n{profile}\n\nJOB POSTING:\n{_job_context(job, blocks)}"

    draft_prompt = f"""Write a complete, tailored 1-page cover letter in LaTeX for this candidate and job.

{context}

TEMPLATE (follow this structure and preamble exactly, replacing placeholder content;
compiles with xelatex; note the itemize handling warning in the comments):
---
{template}
---

Letter rules:
- Forward-looking: lead with what the candidate will solve for this employer, not a CV recap.
- 1-2 brief past examples only, as evidence for future claims.
- Address the named contact if one appears in the job context, else "Dear Hiring Manager,".
- Must fit one page: 4-6 \\lettercontent paragraphs plus at most one short bullet list.
{STYLE_RULES}

Respond with ONLY the complete LaTeX document."""

    stem = f"cover_{re.sub(r'[^A-Za-z0-9]+', '_', job.company or 'job')}_{job.id}_{int(time.time())}"
    return _draft_review_compile(client, draft_prompt, context, stem, "xelatex", expected_pages=1)
