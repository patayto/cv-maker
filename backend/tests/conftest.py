"""
Pytest fixtures for backend tests.

Provides:
- Test database configuration
- Test client for API testing
- Sample data fixtures
- Mock objects for external services
"""

import os
import sys
from typing import Generator
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


# Test database configuration
# Using PostgreSQL test database for realistic integration tests
# Note: Requires PostgreSQL to be running
SQLALCHEMY_TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://filipe@localhost/cv_maker_test_db"
)

# Create test engine
test_engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL)

# Create test session factory
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Patch the database engine BEFORE importing modules that use it
from unittest.mock import patch
import database

# Replace the real engine with test engine
database.engine = test_engine
database.SessionLocal = TestingSessionLocal

# Now safe to import modules that create database tables
from database import Base, get_db
from main import app
from models import Job, ApplicationStatus
from fastapi.testclient import TestClient


@pytest.fixture(scope="function")
def test_db() -> Generator:
    """
    Create a fresh database for each test.

    This fixture:
    1. Creates all tables
    2. Yields a database session
    3. Drops all tables after the test

    Scope: function (new database per test)
    """
    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    # Create session
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(test_db) -> Generator:
    """
    Create a test client for API testing.

    This fixture:
    1. Overrides the get_db dependency with test database
    2. Creates a FastAPI TestClient
    3. Yields the client for testing

    Usage:
        def test_endpoint(client):
            response = client.get("/jobs")
            assert response.status_code == 200
    """
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Clear overrides after test
    app.dependency_overrides.clear()


# Sample data fixtures

@pytest.fixture
def sample_job_data() -> dict:
    """Basic job data for creating test jobs."""
    return {
        "role": "Software Engineer",
        "company": "TechCorp",
        "department": "Engineering",
        "location": "London, UK",
        "salary": "£50,000 - £70,000",
        "status": "yet_to_apply",
        "url": "https://example.com/jobs/123",
        "notes": "Great opportunity for backend development"
    }


@pytest.fixture
def sample_job_with_extended_fields() -> dict:
    """Job data with all extended fields populated."""
    return {
        "role": "Senior Backend Engineer",
        "company": "TechCorp",
        "department": "Platform Engineering",
        "location": "Remote - UK",
        "salary": "£80,000 - £120,000",
        "status": "applied_waiting",
        "url": "https://linkedin.com/jobs/view/12345",
        "notes": "Exciting role with great team",

        # Extended fields
        "parsed_skills": ["Python", "FastAPI", "PostgreSQL", "AWS", "Docker"],
        "parsed_requirements": [
            "5+ years of backend development experience",
            "Strong Python and FastAPI knowledge",
            "Experience with PostgreSQL and SQL optimization"
        ],
        "parsed_responsibilities": [
            "Design and implement scalable APIs",
            "Mentor junior engineers",
            "Collaborate with product team on requirements"
        ],
        "salary_min": 80000,
        "salary_max": 120000,
        "salary_currency": "GBP",
        "experience_level": "senior",
        "workplace_type": "remote",
        "employment_type": "full-time",
        "recruiter_name": "Jane Smith",
        "recruiter_email": "jane.smith@techcorp.com",
        "recruiter_linkedin": "https://linkedin.com/in/janesmith",
    }


@pytest.fixture
def multiple_sample_jobs() -> list[dict]:
    """Multiple job entries for list/filter testing."""
    return [
        {
            "role": "Junior Developer",
            "company": "StartupCo",
            "status": "yet_to_apply",
            "location": "London",
            "salary": "£30,000 - £40,000",
        },
        {
            "role": "Senior Engineer",
            "company": "BigTech",
            "status": "applied_waiting",
            "location": "Manchester",
            "salary": "£70,000 - £90,000",
        },
        {
            "role": "Lead Developer",
            "company": "TechCorp",
            "status": "job_offered",
            "location": "Remote",
            "salary": "£100,000 - £130,000",
        },
        {
            "role": "Full Stack Developer",
            "company": "WebCo",
            "status": "application_rejected",
            "location": "Birmingham",
            "salary": "£50,000 - £65,000",
        },
    ]


@pytest.fixture
def mock_linkedin_html() -> str:
    """Mock LinkedIn job posting HTML for parser testing."""
    return """
    <html>
        <head><title>Software Engineer at TechCorp | LinkedIn</title></head>
        <body>
            <div class="top-card-layout__entity-info">
                <h1 class="topcard__title">Software Engineer</h1>
                <a class="topcard__org-name-link">TechCorp</a>
            </div>
            <div class="description">
                <p>We are looking for a talented Software Engineer to join our team.</p>
                <h3>Requirements:</h3>
                <ul>
                    <li>3+ years of Python experience</li>
                    <li>Experience with FastAPI or similar frameworks</li>
                    <li>Strong SQL skills</li>
                </ul>
                <h3>Responsibilities:</h3>
                <ul>
                    <li>Build and maintain RESTful APIs</li>
                    <li>Work with the product team</li>
                    <li>Code reviews and mentoring</li>
                </ul>
                <p>Salary: £60,000 - £80,000</p>
                <p>Location: London, UK</p>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def mock_anthropic_response() -> dict:
    """Mock Claude API response for LLM parsing tests."""
    return {
        "role": "Software Engineer",
        "company": "TechCorp",
        "location": "London, UK",
        "skills": ["Python", "FastAPI", "SQL", "RESTful APIs"],
        "requirements": [
            "3+ years of Python experience",
            "Experience with FastAPI or similar frameworks",
            "Strong SQL skills"
        ],
        "responsibilities": [
            "Build and maintain RESTful APIs",
            "Work with the product team",
            "Code reviews and mentoring"
        ],
        "salary_min": 60000,
        "salary_max": 80000,
        "salary_currency": "GBP",
        "experience_level": "mid",
        "employment_type": "full-time",
    }


# Environment setup

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up environment variables for testing."""
    # Disable actual API calls during tests
    os.environ["TESTING"] = "true"

    # Mock API key (will be caught by mocks)
    if "ANTHROPIC_API_KEY" not in os.environ:
        os.environ["ANTHROPIC_API_KEY"] = "test-api-key-12345"

    yield

    # Cleanup
    if "TESTING" in os.environ:
        del os.environ["TESTING"]


# Utility functions for tests

def create_job_in_db(db, job_data: dict) -> Job:
    """
    Helper function to create a job in the test database.

    Args:
        db: Database session
        job_data: Dictionary of job fields

    Returns:
        Created Job object
    """
    job = Job(**job_data)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@pytest.fixture
def create_job(test_db):
    """Fixture that returns a function to create jobs in the test database."""
    def _create_job(job_data: dict) -> Job:
        return create_job_in_db(test_db, job_data)
    return _create_job
