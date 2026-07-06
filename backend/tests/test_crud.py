"""
Unit tests for CRUD operations (crud.py).

Tests all database operations:
- Create, read, update, delete jobs
- Filtering by status and company
- Pagination
- Contact history tracking
- Staleness calculation
"""

import pytest
from datetime import date, timedelta
from sqlalchemy.orm import Session

import crud
import models
import schemas
from tests.conftest import create_job_in_db


# ==================== CREATE TESTS ====================

@pytest.mark.unit
@pytest.mark.database
def test_create_job_basic(test_db: Session, sample_job_data):
    """Test creating a basic job with minimal fields."""
    job_create = schemas.JobCreate(**sample_job_data)
    created_job = crud.create_job(test_db, job_create)

    assert created_job.id is not None
    assert created_job.role == sample_job_data["role"]
    assert created_job.company == sample_job_data["company"]
    assert created_job.status == models.ApplicationStatus.yet_to_apply


@pytest.mark.unit
@pytest.mark.database
def test_create_job_with_all_fields(test_db: Session, sample_job_with_extended_fields):
    """Test creating a job with all extended fields populated."""
    job_create = schemas.JobCreate(**sample_job_with_extended_fields)
    created_job = crud.create_job(test_db, job_create)

    assert created_job.id is not None
    assert created_job.role == sample_job_with_extended_fields["role"]
    assert created_job.parsed_skills == sample_job_with_extended_fields["parsed_skills"]
    assert created_job.salary_min == sample_job_with_extended_fields["salary_min"]
    assert created_job.salary_max == sample_job_with_extended_fields["salary_max"]
    assert created_job.salary_currency == sample_job_with_extended_fields["salary_currency"]
    assert created_job.experience_level == sample_job_with_extended_fields["experience_level"]
    assert created_job.recruiter_name == sample_job_with_extended_fields["recruiter_name"]


@pytest.mark.unit
@pytest.mark.database
def test_create_job_with_partial_fields(test_db: Session):
    """Test creating a job with only required fields."""
    minimal_data = {
        "role": "Test Role",
        "company": "Test Company"
    }
    job_create = schemas.JobCreate(**minimal_data)
    created_job = crud.create_job(test_db, job_create)

    assert created_job.id is not None
    assert created_job.role == "Test Role"
    assert created_job.company == "Test Company"
    # Optional fields should be None
    assert created_job.location is None
    assert created_job.salary is None
    assert created_job.parsed_skills is None


# ==================== READ TESTS ====================

@pytest.mark.unit
@pytest.mark.database
def test_get_job_existing(test_db: Session, sample_job_data):
    """Test retrieving an existing job by ID."""
    # Create a job first
    created_job = create_job_in_db(test_db, sample_job_data)

    # Retrieve it
    retrieved_job = crud.get_job(test_db, created_job.id)

    assert retrieved_job is not None
    assert retrieved_job.id == created_job.id
    assert retrieved_job.role == created_job.role
    assert retrieved_job.company == created_job.company


@pytest.mark.unit
@pytest.mark.database
def test_get_job_nonexistent(test_db: Session):
    """Test retrieving a job that doesn't exist."""
    result = crud.get_job(test_db, 99999)
    assert result is None


@pytest.mark.unit
@pytest.mark.database
def test_get_jobs_empty_database(test_db: Session):
    """Test retrieving jobs from an empty database."""
    jobs = crud.get_jobs(test_db)
    assert jobs == []


@pytest.mark.unit
@pytest.mark.database
def test_get_jobs_multiple(test_db: Session, multiple_sample_jobs):
    """Test retrieving multiple jobs."""
    # Create multiple jobs
    for job_data in multiple_sample_jobs:
        create_job_in_db(test_db, job_data)

    # Retrieve all
    jobs = crud.get_jobs(test_db)

    assert len(jobs) == len(multiple_sample_jobs)


@pytest.mark.unit
@pytest.mark.database
def test_get_jobs_pagination(test_db: Session, multiple_sample_jobs):
    """Test pagination with skip and limit."""
    # Create multiple jobs
    for job_data in multiple_sample_jobs:
        create_job_in_db(test_db, job_data)

    # Test skip
    jobs_page1 = crud.get_jobs(test_db, skip=0, limit=2)
    assert len(jobs_page1) == 2

    jobs_page2 = crud.get_jobs(test_db, skip=2, limit=2)
    assert len(jobs_page2) == 2

    # Ensure different jobs
    assert jobs_page1[0].id != jobs_page2[0].id


# ==================== FILTER TESTS ====================

@pytest.mark.unit
@pytest.mark.database
def test_get_jobs_by_status(test_db: Session, multiple_sample_jobs):
    """Test filtering jobs by status."""
    # Create jobs with different statuses
    for job_data in multiple_sample_jobs:
        create_job_in_db(test_db, job_data)

    # Filter by status
    applied_jobs = crud.get_jobs_by_status(
        test_db,
        models.ApplicationStatus.applied_waiting
    )

    assert len(applied_jobs) == 1
    assert applied_jobs[0].status == models.ApplicationStatus.applied_waiting


@pytest.mark.unit
@pytest.mark.database
def test_get_jobs_by_status_no_results(test_db: Session, sample_job_data):
    """Test filtering by a status with no matching jobs."""
    # Create a job with yet_to_apply status
    create_job_in_db(test_db, sample_job_data)

    # Search for job_offered status
    jobs = crud.get_jobs_by_status(
        test_db,
        models.ApplicationStatus.job_offered
    )

    assert jobs == []


@pytest.mark.unit
@pytest.mark.database
def test_get_jobs_by_company_exact_match(test_db: Session, multiple_sample_jobs):
    """Test filtering by company name (exact match)."""
    for job_data in multiple_sample_jobs:
        create_job_in_db(test_db, job_data)

    jobs = crud.get_jobs_by_company(test_db, "TechCorp")

    assert len(jobs) == 1
    assert jobs[0].company == "TechCorp"


@pytest.mark.unit
@pytest.mark.database
def test_get_jobs_by_company_partial_match(test_db: Session, multiple_sample_jobs):
    """Test filtering by company with partial matching (case-insensitive)."""
    for job_data in multiple_sample_jobs:
        create_job_in_db(test_db, job_data)

    # Partial match with different case
    jobs = crud.get_jobs_by_company(test_db, "tech")

    # Should match "TechCorp" and "BigTech"
    assert len(jobs) == 2


@pytest.mark.unit
@pytest.mark.database
def test_get_jobs_by_company_no_results(test_db: Session, sample_job_data):
    """Test filtering by company with no matches."""
    create_job_in_db(test_db, sample_job_data)

    jobs = crud.get_jobs_by_company(test_db, "NonExistentCompany")

    assert jobs == []


# ==================== UPDATE TESTS ====================

@pytest.mark.unit
@pytest.mark.database
def test_update_job_single_field(test_db: Session, sample_job_data):
    """Test updating a single field."""
    # Create a job
    created_job = create_job_in_db(test_db, sample_job_data)

    # Update just the role
    job_update = schemas.JobUpdate(role="Updated Role")
    updated_job = crud.update_job(test_db, created_job.id, job_update)

    assert updated_job is not None
    assert updated_job.role == "Updated Role"
    # Other fields should remain unchanged
    assert updated_job.company == sample_job_data["company"]


@pytest.mark.unit
@pytest.mark.database
def test_update_job_multiple_fields(test_db: Session, sample_job_data):
    """Test updating multiple fields at once."""
    created_job = create_job_in_db(test_db, sample_job_data)

    # Update multiple fields
    job_update = schemas.JobUpdate(
        role="New Role",
        status="applied_waiting",
        notes="Updated notes"
    )
    updated_job = crud.update_job(test_db, created_job.id, job_update)

    assert updated_job.role == "New Role"
    assert updated_job.status == models.ApplicationStatus.applied_waiting
    assert updated_job.notes == "Updated notes"


@pytest.mark.unit
@pytest.mark.database
def test_update_job_extended_fields(test_db: Session, sample_job_data):
    """Test updating extended fields (skills, salary, etc.)."""
    created_job = create_job_in_db(test_db, sample_job_data)

    # Update extended fields
    job_update = schemas.JobUpdate(
        parsed_skills=["Python", "FastAPI", "PostgreSQL"],
        salary_min=60000,
        salary_max=80000,
        salary_currency="GBP",
        experience_level="mid"
    )
    updated_job = crud.update_job(test_db, created_job.id, job_update)

    assert updated_job.parsed_skills == ["Python", "FastAPI", "PostgreSQL"]
    assert updated_job.salary_min == 60000
    assert updated_job.salary_max == 80000
    assert updated_job.salary_currency == "GBP"
    assert updated_job.experience_level == "mid"


@pytest.mark.unit
@pytest.mark.database
def test_update_job_nonexistent(test_db: Session):
    """Test updating a job that doesn't exist."""
    job_update = schemas.JobUpdate(role="New Role")
    result = crud.update_job(test_db, 99999, job_update)

    assert result is None


@pytest.mark.unit
@pytest.mark.database
def test_update_job_to_null(test_db: Session, sample_job_with_extended_fields):
    """Test clearing fields by setting them to None."""
    created_job = create_job_in_db(test_db, sample_job_with_extended_fields)

    # Clear some fields
    job_update = schemas.JobUpdate(
        notes=None,
        recruiter_name=None,
        parsed_skills=None
    )
    updated_job = crud.update_job(test_db, created_job.id, job_update)

    assert updated_job.notes is None
    assert updated_job.recruiter_name is None
    assert updated_job.parsed_skills is None


# ==================== DELETE TESTS ====================

@pytest.mark.unit
@pytest.mark.database
def test_delete_job_existing(test_db: Session, sample_job_data):
    """Test deleting an existing job."""
    created_job = create_job_in_db(test_db, sample_job_data)

    # Delete the job
    result = crud.delete_job(test_db, created_job.id)

    assert result is True

    # Verify it's gone
    deleted_job = crud.get_job(test_db, created_job.id)
    assert deleted_job is None


@pytest.mark.unit
@pytest.mark.database
def test_delete_job_nonexistent(test_db: Session):
    """Test deleting a job that doesn't exist."""
    result = crud.delete_job(test_db, 99999)
    assert result is False


@pytest.mark.unit
@pytest.mark.database
def test_delete_job_and_verify_count(test_db: Session, multiple_sample_jobs):
    """Test that deletion reduces job count correctly."""
    # Create multiple jobs
    for job_data in multiple_sample_jobs:
        create_job_in_db(test_db, job_data)

    initial_count = len(crud.get_jobs(test_db))

    # Delete first job
    first_job = crud.get_jobs(test_db)[0]
    crud.delete_job(test_db, first_job.id)

    final_count = len(crud.get_jobs(test_db))

    assert final_count == initial_count - 1


# ==================== STALENESS TESTS ====================

@pytest.mark.unit
def test_get_job_staleness_recent_update():
    """Test staleness for a recently updated job (green)."""
    job = models.Job(
        id=1,
        role="Test",
        company="Test",
        last_update=date.today() - timedelta(days=3)
    )

    staleness = crud.get_job_staleness(job)

    assert staleness["days_since_update"] == 3
    assert staleness["staleness_level"] == "green"


@pytest.mark.unit
def test_get_job_staleness_week_old():
    """Test staleness for a week-old job (yellow)."""
    job = models.Job(
        id=1,
        role="Test",
        company="Test",
        last_update=date.today() - timedelta(days=10)
    )

    staleness = crud.get_job_staleness(job)

    assert staleness["days_since_update"] == 10
    assert staleness["staleness_level"] == "yellow"


@pytest.mark.unit
def test_get_job_staleness_two_weeks_old():
    """Test staleness for a two-week-old job (orange)."""
    job = models.Job(
        id=1,
        role="Test",
        company="Test",
        last_update=date.today() - timedelta(days=18)
    )

    staleness = crud.get_job_staleness(job)

    assert staleness["days_since_update"] == 18
    assert staleness["staleness_level"] == "orange"


@pytest.mark.unit
def test_get_job_staleness_very_old():
    """Test staleness for a very old job (red)."""
    job = models.Job(
        id=1,
        role="Test",
        company="Test",
        last_update=date.today() - timedelta(days=30)
    )

    staleness = crud.get_job_staleness(job)

    assert staleness["days_since_update"] == 30
    assert staleness["staleness_level"] == "red"


@pytest.mark.unit
def test_get_job_staleness_no_date():
    """Test staleness when no date is available (gray)."""
    job = models.Job(
        id=1,
        role="Test",
        company="Test",
        last_update=None,
        application_date=None
    )

    staleness = crud.get_job_staleness(job)

    assert staleness["days_since_update"] is None
    assert staleness["staleness_level"] == "gray"


@pytest.mark.unit
def test_get_job_staleness_fallback_to_application_date():
    """Test that staleness falls back to application_date if last_update is None."""
    job = models.Job(
        id=1,
        role="Test",
        company="Test",
        last_update=None,
        application_date=date.today() - timedelta(days=5)
    )

    staleness = crud.get_job_staleness(job)

    assert staleness["days_since_update"] == 5
    assert staleness["staleness_level"] == "green"


# ==================== EDGE CASES ====================

@pytest.mark.unit
@pytest.mark.database
def test_create_job_with_empty_arrays(test_db: Session):
    """Test creating a job with empty arrays for extended fields."""
    job_data = {
        "role": "Test Role",
        "company": "Test Company",
        "parsed_skills": [],
        "parsed_requirements": [],
        "parsed_responsibilities": []
    }
    job_create = schemas.JobCreate(**job_data)
    created_job = crud.create_job(test_db, job_create)

    assert created_job.parsed_skills == []
    assert created_job.parsed_requirements == []
    assert created_job.parsed_responsibilities == []


@pytest.mark.unit
@pytest.mark.database
def test_update_job_preserves_unspecified_fields(test_db: Session, sample_job_with_extended_fields):
    """Test that updating doesn't clear unspecified fields."""
    created_job = create_job_in_db(test_db, sample_job_with_extended_fields)

    # Update only role
    job_update = schemas.JobUpdate(role="New Role")
    updated_job = crud.update_job(test_db, created_job.id, job_update)

    # All other fields should be preserved
    assert updated_job.role == "New Role"
    assert updated_job.parsed_skills == sample_job_with_extended_fields["parsed_skills"]
    assert updated_job.salary_min == sample_job_with_extended_fields["salary_min"]
    assert updated_job.recruiter_name == sample_job_with_extended_fields["recruiter_name"]


@pytest.mark.unit
@pytest.mark.database
def test_pagination_edge_cases(test_db: Session, multiple_sample_jobs):
    """Test pagination with edge cases."""
    for job_data in multiple_sample_jobs:
        create_job_in_db(test_db, job_data)

    # Request more than available
    jobs = crud.get_jobs(test_db, skip=0, limit=100)
    assert len(jobs) == len(multiple_sample_jobs)

    # Skip beyond available
    jobs = crud.get_jobs(test_db, skip=100, limit=10)
    assert jobs == []

    # Limit of 0 (should return empty)
    jobs = crud.get_jobs(test_db, skip=0, limit=0)
    assert jobs == []
