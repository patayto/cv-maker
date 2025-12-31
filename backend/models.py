from sqlalchemy import Column, Integer, String, Date, Text, Enum as SQLEnum, ForeignKey, DateTime, Numeric
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship
from database import Base
import enum
from datetime import datetime

# Define application_status enum matching the PostgreSQL enum
class ApplicationStatus(str, enum.Enum):
    yet_to_apply = "yet_to_apply"
    applied_waiting = "applied_waiting"
    job_offered = "job_offered"
    job_accepted = "job_accepted"
    application_rejected = "application_rejected"
    job_rejected = "job_rejected"

# Job model matching the jobs table schema
class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(255))
    company = Column(String(255))
    department = Column(String(255))
    opening_date = Column(Date)
    closing_date = Column(Date)
    application_date = Column(Date)
    last_update = Column(Date)
    status = Column(SQLEnum(ApplicationStatus, name="application_status", create_type=False))
    url = Column(Text)
    cv = Column(Text)  # Now stores file path instead of text content
    cover_letter = Column(Text)  # Now stores file path instead of text content
    other_questions = Column(Text)  # Now stores file path instead of text content
    location = Column(String(255))
    salary = Column(String(255))
    notes = Column(Text)

    # New columns for enhanced job tracking
    parsed_skills = Column(ARRAY(String))
    parsed_requirements = Column(ARRAY(String))
    parsed_responsibilities = Column(ARRAY(String))
    experience_level = Column(String(50))
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    salary_currency = Column(String(10))
    net_salary_yearly = Column(Numeric(10, 2))
    net_salary_monthly = Column(Numeric(10, 2))
    workplace_type = Column(String(50))  # Remote, Hybrid, On-site
    employment_type = Column(String(50))  # Full-time, Part-time, Contract, etc.
    generated_cv_id = Column(Integer, ForeignKey('generated_cvs.id'))
    generated_cover_letter_id = Column(Integer, ForeignKey('generated_cover_letters.id'))

    # Contact tracking fields
    recruiter_name = Column(String(255))
    recruiter_email = Column(String(255))
    recruiter_linkedin = Column(String(500))

    # Relationships
    generated_cv = relationship("GeneratedCV", foreign_keys=[generated_cv_id])
    generated_cover_letter = relationship("GeneratedCoverLetter", foreign_keys=[generated_cover_letter_id])
    contact_history = relationship("ContactHistory", back_populates="job", cascade="all, delete-orphan")


# LegoBlock model for storing reusable CV content blocks
class LegoBlock(Base):
    __tablename__ = "lego_blocks"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False)
    subcategory = Column(String(100))
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    skills = Column(ARRAY(String))
    keywords = Column(ARRAY(String))
    strength_level = Column(Integer)  # 1-5 rating for content strength
    role_types = Column(ARRAY(String))  # e.g., ['backend', 'fullstack']
    company_types = Column(ARRAY(String))  # e.g., ['startup', 'enterprise']
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# GeneratedCV model for tracking CV versions created for specific jobs
class GeneratedCV(Base):
    __tablename__ = "generated_cvs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey('jobs.id'))
    selected_blocks = Column(ARRAY(Integer))  # Array of LegoBlock IDs
    customizations = Column(JSONB)  # Store any custom modifications
    pdf_path = Column(Text)  # Path to generated PDF
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    job = relationship("Job", foreign_keys=[job_id])


# GeneratedCoverLetter model for tracking cover letters
class GeneratedCoverLetter(Base):
    __tablename__ = "generated_cover_letters"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey('jobs.id'))
    content = Column(Text, nullable=False)
    template_used = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    job = relationship("Job", foreign_keys=[job_id])


# TaxConfig model for storing tax calculation parameters
class TaxConfig(Base):
    __tablename__ = "tax_configs"

    id = Column(Integer, primary_key=True, index=True)
    tax_year = Column(Integer, nullable=False)
    country = Column(String(2), nullable=False)  # ISO country code
    personal_allowance = Column(Numeric(10, 2))
    basic_rate = Column(Numeric(5, 2))  # Percentage
    higher_rate = Column(Numeric(5, 2))  # Percentage
    additional_rate = Column(Numeric(5, 2))  # Percentage
    thresholds = Column(JSONB)  # Tax band thresholds
    ni_rates = Column(JSONB)  # National Insurance rates
    student_loan_config = Column(JSONB)  # Student loan repayment config
    is_active = Column(Integer, default=1)  # Boolean: 1=active, 0=inactive
    created_at = Column(DateTime, default=datetime.utcnow)


# ContactHistory model for tracking all contact interactions with recruiters
class ContactHistory(Base):
    __tablename__ = "contact_history"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey('jobs.id'), nullable=False)
    contacted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    contact_method = Column(String(50), nullable=False)  # Email, LinkedIn, Phone, In-person, etc.
    message_content = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    job = relationship("Job", back_populates="contact_history")
