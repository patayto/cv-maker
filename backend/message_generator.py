"""Message generator for job application follow-up communications."""

from typing import Dict, Optional
from models import Job


class MessageGenerator:
    """Generate follow-up messages for job applications."""

    EMAIL_TEMPLATE = """Subject: Following up on {role} application - {company}

Dear {recruiter_name},

I hope this message finds you well. I wanted to follow up on my application for the {role} position at {company}, which I submitted on {application_date}.

I remain very enthusiastic about this opportunity and would welcome the chance to discuss how my experience aligns with your team's needs.

Would you be able to provide an update on the status of my application?

Thank you for your time and consideration.

Best regards,
[Your name]"""

    LINKEDIN_TEMPLATE = """Hi {recruiter_name},

I hope you're doing well! I wanted to follow up on my application for the {role} role at {company}.

I submitted my application on {application_date} and remain very interested in this opportunity. Would you have any updates on the hiring timeline?

Thank you!"""

    @classmethod
    def generate_followup(cls, job: Job, message_type: str = 'email') -> Dict[str, Optional[str]]:
        """Generate a follow-up message for a job application.

        Args:
            job: The Job object to generate a follow-up for
            message_type: Type of message - 'email' or 'linkedin' (default: 'email')

        Returns:
            Dictionary containing:
                - message: The formatted message text
                - subject: Email subject line (None for LinkedIn)
                - recipient_name: Name of the recruiter/hiring manager
                - recipient_email: Email address (may be None)
                - recipient_linkedin: LinkedIn URL (may be None)
        """
        # Select the appropriate template
        template = cls.EMAIL_TEMPLATE if message_type == 'email' else cls.LINKEDIN_TEMPLATE

        # Get recruiter name with fallback
        recruiter_name = job.recruiter_name or "Hiring Manager"

        # Format application date with fallback
        if job.application_date:
            application_date = job.application_date.strftime('%B %d, %Y')
        else:
            application_date = "recently"

        # Format the message with placeholders
        message = template.format(
            role=job.role or "the position",
            company=job.company or "your company",
            recruiter_name=recruiter_name,
            application_date=application_date
        )

        # Build the response dictionary
        return {
            'message': message,
            'subject': f"Following up on {job.role} application - {job.company}" if message_type == 'email' else None,
            'recipient_name': recruiter_name,
            'recipient_email': job.recruiter_email,
            'recipient_linkedin': job.recruiter_linkedin
        }
