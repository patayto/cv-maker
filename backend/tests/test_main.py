"""
Integration tests for FastAPI endpoints (main.py).

Tests all API endpoints:
- GET / (welcome message)
- POST /jobs (create job)
- GET /jobs (list jobs with filters)
- GET /jobs/{id} (get single job)
- PUT /jobs/{id} (update job)
- DELETE /jobs/{id} (delete job)
- POST /parse-job-url (parse job URL)
- GET /linkedin/search (search LinkedIn public job listings)
"""

import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
import json

from models import ApplicationStatus


# ==================== BASIC ENDPOINT TESTS ====================

@pytest.mark.integration
@pytest.mark.api
def test_read_root(client: TestClient):
    """Test the root endpoint returns welcome message."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "CV Maker API" in data["message"]


# ==================== CREATE JOB TESTS ====================

@pytest.mark.integration
@pytest.mark.api
def test_create_job_success(client: TestClient, sample_job_data):
    """Test successfully creating a new job."""
    response = client.post("/jobs", json=sample_job_data)

    assert response.status_code == 201
    data = response.json()
    assert data["role"] == sample_job_data["role"]
    assert data["company"] == sample_job_data["company"]
    assert "id" in data


@pytest.mark.integration
@pytest.mark.api
def test_create_job_with_all_fields(client: TestClient, sample_job_with_extended_fields):
    """Test creating a job with all extended fields."""
    response = client.post("/jobs", json=sample_job_with_extended_fields)

    assert response.status_code == 201
    data = response.json()
    assert data["parsed_skills"] == sample_job_with_extended_fields["parsed_skills"]
    assert data["salary_min"] == sample_job_with_extended_fields["salary_min"]
    assert data["salary_max"] == sample_job_with_extended_fields["salary_max"]
    assert data["recruiter_name"] == sample_job_with_extended_fields["recruiter_name"]


@pytest.mark.integration
@pytest.mark.api
def test_create_job_minimal_fields(client: TestClient):
    """Test creating a job with only required fields."""
    minimal_job = {
        "role": "Test Role",
        "company": "Test Company"
    }

    response = client.post("/jobs", json=minimal_job)

    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "Test Role"
    assert data["company"] == "Test Company"


@pytest.mark.integration
@pytest.mark.api
def test_create_job_invalid_data(client: TestClient):
    """Test creating a job with invalid data."""
    invalid_job = {
        # Missing required fields
        "location": "London"
    }

    response = client.post("/jobs", json=invalid_job)

    # Should return 422 Unprocessable Entity for validation errors
    assert response.status_code == 422


# ==================== LIST JOBS TESTS ====================

@pytest.mark.integration
@pytest.mark.api
def test_get_jobs_empty(client: TestClient):
    """Test getting jobs when database is empty."""
    response = client.get("/jobs")

    assert response.status_code == 200
    data = response.json()
    assert data == []


@pytest.mark.integration
@pytest.mark.api
def test_get_jobs_multiple(client: TestClient, multiple_sample_jobs):
    """Test getting multiple jobs."""
    # Create multiple jobs
    for job_data in multiple_sample_jobs:
        client.post("/jobs", json=job_data)

    response = client.get("/jobs")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == len(multiple_sample_jobs)


@pytest.mark.integration
@pytest.mark.api
def test_get_jobs_pagination(client: TestClient, multiple_sample_jobs):
    """Test jobs pagination with skip and limit."""
    # Create multiple jobs
    for job_data in multiple_sample_jobs:
        client.post("/jobs", json=job_data)

    # Test pagination
    response = client.get("/jobs?skip=0&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Get next page
    response = client.get("/jobs?skip=2&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.integration
@pytest.mark.api
def test_get_jobs_filter_by_status(client: TestClient, multiple_sample_jobs):
    """Test filtering jobs by status."""
    # Create multiple jobs
    for job_data in multiple_sample_jobs:
        client.post("/jobs", json=job_data)

    # Filter by status
    response = client.get("/jobs?status=applied_waiting")

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all(job["status"] == "applied_waiting" for job in data)


@pytest.mark.integration
@pytest.mark.api
def test_get_jobs_filter_by_company(client: TestClient, multiple_sample_jobs):
    """Test filtering jobs by company (partial match)."""
    # Create multiple jobs
    for job_data in multiple_sample_jobs:
        client.post("/jobs", json=job_data)

    # Filter by partial company name
    response = client.get("/jobs?company=Tech")

    assert response.status_code == 200
    data = response.json()
    # Should match "TechCorp" and "BigTech"
    assert len(data) >= 2


@pytest.mark.integration
@pytest.mark.api
def test_get_jobs_filter_by_company_case_insensitive(client: TestClient, sample_job_data):
    """Test that company filter is case-insensitive."""
    client.post("/jobs", json=sample_job_data)

    response = client.get("/jobs?company=techcorp")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["company"] == sample_job_data["company"]


# ==================== GET SINGLE JOB TESTS ====================

@pytest.mark.integration
@pytest.mark.api
def test_get_job_by_id_success(client: TestClient, sample_job_data):
    """Test getting a specific job by ID."""
    # Create a job
    create_response = client.post("/jobs", json=sample_job_data)
    created_job = create_response.json()

    # Get it by ID
    response = client.get(f"/jobs/{created_job['id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_job["id"]
    assert data["role"] == sample_job_data["role"]


@pytest.mark.integration
@pytest.mark.api
def test_get_job_by_id_not_found(client: TestClient):
    """Test getting a non-existent job returns 404."""
    response = client.get("/jobs/99999")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


# ==================== UPDATE JOB TESTS ====================

@pytest.mark.integration
@pytest.mark.api
def test_update_job_success(client: TestClient, sample_job_data):
    """Test successfully updating a job."""
    # Create a job
    create_response = client.post("/jobs", json=sample_job_data)
    created_job = create_response.json()

    # Update it
    update_data = {"role": "Updated Role", "status": "applied_waiting"}
    response = client.put(f"/jobs/{created_job['id']}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "Updated Role"
    assert data["status"] == "applied_waiting"
    # Other fields should remain unchanged
    assert data["company"] == sample_job_data["company"]


@pytest.mark.integration
@pytest.mark.api
def test_update_job_partial_update(client: TestClient, sample_job_data):
    """Test partial update (only some fields)."""
    create_response = client.post("/jobs", json=sample_job_data)
    created_job = create_response.json()

    # Update only one field
    update_data = {"notes": "Updated notes only"}
    response = client.put(f"/jobs/{created_job['id']}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["notes"] == "Updated notes only"
    # All other fields should be preserved
    assert data["role"] == sample_job_data["role"]
    assert data["company"] == sample_job_data["company"]


@pytest.mark.integration
@pytest.mark.api
def test_update_job_extended_fields(client: TestClient, sample_job_data):
    """Test updating extended fields."""
    create_response = client.post("/jobs", json=sample_job_data)
    created_job = create_response.json()

    # Update extended fields
    update_data = {
        "parsed_skills": ["Python", "FastAPI", "PostgreSQL"],
        "salary_min": 60000,
        "salary_max": 80000,
        "salary_currency": "GBP"
    }
    response = client.put(f"/jobs/{created_job['id']}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["parsed_skills"] == ["Python", "FastAPI", "PostgreSQL"]
    assert data["salary_min"] == 60000
    assert data["salary_max"] == 80000


@pytest.mark.integration
@pytest.mark.api
def test_update_job_not_found(client: TestClient):
    """Test updating a non-existent job returns 404."""
    update_data = {"role": "New Role"}
    response = client.put("/jobs/99999", json=update_data)

    assert response.status_code == 404


# ==================== DELETE JOB TESTS ====================

@pytest.mark.integration
@pytest.mark.api
def test_delete_job_success(client: TestClient, sample_job_data):
    """Test successfully deleting a job."""
    # Create a job
    create_response = client.post("/jobs", json=sample_job_data)
    created_job = create_response.json()

    # Delete it
    response = client.delete(f"/jobs/{created_job['id']}")

    assert response.status_code == 204

    # Verify it's gone
    get_response = client.get(f"/jobs/{created_job['id']}")
    assert get_response.status_code == 404


@pytest.mark.integration
@pytest.mark.api
def test_delete_job_not_found(client: TestClient):
    """Test deleting a non-existent job returns 404."""
    response = client.delete("/jobs/99999")

    assert response.status_code == 404


# ==================== PARSE JOB URL TESTS ====================

@pytest.mark.integration
@pytest.mark.api
@pytest.mark.slow
def test_parse_job_url_basic(client: TestClient):
    """Test basic job URL parsing (without LLM)."""
    with patch('job_parser.JobParser.fetch_page_content') as mock_fetch:
        # Mock HTML response
        mock_html = """
        <html>
            <head><title>Software Engineer at TechCorp</title></head>
            <body>
                <h1>Software Engineer</h1>
                <p>Company: TechCorp</p>
                <p>Location: London, UK</p>
                <p>Salary: $80,000 - $100,000</p>
            </body>
        </html>
        """
        mock_fetch.return_value = (mock_html, "Software Engineer TechCorp London, UK $80,000 - $100,000")

        parse_request = {
            "url": "https://example.com/jobs/123",
            "use_llm": False
        }

        response = client.post("/parse-job-url", json=parse_request)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        # Should extract at least the URL
        assert data["data"]["url"] == parse_request["url"]


@pytest.mark.integration
@pytest.mark.api
def test_parse_job_url_linkedin_unfetchable(client: TestClient):
    """Test graceful handling when the LinkedIn jobs-guest API returns nothing."""
    with patch('job_parser.linkedin_guest.fetch_job_detail') as mock_detail:
        mock_detail.return_value = None

        parse_request = {
            "url": "https://linkedin.com/jobs/view/123456789",
            "use_llm": False
        }

        response = client.post("/parse-job-url", json=parse_request)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "role" in data["missing_fields"]


@pytest.mark.integration
@pytest.mark.api
def test_parse_job_url_invalid_url(client: TestClient):
    """Test parsing with invalid URL format."""
    parse_request = {
        "url": "not-a-valid-url",
        "use_llm": False
    }

    response = client.post("/parse-job-url", json=parse_request)

    # Should return some response (success or error)
    assert response.status_code in [200, 422]


@pytest.mark.integration
@pytest.mark.api
def test_parse_job_url_missing_fields(client: TestClient):
    """Test that missing_fields are reported."""
    with patch('job_parser.JobParser.fetch_page_content') as mock_fetch:
        # Return minimal content
        mock_html = "<html><body><p>Minimal job posting</p></body></html>"
        mock_fetch.return_value = (mock_html, "Minimal job posting")

        parse_request = {
            "url": "https://example.com/jobs/123",
            "use_llm": False
        }

        response = client.post("/parse-job-url", json=parse_request)

        assert response.status_code == 200
        data = response.json()
        # Should report missing fields
        assert "missing_fields" in data
        assert isinstance(data["missing_fields"], list)


# ==================== WORKFLOW INTEGRATION TESTS ====================

@pytest.mark.integration
@pytest.mark.api
def test_full_job_lifecycle(client: TestClient, sample_job_data):
    """Test complete CRUD workflow for a job."""
    # 1. Create
    create_response = client.post("/jobs", json=sample_job_data)
    assert create_response.status_code == 201
    job = create_response.json()
    job_id = job["id"]

    # 2. Read (get single)
    get_response = client.get(f"/jobs/{job_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == job_id

    # 3. Read (list)
    list_response = client.get("/jobs")
    assert list_response.status_code == 200
    assert len(list_response.json()) >= 1

    # 4. Update
    update_response = client.put(f"/jobs/{job_id}", json={"status": "applied_waiting"})
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "applied_waiting"

    # 5. Delete
    delete_response = client.delete(f"/jobs/{job_id}")
    assert delete_response.status_code == 204

    # 6. Verify deleted
    get_deleted_response = client.get(f"/jobs/{job_id}")
    assert get_deleted_response.status_code == 404


@pytest.mark.integration
@pytest.mark.api
def test_filter_and_update_workflow(client: TestClient, multiple_sample_jobs):
    """Test filtering jobs and updating them."""
    # Create multiple jobs
    created_ids = []
    for job_data in multiple_sample_jobs:
        response = client.post("/jobs", json=job_data)
        created_ids.append(response.json()["id"])

    # Filter by status
    filter_response = client.get("/jobs?status=yet_to_apply")
    assert filter_response.status_code == 200
    yet_to_apply_jobs = filter_response.json()

    # Update first job to applied
    if yet_to_apply_jobs:
        job_id = yet_to_apply_jobs[0]["id"]
        update_response = client.put(f"/jobs/{job_id}", json={"status": "applied_waiting"})
        assert update_response.status_code == 200

        # Verify filter shows one less now
        filter_again = client.get("/jobs?status=yet_to_apply")
        assert len(filter_again.json()) == len(yet_to_apply_jobs) - 1


# ==================== ERROR HANDLING TESTS ====================

@pytest.mark.integration
@pytest.mark.api
def test_create_job_with_invalid_status(client: TestClient):
    """Test creating a job with invalid status value."""
    invalid_job = {
        "role": "Test Role",
        "company": "Test Company",
        "status": "invalid_status"
    }

    response = client.post("/jobs", json=invalid_job)

    # Should return 422 for validation error
    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.api
def test_update_job_with_invalid_field_type(client: TestClient, sample_job_data):
    """Test updating with wrong field type."""
    create_response = client.post("/jobs", json=sample_job_data)
    job_id = create_response.json()["id"]

    # Try to update with wrong type
    invalid_update = {
        "salary_min": "not a number"  # Should be int
    }

    response = client.put(f"/jobs/{job_id}", json=invalid_update)

    # Should return 422 for validation error
    assert response.status_code == 422


# ==================== PAGINATION EDGE CASES ====================

@pytest.mark.integration
@pytest.mark.api
def test_pagination_beyond_available(client: TestClient, multiple_sample_jobs):
    """Test pagination when skip exceeds available jobs."""
    # Create jobs
    for job_data in multiple_sample_jobs:
        client.post("/jobs", json=job_data)

    # Request beyond available
    response = client.get("/jobs?skip=100&limit=10")

    assert response.status_code == 200
    data = response.json()
    assert data == []


@pytest.mark.integration
@pytest.mark.api
def test_pagination_with_limit_zero(client: TestClient, sample_job_data):
    """Test that limit=0 is rejected (endpoint declares limit >= 1)."""
    client.post("/jobs", json=sample_job_data)

    response = client.get("/jobs?skip=0&limit=0")

    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.api
def test_pagination_with_negative_values(client: TestClient):
    """Test that negative pagination values are handled."""
    # This should either work (treating as 0) or return an error
    response = client.get("/jobs?skip=-1&limit=-1")

    # Response should be valid (either empty list or error)
    assert response.status_code in [200, 422]


# ==================== DUPLICATE DETECTION TESTS ====================

@pytest.mark.integration
@pytest.mark.api
def test_create_duplicate_job_by_url(client: TestClient, sample_job_data):
    """Creating a job with an already-tracked URL returns 409 with the existing id."""
    first = client.post("/jobs", json=sample_job_data).json()

    duplicate = {"role": "Different Role", "company": "Different Co", "url": sample_job_data["url"]}
    response = client.post("/jobs", json=duplicate)

    assert response.status_code == 409
    assert response.json()["detail"]["existing_job_id"] == first["id"]


@pytest.mark.integration
@pytest.mark.api
def test_create_duplicate_job_by_role_and_company(client: TestClient, sample_job_data):
    """Creating a job with the same role+company (case-insensitive) returns 409."""
    client.post("/jobs", json=sample_job_data)

    duplicate = {
        "role": sample_job_data["role"].upper(),
        "company": sample_job_data["company"].lower(),
    }
    response = client.post("/jobs", json=duplicate)

    assert response.status_code == 409


@pytest.mark.integration
@pytest.mark.api
def test_create_non_duplicate_job(client: TestClient, sample_job_data):
    """A different role at the same company is not a duplicate."""
    client.post("/jobs", json=sample_job_data)

    other = {"role": "Another Role", "company": sample_job_data["company"]}
    response = client.post("/jobs", json=other)

    assert response.status_code == 201
