"""
Lego Blocks Matcher - Uses an LLM (OpenRouter) to match job requirements to relevant CV blocks
"""

import json
import logging
import os
from typing import Dict, List, Optional

from dotenv import load_dotenv

import llm

from lego_blocks_parser import LegoBlock, get_parser

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class BlockMatch:
    """Represents a matched block with relevance score and reasoning"""

    def __init__(self, block: LegoBlock, relevance_score: int, match_reason: str):
        """
        Args:
            block: The matched LegoBlock
            relevance_score: Score from 1-10 indicating relevance
            match_reason: Why this block was selected
        """
        self.block = block
        self.relevance_score = relevance_score
        self.match_reason = match_reason

    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            'block_id': self.block.id,
            'block_text': self.block.text,
            'company': self.block.company,
            'strength': self.block.strength,
            'relevance_score': self.relevance_score,
            'match_reason': self.match_reason
        }


class LegoBlocksMatcher:
    """Matches job requirements to relevant CV blocks using an LLM"""

    def __init__(self):
        """Initialize matcher with LLM client and lego blocks parser"""
        self.parser = get_parser()
        self.llm_client = llm.get_client()
        if self.llm_client:
            logger.info("LLM client initialized for block matching")
        else:
            logger.warning("No OPENROUTER_API_KEY found. AI matching disabled.")

    def match_blocks_for_job(
        self,
        job_title: str,
        company: str,
        skills: Optional[List[str]] = None,
        requirements: Optional[List[str]] = None,
        responsibilities: Optional[List[str]] = None,
        max_blocks: int = 10
    ) -> List[BlockMatch]:
        """
        Find and rank the most relevant CV blocks for a job posting

        Args:
            job_title: Job title/role
            company: Company name
            skills: List of required skills
            requirements: List of job requirements
            responsibilities: List of job responsibilities
            max_blocks: Maximum number of blocks to return

        Returns:
            List of BlockMatch objects, ranked by relevance
        """
        if not self.llm_client:
            # Fallback: return essential blocks without AI
            logger.warning("AI matching unavailable. Returning essential blocks.")
            return self._get_default_blocks(max_blocks)

        # Get candidate blocks (exclude 'omit' and 'weak')
        all_blocks = self.parser.parse()
        candidate_blocks = [
            block for block in all_blocks
            if block.strength in ['essential', 'strong', 'good']
        ]

        # Build prompt for the LLM
        prompt = self._build_matching_prompt(
            job_title=job_title,
            company=company,
            skills=skills or [],
            requirements=requirements or [],
            responsibilities=responsibilities or [],
            blocks=candidate_blocks,
            max_blocks=max_blocks
        )

        try:
            logger.info(f"Requesting block matches from LLM for: {job_title} at {company}")

            response_text = llm.complete(self.llm_client, prompt).strip()

            # Parse JSON response
            matches = self._parse_llm_response(response_text, candidate_blocks)

            logger.info(f"LLM matched {len(matches)} blocks for job")
            return matches

        except Exception as e:
            logger.error(f"Error matching blocks with LLM: {e}")
            # Fallback to default blocks
            return self._get_default_blocks(max_blocks)

    def _build_matching_prompt(
        self,
        job_title: str,
        company: str,
        skills: List[str],
        requirements: List[str],
        responsibilities: List[str],
        blocks: List[LegoBlock],
        max_blocks: int
    ) -> str:
        """Build the prompt for the LLM to match blocks"""

        # Format blocks for the prompt
        blocks_text = ""
        for i, block in enumerate(blocks, 1):
            blocks_text += f"\n{i}. ID: {block.id}\n"
            blocks_text += f"   Strength: {block.strength}\n"
            blocks_text += f"   Company: {block.company}\n"
            blocks_text += f"   Text: {block.text}\n"

        prompt = f"""You are a CV optimization expert. Your task is to select the most relevant CV bullet points (experience blocks) for a specific job application.

JOB DETAILS:
- Role: {job_title}
- Company: {company}

REQUIRED SKILLS:
{chr(10).join(f"- {skill}" for skill in skills) if skills else "- Not specified"}

JOB REQUIREMENTS:
{chr(10).join(f"- {req}" for req in requirements) if requirements else "- Not specified"}

JOB RESPONSIBILITIES:
{chr(10).join(f"- {resp}" for resp in responsibilities) if responsibilities else "- Not specified"}

AVAILABLE CV BLOCKS:
{blocks_text}

TASK:
Select the top {max_blocks} most relevant CV blocks for this job. For each selected block:
1. Consider how well it demonstrates the required skills
2. Consider how well it matches the job requirements
3. Consider how well it aligns with the responsibilities
4. Give preference to 'essential' strength blocks, then 'strong', then 'good'
5. Score each block from 1-10 for relevance (10 = perfect match)
6. Explain why you selected it

IMPORTANT:
- Focus on technical skills match, leadership experience, and scale of impact
- Prioritize blocks that show similar technologies, systems, or business domains
- Include blocks that demonstrate the level of seniority required
- Ensure variety - don't just pick similar blocks

OUTPUT FORMAT (JSON only, no other text):
{{
  "matches": [
    {{
      "block_id": "ads-essential-1",
      "relevance_score": 9,
      "match_reason": "Shows full-stack ML system architecture experience which directly aligns with the role's requirement for..."
    }}
  ]
}}

Return ONLY valid JSON, no markdown formatting, no other text."""

        return prompt

    def _parse_llm_response(
        self,
        response_text: str,
        candidate_blocks: List[LegoBlock]
    ) -> List[BlockMatch]:
        """
        Parse the LLM JSON response into BlockMatch objects

        Args:
            response_text: Raw response from the LLM
            candidate_blocks: List of candidate blocks to match against

        Returns:
            List of BlockMatch objects
        """
        # Extract JSON from response (handle markdown code blocks)
        json_text = response_text.strip()

        # Remove markdown code fences if present
        if json_text.startswith('```'):
            lines = json_text.split('\n')
            # Remove first and last line (code fences)
            json_text = '\n'.join(lines[1:-1])

        # Remove 'json' language identifier if present
        json_text = json_text.replace('```json', '').replace('```', '').strip()

        # Parse JSON
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response text: {response_text}")
            raise ValueError("Invalid JSON response from the LLM")

        # Create BlockMatch objects
        matches = []
        blocks_by_id = {block.id: block for block in candidate_blocks}

        for match_data in data.get('matches', []):
            block_id = match_data.get('block_id')
            relevance_score = match_data.get('relevance_score', 5)
            match_reason = match_data.get('match_reason', 'No reason provided')

            # Find the block
            block = blocks_by_id.get(block_id)
            if block:
                match = BlockMatch(
                    block=block,
                    relevance_score=relevance_score,
                    match_reason=match_reason
                )
                matches.append(match)
            else:
                logger.warning(f"Block ID '{block_id}' not found in candidates")

        # Sort by relevance score (descending)
        matches.sort(key=lambda m: m.relevance_score, reverse=True)

        return matches

    def _get_default_blocks(self, max_blocks: int) -> List[BlockMatch]:
        """
        Fallback: Return essential + strong blocks when AI is unavailable

        Args:
            max_blocks: Maximum number of blocks to return

        Returns:
            List of BlockMatch objects
        """
        recommended = self.parser.get_recommended_blocks()

        # Create BlockMatch objects with default scores
        matches = []
        for block in recommended[:max_blocks]:
            score = 9 if block.strength == 'essential' else 7
            matches.append(BlockMatch(
                block=block,
                relevance_score=score,
                match_reason="Recommended block (AI matching unavailable)"
            ))

        return matches


# Global singleton instance
_matcher_instance: Optional[LegoBlocksMatcher] = None


def get_matcher() -> LegoBlocksMatcher:
    """Get or create the global matcher instance"""
    global _matcher_instance
    if _matcher_instance is None:
        _matcher_instance = LegoBlocksMatcher()
    return _matcher_instance


if __name__ == "__main__":
    # Test the matcher
    logging.basicConfig(level=logging.INFO)

    matcher = LegoBlocksMatcher()

    # Test job
    test_job = {
        "title": "Senior Software Engineer - ML Systems",
        "company": "Tech Startup",
        "skills": ["Python", "AWS", "Machine Learning", "Spark", "MLOps"],
        "requirements": [
            "5+ years of experience building production ML systems",
            "Strong experience with distributed data processing",
            "Experience with cloud infrastructure (AWS/GCP)",
            "Leadership experience mentoring junior engineers"
        ],
        "responsibilities": [
            "Design and build ML infrastructure for product recommendations",
            "Lead technical design across multiple teams",
            "Mentor junior engineers and set engineering standards"
        ]
    }

    print("\n🎯 Testing Block Matching\n")
    print(f"Job: {test_job['title']} at {test_job['company']}\n")

    matches = matcher.match_blocks_for_job(
        job_title=test_job['title'],
        company=test_job['company'],
        skills=test_job['skills'],
        requirements=test_job['requirements'],
        responsibilities=test_job['responsibilities'],
        max_blocks=8
    )

    print(f"✅ Found {len(matches)} matching blocks:\n")

    for i, match in enumerate(matches, 1):
        print(f"{i}. {match.block.id} (Score: {match.relevance_score}/10)")
        print(f"   Strength: {match.block.strength}")
        print(f"   Text: {match.block.text[:100]}...")
        print(f"   Why: {match.match_reason}\n")
