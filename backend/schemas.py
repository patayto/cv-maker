from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from models import ApplicationStatus

# Pydantic schemas for request/response validation

class JobBase(BaseModel):
    role: Optional[str] = None
    company: Optional[str] = None
    department: Optional[str] = None
    opening_date: Optional[date] = None
    closing_date: Optional[date] = None
    application_date: Optional[date] = None
    last_update: Optional[date] = None
    status: Optional[ApplicationStatus] = None
    url: Optional[str] = None
    cv: Optional[str] = None
    cover_letter: Optional[str] = None
    other_questions: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[str] = None
    notes: Optional[str] = None

    # New fields
    parsed_skills: Optional[List[str]] = None
    parsed_requirements: Optional[List[str]] = None
    parsed_responsibilities: Optional[List[str]] = None
    experience_level: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: Optional[str] = None
    net_salary_yearly: Optional[Decimal] = None
    net_salary_monthly: Optional[Decimal] = None
    workplace_type: Optional[str] = None  # Remote, Hybrid, On-site
    employment_type: Optional[str] = None  # Full-time, Part-time, Contract
    generated_cv_id: Optional[int] = None
    generated_cover_letter_id: Optional[int] = None

    # Contact tracking fields
    recruiter_name: Optional[str] = None
    recruiter_email: Optional[str] = None
    recruiter_linkedin: Optional[str] = None

class JobCreate(JobBase):
    pass

class JobUpdate(JobBase):
    pass

class JobResponse(JobBase):
    id: int

    class Config:
        from_attributes = True


# LegoBlock schemas
class LegoBlockBase(BaseModel):
    category: str
    subcategory: Optional[str] = None
    title: str
    content: str
    skills: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    strength_level: Optional[int] = None
    role_types: Optional[List[str]] = None
    company_types: Optional[List[str]] = None


class LegoBlockCreate(LegoBlockBase):
    pass


class LegoBlockUpdate(BaseModel):
    category: Optional[str] = None
    subcategory: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    skills: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    strength_level: Optional[int] = None
    role_types: Optional[List[str]] = None
    company_types: Optional[List[str]] = None


class LegoBlockResponse(LegoBlockBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# GeneratedCV schemas
class GeneratedCVBase(BaseModel):
    job_id: int
    selected_blocks: Optional[List[int]] = None
    customizations: Optional[Dict[str, Any]] = None
    pdf_path: Optional[str] = None


class GeneratedCVCreate(GeneratedCVBase):
    pass


class GeneratedCVUpdate(BaseModel):
    selected_blocks: Optional[List[int]] = None
    customizations: Optional[Dict[str, Any]] = None
    pdf_path: Optional[str] = None


class GeneratedCVResponse(GeneratedCVBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# GeneratedCoverLetter schemas
class GeneratedCoverLetterBase(BaseModel):
    job_id: int
    content: str
    template_used: Optional[str] = None


class GeneratedCoverLetterCreate(GeneratedCoverLetterBase):
    pass


class GeneratedCoverLetterUpdate(BaseModel):
    content: Optional[str] = None
    template_used: Optional[str] = None


class GeneratedCoverLetterResponse(GeneratedCoverLetterBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# TaxConfig schemas
class TaxConfigBase(BaseModel):
    tax_year: int
    country: str
    personal_allowance: Optional[Decimal] = None
    basic_rate: Optional[Decimal] = None
    higher_rate: Optional[Decimal] = None
    additional_rate: Optional[Decimal] = None
    thresholds: Optional[Dict[str, Any]] = None
    ni_rates: Optional[Dict[str, Any]] = None
    student_loan_config: Optional[Dict[str, Any]] = None
    is_active: Optional[int] = 1


class TaxConfigCreate(TaxConfigBase):
    pass


class TaxConfigUpdate(BaseModel):
    tax_year: Optional[int] = None
    country: Optional[str] = None
    personal_allowance: Optional[Decimal] = None
    basic_rate: Optional[Decimal] = None
    higher_rate: Optional[Decimal] = None
    additional_rate: Optional[Decimal] = None
    thresholds: Optional[Dict[str, Any]] = None
    ni_rates: Optional[Dict[str, Any]] = None
    student_loan_config: Optional[Dict[str, Any]] = None
    is_active: Optional[int] = None


class TaxConfigResponse(TaxConfigBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== SALARY CALCULATION SCHEMAS ====================

class SalaryCalculationRequest(BaseModel):
    gross_yearly: float
    pension_pct: float = 0.05
    include_student_loan: bool = True
    student_loan_plan: str = "plan1"


class TaxBreakdownResponse(BaseModel):
    personal_allowance: float
    taxable_income: float
    basic_rate_amount: float
    higher_rate_amount: float
    additional_rate_amount: float


class BudgetRecommendationResponse(BaseModel):
    needs_50: float
    wants_30: float
    savings_20: float


class SalaryCalculationResponse(BaseModel):
    gross_yearly: float
    gross_monthly: float
    net_yearly: float
    net_monthly: float
    income_tax: float
    national_insurance: float
    student_loan: float
    pension: float
    effective_tax_rate: float
    tax_breakdown: TaxBreakdownResponse
    budget_recommendation: BudgetRecommendationResponse


# ==================== LEGO BLOCKS SCHEMAS ====================

class LegoBlockImportResponse(BaseModel):
    success: bool
    imported_count: int
    skipped_count: int
    message: str


# ==================== CV GENERATION SCHEMAS ====================

class BlockSuggestion(BaseModel):
    block_id: int
    block: LegoBlockResponse
    relevance_score: float


class CVSuggestionsResponse(BaseModel):
    job_id: int
    suggestions: List[BlockSuggestion]


class CVGenerationRequest(BaseModel):
    max_blocks: int = 10


class CVGenerationResponse(BaseModel):
    cv_id: int
    selected_blocks: List[LegoBlockResponse]
    latex: str


# ==================== COVER LETTER SCHEMAS ====================

class CoverLetterGenerationRequest(BaseModel):
    style: str = "professional"  # professional, enthusiastic, technical


class CoverLetterGenerationResponse(BaseModel):
    letter_id: int
    content: str


class CoverLetterUpdateRequest(BaseModel):
    instructions: str


# ==================== CONTACT HISTORY SCHEMAS ====================

class ContactHistoryBase(BaseModel):
    contact_method: str  # Email, LinkedIn, Phone, In-person, etc.
    message_content: Optional[str] = None
    notes: Optional[str] = None


class ContactHistoryCreate(ContactHistoryBase):
    """Schema for creating a new contact history record.

    Note: job_id comes from the URL path parameter.
    contacted_at is auto-generated by the server (defaults to current timestamp).
    """
    pass


class ContactHistoryResponse(ContactHistoryBase):
    id: int
    job_id: int
    contacted_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True
