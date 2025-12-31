"""
CV Generator Module

Generates tailored CVs from lego blocks matched to job requirements.
Uses Claude AI for intelligent block selection when API key is available.
"""

import os
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from anthropic import Anthropic
import json

try:
    from models import Job, LegoBlock, GeneratedCV
except ImportError:
    # Allow import when models aren't available yet
    pass


class CVGenerator:
    """Generate tailored CVs from lego blocks matched to job requirements"""

    def __init__(self):
        self.anthropic_client = None
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            self.anthropic_client = Anthropic(api_key=api_key)

    def select_blocks(self, job_id: int, db: Session, max_blocks: int = 6) -> List:
        """
        Select most relevant lego blocks for a job based on parsed requirements.

        Args:
            job_id: ID of the job to generate CV for
            db: Database session
            max_blocks: Maximum number of blocks to select

        Returns:
            List of selected LegoBlock objects
        """
        # Get job details
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job with ID {job_id} not found")

        # Get all available lego blocks
        all_blocks = db.query(LegoBlock).all()
        if not all_blocks:
            return []

        # Use LLM if available, otherwise use keyword matching
        if self.anthropic_client:
            return self._select_blocks_with_llm(job, all_blocks, max_blocks)
        else:
            return self._select_blocks_fallback(job, all_blocks, max_blocks)

    def _select_blocks_with_llm(self, job, all_blocks: List, max_blocks: int) -> List:
        """Select blocks using Claude AI based on job requirements"""
        # Prepare job context
        job_context = {
            "role": job.role,
            "company": job.company,
            "skills": job.parsed_skills or [],
            "requirements": job.parsed_requirements or [],
            "responsibilities": job.parsed_responsibilities or [],
            "experience_level": job.experience_level,
        }

        # Prepare blocks for LLM
        blocks_data = [
            {
                "id": block.id,
                "title": block.title,
                "category": block.category,
                "content": block.content[:200],  # Truncate for token efficiency
                "skills": block.skills or [],
                "keywords": block.keywords or [],
            }
            for block in all_blocks
        ]

        prompt = f"""You are a CV optimization expert. Given a job posting and a library of CV achievement statements (lego blocks), select the {max_blocks} most relevant blocks that best demonstrate the candidate's fit for the role.

Job Context:
{json.dumps(job_context, indent=2)}

Available CV Blocks:
{json.dumps(blocks_data, indent=2)}

Select the {max_blocks} most relevant block IDs that:
1. Match the required skills and technologies
2. Demonstrate relevant experience level
3. Show achievements related to the job responsibilities
4. Provide diverse evidence across different competency areas

Respond with ONLY a JSON array of block IDs, e.g.: [1, 5, 8, 12, 15, 20]"""

        try:
            message = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse response to get block IDs
            response_text = message.content[0].text.strip()
            # Extract JSON array from response
            if "[" in response_text:
                json_str = response_text[response_text.find("["):response_text.rfind("]")+1]
                selected_ids = json.loads(json_str)
            else:
                # Fallback if no JSON found
                return self._select_blocks_fallback(job, all_blocks, max_blocks)

            # Get selected blocks
            selected_blocks = [block for block in all_blocks if block.id in selected_ids]
            return selected_blocks[:max_blocks]

        except Exception as e:
            print(f"LLM selection failed: {e}, falling back to keyword matching")
            return self._select_blocks_fallback(job, all_blocks, max_blocks)

    def _select_blocks_fallback(self, job, all_blocks: List, max_blocks: int) -> List:
        """Fallback block selection using simple keyword matching"""
        # Collect all relevant keywords from job
        job_keywords = set()
        if job.parsed_skills:
            job_keywords.update([s.lower() for s in job.parsed_skills])
        if job.parsed_requirements:
            job_keywords.update([r.lower() for r in job.parsed_requirements])
        if job.role:
            job_keywords.update(job.role.lower().split())

        # Score each block
        scored_blocks = []
        for block in all_blocks:
            score = 0
            block_text = f"{block.title} {block.content}".lower()

            # Check skill matches
            if block.skills:
                for skill in block.skills:
                    if skill.lower() in job_keywords:
                        score += 3

            # Check keyword matches
            if block.keywords:
                for keyword in block.keywords:
                    if keyword.lower() in job_keywords:
                        score += 2

            # Check content matches
            for keyword in job_keywords:
                if keyword in block_text:
                    score += 1

            if score > 0:
                scored_blocks.append((score, block))

        # Sort by score and return top blocks
        scored_blocks.sort(reverse=True, key=lambda x: x[0])
        return [block for score, block in scored_blocks[:max_blocks]]

    def rank_blocks(self, job_id: int, db: Session) -> List[Tuple[int, float]]:
        """
        Rank all available blocks by relevance to a job.

        Returns:
            List of tuples: (block_id, relevance_score)
        """
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job with ID {job_id} not found")

        all_blocks = db.query(LegoBlock).all()
        if not all_blocks:
            return []

        # Use fallback scoring method
        job_keywords = set()
        if job.parsed_skills:
            job_keywords.update([s.lower() for s in job.parsed_skills])
        if job.parsed_requirements:
            job_keywords.update([r.lower() for r in job.parsed_requirements])

        ranked = []
        for block in all_blocks:
            score = 0.0
            block_text = f"{block.title} {block.content}".lower()

            if block.skills:
                for skill in block.skills:
                    if skill.lower() in job_keywords:
                        score += 3.0

            if block.keywords:
                for keyword in block.keywords:
                    if keyword.lower() in job_keywords:
                        score += 2.0

            for keyword in job_keywords:
                if keyword in block_text:
                    score += 1.0

            # Normalize score to 0-100 scale
            normalized_score = min(100.0, score * 10)
            ranked.append((block.id, normalized_score))

        # Sort by score descending
        ranked.sort(reverse=True, key=lambda x: x[1])
        return ranked

    def customize_block(self, block, job_context: str) -> str:
        """
        Customize a lego block's content for a specific job context.

        Args:
            block: LegoBlock object
            job_context: String describing the job (role, company, requirements)

        Returns:
            Customized block content
        """
        if not self.anthropic_client:
            # No API key, return original content
            return block.content

        prompt = f"""Tailor this CV achievement statement for the following job context.
Keep the same core achievement but adjust language and emphasis to better fit the role.
Maintain the same length and format.

Job Context: {job_context}

Original Statement:
{block.content}

Provide ONLY the tailored version, no explanation."""

        try:
            message = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text.strip()
        except Exception as e:
            print(f"Block customization failed: {e}")
            return block.content

    def generate_latex(self, blocks: List, template: str = "default") -> str:
        """
        Generate LaTeX document from selected lego blocks.

        Args:
            blocks: List of LegoBlock objects
            template: Template name (currently only "default" supported)

        Returns:
            LaTeX document string
        """
        # Simple LaTeX template
        latex = r"""\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[margin=1in]{geometry}
\usepackage{enumitem}
\usepackage{hyperref}

\begin{document}

\section*{Professional Experience}

"""
        # Group blocks by category
        categories = {}
        for block in blocks:
            cat = block.category or "General"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(block)

        # Add blocks by category
        for category, cat_blocks in categories.items():
            latex += f"\\subsection*{{{self._escape_latex(category)}}}\n\n"
            latex += "\\begin{itemize}[leftmargin=*]\n"
            for block in cat_blocks:
                # Escape LaTeX special characters
                content = self._escape_latex(block.content)
                latex += f"  \\item {content}\n"
            latex += "\\end{itemize}\n\n"

        latex += r"\end{document}"
        return latex

    def _escape_latex(self, text: str) -> str:
        """Escape special LaTeX characters"""
        replacements = {
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '^': r'\textasciicircum{}',
            '\\': r'\textbackslash{}',
        }
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        return text


# Create singleton instance
cv_generator = CVGenerator()
