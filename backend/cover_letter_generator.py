"""
Cover Letter Generator Module

Generates and customizes cover letters using Claude AI.
Falls back to template-based generation when API key is not available.
"""

import os
from typing import Optional
from sqlalchemy.orm import Session
from anthropic import Anthropic

try:
    from models import Job, GeneratedCV, LegoBlock
except ImportError:
    pass


class CoverLetterGenerator:
    """Generate and customize cover letters using Claude AI"""

    def __init__(self):
        self.anthropic_client = None
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            self.anthropic_client = Anthropic(api_key=api_key)

    def generate(self, job_id: int, db: Session, style: str = "professional") -> str:
        """
        Generate a cover letter for a specific job application.

        Args:
            job_id: ID of the job to generate cover letter for
            db: Database session
            style: Style of cover letter ("professional", "enthusiastic", "technical")

        Returns:
            Generated cover letter text
        """
        # Get job details
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job with ID {job_id} not found")

        # Get related CV blocks if available
        lego_blocks = []
        if job.generated_cv_id:
            generated_cv = db.query(GeneratedCV).filter(GeneratedCV.id == job.generated_cv_id).first()
            if generated_cv and generated_cv.selected_blocks:
                lego_blocks = db.query(LegoBlock).filter(
                    LegoBlock.id.in_(generated_cv.selected_blocks)
                ).all()

        if self.anthropic_client:
            return self._generate_with_llm(job, lego_blocks, style)
        else:
            return self._generate_fallback(job, style)

    def _generate_with_llm(self, job, lego_blocks: list, style: str) -> str:
        """Generate cover letter using Claude AI"""
        # Prepare context
        job_context = f"""
Role: {job.role or 'N/A'}
Company: {job.company or 'N/A'}
Department: {job.department or 'N/A'}
Location: {job.location or 'N/A'}
"""
        if job.parsed_requirements:
            job_context += f"\nKey Requirements:\n" + "\n".join(f"- {req}" for req in job.parsed_requirements[:5])

        if job.parsed_responsibilities:
            job_context += f"\n\nKey Responsibilities:\n" + "\n".join(f"- {resp}" for resp in job.parsed_responsibilities[:5])

        # Add CV achievements if available
        achievements_context = ""
        if lego_blocks:
            achievements_context = "\n\nRelevant Achievements from CV:\n"
            for block in lego_blocks[:3]:  # Use top 3 blocks
                achievements_context += f"- {block.content}\n"

        # Style-specific instructions
        style_instructions = {
            "professional": "Write in a formal, professional tone. Focus on qualifications and alignment with role requirements.",
            "enthusiastic": "Write with genuine enthusiasm and passion. Show excitement about the opportunity while remaining professional.",
            "technical": "Focus on technical skills and achievements. Use industry terminology and emphasize problem-solving abilities.",
        }
        style_guide = style_instructions.get(style, style_instructions["professional"])

        prompt = f"""Write a compelling cover letter for this job application.

{style_guide}

Job Details:
{job_context}
{achievements_context}

Cover letter should:
1. Open with a strong introduction expressing interest in the role
2. Highlight 2-3 key qualifications that match the job requirements
3. Reference specific achievements that demonstrate fit
4. Express enthusiasm for the company and role
5. Close with a call to action

Format as a professional business letter without addresses (just the body paragraphs).
Keep it concise (250-300 words).
"""

        try:
            message = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text.strip()
        except Exception as e:
            print(f"LLM generation failed: {e}, using fallback template")
            return self._generate_fallback(job, style)

    def _generate_fallback(self, job, style: str) -> str:
        """Generate cover letter using template when no API key available"""
        company = job.company or "[Company Name]"
        role = job.role or "[Position]"

        template = f"""Dear Hiring Manager,

I am writing to express my strong interest in the {role} position at {company}. With my background in software engineering and proven track record of delivering high-impact projects, I am confident I would be a valuable addition to your team.

Throughout my career, I have consistently demonstrated the ability to solve complex technical challenges and deliver results that exceed expectations. My experience aligns well with the requirements for this role, particularly in areas of system design, development, and cross-functional collaboration.

I am particularly excited about the opportunity to contribute to {company}'s mission and work alongside a talented team of professionals. I am confident that my technical skills, problem-solving abilities, and passion for innovation would enable me to make immediate contributions to your organization.

I would welcome the opportunity to discuss how my experience and qualifications align with your needs. Thank you for considering my application.

Sincerely,
[Your Name]"""

        return template

    def customize(self, base_letter: str, instructions: str) -> str:
        """
        Customize an existing cover letter based on user instructions.

        Args:
            base_letter: Original cover letter text
            instructions: User instructions for customization

        Returns:
            Customized cover letter
        """
        if not self.anthropic_client:
            # No API key, return original
            return base_letter

        prompt = f"""Revise this cover letter based on the following instructions:

Instructions: {instructions}

Original Cover Letter:
{base_letter}

Provide the revised cover letter."""

        try:
            message = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text.strip()
        except Exception as e:
            print(f"Customization failed: {e}")
            return base_letter


# Create singleton instance
cover_letter_generator = CoverLetterGenerator()
