from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import date
import models
import schemas

# CREATE
def create_job(db: Session, job: schemas.JobCreate) -> models.Job:
    """Create a new job application"""
    db_job = models.Job(**job.model_dump(exclude_unset=True))
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

def find_duplicate_job(
    db: Session,
    url: Optional[str] = None,
    role: Optional[str] = None,
    company: Optional[str] = None,
) -> Optional[models.Job]:
    """Find an existing job matching by exact URL, or by role+company (case-insensitive)."""
    if url:
        existing = db.query(models.Job).filter(models.Job.url == url).first()
        if existing:
            return existing
    if role and company:
        return (
            db.query(models.Job)
            .filter(models.Job.role.ilike(role), models.Job.company.ilike(company))
            .first()
        )
    return None

# READ
def get_job(db: Session, job_id: int) -> Optional[models.Job]:
    """Get a single job by ID"""
    return db.query(models.Job).filter(models.Job.id == job_id).first()

def get_jobs(db: Session, skip: int = 0, limit: int = 100) -> List[models.Job]:
    """Get all jobs with pagination"""
    return db.query(models.Job).offset(skip).limit(limit).all()

def get_jobs_by_status(db: Session, status: models.ApplicationStatus, skip: int = 0, limit: int = 100) -> List[models.Job]:
    """Get jobs filtered by application status"""
    return db.query(models.Job).filter(models.Job.status == status).offset(skip).limit(limit).all()

def get_jobs_by_company(db: Session, company: str, skip: int = 0, limit: int = 100) -> List[models.Job]:
    """Get jobs filtered by company"""
    return db.query(models.Job).filter(models.Job.company.ilike(f"%{company}%")).offset(skip).limit(limit).all()

# UPDATE
def update_job(db: Session, job_id: int, job_update: schemas.JobUpdate) -> Optional[models.Job]:
    """Update an existing job application"""
    db_job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not db_job:
        return None

    # Update only the fields that were provided
    update_data = job_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_job, field, value)

    db.commit()
    db.refresh(db_job)
    return db_job

# DELETE
def delete_job(db: Session, job_id: int) -> bool:
    """Delete a job application"""
    db_job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not db_job:
        return False

    db.delete(db_job)
    db.commit()
    return True


# ==================== FIT EVALUATIONS ====================

def create_fit_evaluation(db: Session, job_id: int, scores: Dict) -> models.JobFitEvaluation:
    """Store a fit evaluation for a job"""
    evaluation = models.JobFitEvaluation(job_id=job_id, **scores)
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    return evaluation


def get_latest_fit_evaluation(db: Session, job_id: int) -> Optional[models.JobFitEvaluation]:
    """Get the most recent fit evaluation for a job"""
    return (
        db.query(models.JobFitEvaluation)
        .filter(models.JobFitEvaluation.job_id == job_id)
        .order_by(models.JobFitEvaluation.created_at.desc())
        .first()
    )


# ==================== CONTACT TRACKING ====================

def get_contact_history(db: Session, job_id: int) -> List[models.ContactHistory]:
    """Get all contact history for a job, ordered by most recent first"""
    return db.query(models.ContactHistory).filter(
        models.ContactHistory.job_id == job_id
    ).order_by(
        models.ContactHistory.contacted_at.desc()
    ).all()


def create_contact_history(
    db: Session,
    job_id: int,
    contact: schemas.ContactHistoryCreate
) -> models.ContactHistory:
    """Create a new contact history record"""
    db_contact = models.ContactHistory(
        job_id=job_id,
        **contact.model_dump()
    )
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact


def get_job_staleness(job: models.Job) -> Dict[str, any]:
    """
    Calculate staleness metrics for a job.

    Returns:
        Dictionary with:
            - days_since_update: Number of days since last activity (or None)
            - staleness_level: Color level (green/yellow/orange/red/gray)
    """
    # Determine the reference date (prefer last_update, fall back to application_date)
    reference_date = job.last_update or job.application_date

    if not reference_date:
        return {
            'days_since_update': None,
            'staleness_level': 'gray'
        }

    # Calculate days since the reference date
    days = (date.today() - reference_date).days

    # Determine staleness level based on thresholds
    if days < 7:
        level = 'green'
    elif days < 14:
        level = 'yellow'
    elif days < 21:
        level = 'orange'
    else:
        level = 'red'

    return {
        'days_since_update': days,
        'staleness_level': level
    }
