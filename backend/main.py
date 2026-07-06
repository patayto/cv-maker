from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException, Query, Body, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db, engine, SessionLocal
from models import Base, ApplicationStatus
import models
import schemas
import crud
from job_parser import job_parser
import document_pipeline
import fit_evaluator
import gap_analyzer
import latex_service
import linkedin_guest
import requests
from message_generator import MessageGenerator
from lego_blocks_matcher import get_matcher
from auth import verify_auth
from pydantic import BaseModel
import aiofiles
import logging
import os
import time
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)

# Create database tables (if they don't exist)
# Note: In production, use Alembic migrations instead
Base.metadata.create_all(bind=engine)

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title="CV Maker API", version="1.0.0")

# Mount uploads directory for static file serving
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Configure CORS
# CORS_ORIGINS env var should be comma-separated list of allowed origins
ALLOWED_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "CV Maker API - Use /docs for API documentation"}

@app.get("/health")
async def health_check():
    """Health check endpoint - no authentication required"""
    return {"status": "ok"}

# Database connection test endpoint
@app.get("/db-test")
async def test_db_connection(db: Session = Depends(get_db), username: str = Depends(verify_auth)):
    """Test database connection by counting jobs in the database"""
    try:
        count = db.query(models.Job).count()
        return {
            "status": "connected",
            "message": "Database connection successful",
            "jobs_count": count
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Database connection failed: {str(e)}"
        }

# ==================== JOB URL PARSER ENDPOINT ====================

class ParseUrlRequest(BaseModel):
    url: str = ""  # Optional when html is provided
    html: Optional[str] = None  # Raw HTML content (alternative to URL)
    use_llm: bool = True

class ParseUrlResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    missing_fields: List[str] = []
    error: Optional[str] = None

@app.post("/parse-job-url", response_model=ParseUrlResponse)
async def parse_job_url(request: ParseUrlRequest, username: str = Depends(verify_auth)):
    """
    Parse a job posting from URL or raw HTML and extract job details.

    Modes:
    - URL mode: Provide 'url' field to fetch and parse
    - HTML mode: Provide 'html' field with raw HTML content (bypasses fetching)

    Uses web scraping and optionally Claude AI to extract information.
    """
    try:
        job_data, missing_fields = job_parser.parse_job_url(
            request.url,
            use_llm=request.use_llm,
            html=request.html
        )

        return ParseUrlResponse(
            success=True,
            data=job_data,
            missing_fields=missing_fields
        )
    except ConnectionError:
        return ParseUrlResponse(
            success=False,
            error=f"Network error: Unable to connect to {request.url}. Please check your internet connection.",
            missing_fields=[]
        )
    except TimeoutError:
        return ParseUrlResponse(
            success=False,
            error=f"Timeout error: The request to {request.url} took too long. Please try again.",
            missing_fields=[]
        )
    except ValueError as e:
        return ParseUrlResponse(
            success=False,
            error=f"Invalid URL: {str(e)}",
            missing_fields=[]
        )
    except Exception as e:
        error_message = str(e)
        # Provide helpful error messages for common issues
        if 'rate limit' in error_message.lower() or '429' in error_message:
            error_message = "Rate limited: the site is blocking requests. Please wait a few minutes and try again."

        return ParseUrlResponse(
            success=False,
            error=error_message,
            missing_fields=[]
        )

# ==================== LINKEDIN JOB SEARCH ENDPOINT ====================

@app.get("/linkedin/search")
async def linkedin_search(
    keywords: Optional[str] = Query(None, description="Search keywords, e.g. job title or skill"),
    location: Optional[str] = Query(None, description='Location, e.g. "London, United Kingdom" or "Remote"'),
    jobage: Optional[int] = Query(None, ge=1, description="Only jobs posted within this many days"),
    remote: Optional[str] = Query(None, description="Workplace type: remote, hybrid, or onsite"),
    page: int = Query(1, ge=1, description="Result page (10 results per page)"),
    db: Session = Depends(get_db),
    username: str = Depends(verify_auth),
):
    """Search LinkedIn public job listings (unauthenticated jobs-guest API).

    Personal use only - keep request volume low.
    """
    try:
        cards = linkedin_guest.search_jobs(
            query=keywords, location=location, jobage_days=jobage, remote=remote, page=page
        )
    except (ConnectionError, requests.RequestException) as e:
        raise HTTPException(status_code=502, detail=f"LinkedIn search failed: {e}")

    # Flag results already tracked (LinkedIn URL formats vary, so match by job id)
    tracked_ids = set()
    for (url,) in db.query(models.Job.url).filter(models.Job.url.ilike("%linkedin.com%")).all():
        job_id = linkedin_guest.id_from_url(url or "")
        if job_id:
            tracked_ids.add(job_id)

    return {
        "results": [{**card.to_dict(), "tracked": card.id in tracked_ids} for card in cards],
        "page": page,
    }

# ==================== CANDIDATE PROFILE & FIT EVALUATION ====================

@app.get("/profile", response_model=schemas.ProfileContent)
def get_profile(username: str = Depends(verify_auth)):
    """Get the candidate profile markdown"""
    return schemas.ProfileContent(content=fit_evaluator.read_profile())

@app.put("/profile", response_model=schemas.ProfileContent)
def update_profile(profile: schemas.ProfileContent, username: str = Depends(verify_auth)):
    """Replace the candidate profile markdown"""
    fit_evaluator.write_profile(profile.content)
    return profile

@app.post("/jobs/{job_id}/evaluate-fit", response_model=schemas.FitEvaluationResponse)
def evaluate_job_fit(job_id: int, db: Session = Depends(get_db), username: str = Depends(verify_auth)):
    """Score this job against the candidate profile (LLM-backed)"""
    job = crud.get_job(db=db, job_id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    try:
        scores = fit_evaluator.evaluate_fit(job)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return crud.create_fit_evaluation(db=db, job_id=job_id, scores=scores)

@app.get("/jobs/{job_id}/fit", response_model=schemas.FitEvaluationResponse)
def get_job_fit(job_id: int, db: Session = Depends(get_db), username: str = Depends(verify_auth)):
    """Get the most recent fit evaluation for this job"""
    evaluation = crud.get_latest_fit_evaluation(db=db, job_id=job_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="No fit evaluation for this job yet")
    return evaluation

# ==================== SKILL GAP ANALYSIS ====================

@app.get("/gap-analysis")
def gap_analysis(db: Session = Depends(get_db), username: str = Depends(verify_auth)):
    """Aggregate skill gaps across all tracked jobs vs. the candidate profile."""
    jobs = db.query(models.Job).all()
    try:
        return gap_analyzer.analyze_gaps(jobs)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== FILE UPLOAD ENDPOINT ====================

@app.post("/upload-file")
async def upload_file(file: UploadFile = File(...), username: str = Depends(verify_auth)):
    """
    Upload a file (CV, cover letter, or other document)
    Returns the file path that can be stored in the database
    """
    try:
        # Generate unique filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename

        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        # Return relative path for database storage
        return {
            "success": True,
            "filename": file.filename,
            "path": f"uploads/{unique_filename}",
            "url": f"/uploads/{unique_filename}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

@app.delete("/delete-file/{filename}")
async def delete_file(filename: str, username: str = Depends(verify_auth)):
    """Delete an uploaded file"""
    try:
        file_path = UPLOAD_DIR / filename
        if file_path.exists():
            file_path.unlink()
            return {"success": True, "message": "File deleted"}
        else:
            raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File deletion failed: {str(e)}")

# ==================== CRUD ENDPOINTS ====================

# CREATE
@app.post("/jobs", response_model=schemas.JobResponse, status_code=201)
def create_job(job: schemas.JobCreate, db: Session = Depends(get_db), username: str = Depends(verify_auth)):
    """Create a new job application. Returns 409 if the job is already tracked."""
    existing = crud.find_duplicate_job(db=db, url=job.url, role=job.role, company=job.company)
    if existing:
        raise HTTPException(
            status_code=409,
            detail={
                "message": f"Already tracked: {existing.role} at {existing.company} (job #{existing.id})",
                "existing_job_id": existing.id,
            },
        )
    return crud.create_job(db=db, job=job)

# READ
@app.get("/jobs", response_model=List[schemas.JobResponse])
def read_jobs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    status: Optional[ApplicationStatus] = Query(None, description="Filter by application status"),
    company: Optional[str] = Query(None, description="Filter by company name (partial match)"),
    db: Session = Depends(get_db),
    username: str = Depends(verify_auth)
):
    """Get all job applications with optional filters"""
    if status:
        return crud.get_jobs_by_status(db=db, status=status, skip=skip, limit=limit)
    elif company:
        return crud.get_jobs_by_company(db=db, company=company, skip=skip, limit=limit)
    else:
        return crud.get_jobs(db=db, skip=skip, limit=limit)

@app.get("/jobs/{job_id}", response_model=schemas.JobResponse)
def read_job(job_id: int, db: Session = Depends(get_db), username: str = Depends(verify_auth)):
    """Get a specific job application by ID"""
    db_job = crud.get_job(db=db, job_id=job_id)
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return db_job

# UPDATE
@app.put("/jobs/{job_id}", response_model=schemas.JobResponse)
def update_job(job_id: int, job: schemas.JobUpdate, db: Session = Depends(get_db), username: str = Depends(verify_auth)):
    """Update an existing job application"""
    db_job = crud.update_job(db=db, job_id=job_id, job_update=job)
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return db_job

# DELETE
@app.delete("/jobs/{job_id}", status_code=204)
def delete_job(job_id: int, db: Session = Depends(get_db), username: str = Depends(verify_auth)):
    """Delete a job application"""
    success = crud.delete_job(db=db, job_id=job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    return None


# ==================== CV BLOCK MATCHING ENDPOINT ====================

class BlockMatchResponse(BaseModel):
    block_id: str
    block_text: str
    company: str
    strength: str
    relevance_score: int
    match_reason: str

class MatchBlocksResponse(BaseModel):
    success: bool
    matches: List[BlockMatchResponse]
    error: Optional[str] = None

@app.get("/jobs/{job_id}/match-cv-blocks", response_model=MatchBlocksResponse)
def match_cv_blocks(
    job_id: int,
    max_blocks: int = Query(10, ge=1, le=20, description="Maximum number of blocks to return"),
    db: Session = Depends(get_db),
    username: str = Depends(verify_auth)
):
    """
    Match relevant CV experience blocks to a specific job posting

    Uses AI to analyze job requirements and select the most relevant
    CV bullet points from the pre-defined lego blocks library.

    Returns blocks ranked by relevance with reasoning for each match.
    """
    try:
        # Fetch the job from database
        db_job = crud.get_job(db=db, job_id=job_id)
        if db_job is None:
            raise HTTPException(status_code=404, detail="Job not found")

        # Get the matcher instance
        matcher = get_matcher()

        # Match blocks for this job
        matches = matcher.match_blocks_for_job(
            job_title=db_job.role or "Software Engineer",
            company=db_job.company or "Unknown Company",
            skills=db_job.parsed_skills or [],
            requirements=db_job.parsed_requirements or [],
            responsibilities=db_job.parsed_responsibilities or [],
            max_blocks=max_blocks
        )

        # Convert to response format
        match_responses = [
            BlockMatchResponse(
                block_id=match.block.id,
                block_text=match.block.text,
                company=match.block.company,
                strength=match.block.strength,
                relevance_score=match.relevance_score,
                match_reason=match.match_reason
            )
            for match in matches
        ]

        return MatchBlocksResponse(
            success=True,
            matches=match_responses
        )

    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        return MatchBlocksResponse(
            success=False,
            matches=[],
            error=f"Failed to match CV blocks: {str(e)}"
        )


# ==================== SALARY CALCULATION ENDPOINT ====================

@app.post("/calculate-salary", response_model=schemas.SalaryCalculationResponse)
def calculate_salary(request: schemas.SalaryCalculationRequest, username: str = Depends(verify_auth)):
    """Calculate net salary with tax, NI, student loan, and pension deductions."""
    try:
        from tax_calculator import TaxCalculator
        from decimal import Decimal

        calculator = TaxCalculator()
        breakdown = calculator.calculate_net_salary(
            gross=Decimal(str(request.gross_yearly)),
            pension_pct=Decimal(str(request.pension_pct)),
            include_student_loan=request.include_student_loan,
            student_loan_plan=request.student_loan_plan
        )

        return schemas.SalaryCalculationResponse(
            gross_yearly=float(breakdown["gross_yearly"]),
            gross_monthly=float(breakdown["gross_monthly"]),
            net_yearly=float(breakdown["net_yearly"]),
            net_monthly=float(breakdown["net_monthly"]),
            income_tax=float(breakdown["income_tax"]),
            national_insurance=float(breakdown["national_insurance"]),
            student_loan=float(breakdown["student_loan"]),
            pension=float(breakdown["pension"]),
            effective_tax_rate=float(breakdown["effective_tax_rate"]),
            tax_breakdown=schemas.TaxBreakdownResponse(**{
                k: float(v) for k, v in breakdown["tax_breakdown"].items()
            }),
            budget_recommendation=schemas.BudgetRecommendationResponse(**{
                k: float(v) for k, v in breakdown["budget_recommendation"].items()
            })
        )
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Tax calculator module not available. Please ensure tax_calculator.py is in the backend directory."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Salary calculation failed: {str(e)}")


# ==================== LEGO BLOCKS ENDPOINTS ====================

@app.get("/lego-blocks", response_model=List[schemas.LegoBlockResponse])
def get_lego_blocks(
    category: Optional[str] = Query(None, description="Filter by category"),
    skill: Optional[str] = Query(None, description="Filter by skill"),
    role_type: Optional[str] = Query(None, description="Filter by role type"),
    strength_level: Optional[int] = Query(None, ge=1, le=5, description="Filter by strength level"),
    db: Session = Depends(get_db),
    username: str = Depends(verify_auth)
):
    """Get all lego blocks with optional filters."""
    try:
        query = db.query(models.LegoBlock)

        if category:
            query = query.filter(models.LegoBlock.category == category)

        if skill:
            # Filter blocks that have the skill in their skills array
            query = query.filter(models.LegoBlock.skills.contains([skill]))

        if role_type:
            query = query.filter(models.LegoBlock.role_types.contains([role_type]))

        if strength_level:
            query = query.filter(models.LegoBlock.strength_level >= strength_level)

        blocks = query.all()
        return blocks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch lego blocks: {str(e)}")


@app.post("/lego-blocks/import", response_model=schemas.LegoBlockImportResponse)
def import_lego_blocks(db: Session = Depends(get_db), username: str = Depends(verify_auth)):
    """Import lego blocks from cv_lego_blocks_master.md file."""
    try:
        from lego_blocks import LegoBlockManager

        manager = LegoBlockManager()
        # Look for the file in parent directories
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        workspace_dir = os.path.dirname(os.path.dirname(current_dir))
        md_path = os.path.join(workspace_dir, "my-cv-app", "amazon evidence", "cv_lego_blocks_master.md")

        if not os.path.exists(md_path):
            raise HTTPException(
                status_code=404,
                detail=f"cv_lego_blocks_master.md not found at {md_path}"
            )

        blocks = manager.import_from_markdown(md_path)
        imported = 0
        skipped = 0

        for block_data in blocks:
            # Check if block already exists
            existing = db.query(models.LegoBlock).filter(
                models.LegoBlock.title == block_data["title"],
                models.LegoBlock.category == block_data["category"]
            ).first()

            if existing:
                skipped += 1
            else:
                new_block = models.LegoBlock(**block_data)
                db.add(new_block)
                imported += 1

        db.commit()

        return schemas.LegoBlockImportResponse(
            success=True,
            imported_count=imported,
            skipped_count=skipped,
            message=f"Imported {imported} blocks, skipped {skipped} duplicates"
        )
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Lego blocks module not available. Please ensure lego_blocks.py is in the backend directory."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


# ==================== CV GENERATION ENDPOINTS ====================

@app.get("/jobs/{job_id}/cv-suggestions", response_model=schemas.CVSuggestionsResponse)
def get_cv_suggestions(job_id: int, db: Session = Depends(get_db), username: str = Depends(verify_auth)):
    """Get suggested lego blocks for a job with relevance scores."""
    try:
        from cv_generator import cv_generator

        # Verify job exists
        job = db.query(models.Job).filter(models.Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Get ranked blocks
        ranked = cv_generator.rank_blocks(job_id, db)

        # Convert to response format
        suggestions = []
        for block_id, score in ranked:
            block = db.query(models.LegoBlock).filter(models.LegoBlock.id == block_id).first()
            if block:
                suggestions.append(
                    schemas.BlockSuggestion(
                        block_id=block_id,
                        block=schemas.LegoBlockResponse.from_orm(block),
                        relevance_score=score
                    )
                )

        return schemas.CVSuggestionsResponse(
            job_id=job_id,
            suggestions=suggestions
        )
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="CV generator module not available. Please ensure cv_generator.py is in the backend directory."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get CV suggestions: {str(e)}")


# Generation runs for several minutes (multiple LLM calls + LaTeX compile),
# far longer than proxy/browser timeouts, so the POST endpoints only start a
# background task and the frontend polls GET /generation-tasks/{task_id}.
# In-memory registry is fine for this single-process app; a restart just
# means the client re-requests generation.
generation_tasks: dict = {}


def _create_generation_task(kind: str) -> str:
    # Drop finished tasks older than an hour so the registry doesn't grow forever
    cutoff = time.time() - 3600
    for tid in [tid for tid, t in generation_tasks.items()
                if t["status"] != "running" and t["created_at"] < cutoff]:
        generation_tasks.pop(tid, None)

    task_id = str(uuid.uuid4())
    generation_tasks[task_id] = {
        "kind": kind,
        "status": "running",
        "error": None,
        "result": None,
        "created_at": time.time(),
    }
    return task_id


def _run_cv_generation(task_id: str, job_id: int, max_blocks: int):
    from cv_generator import cv_generator

    task = generation_tasks[task_id]
    db = SessionLocal()
    try:
        job = db.query(models.Job).filter(models.Job.id == job_id).first()
        selected_blocks = cv_generator.select_blocks(job_id, db, max_blocks=max_blocks)
        result = document_pipeline.generate_cv(job, selected_blocks)

        generated_cv = models.GeneratedCV(
            job_id=job_id,
            selected_blocks=[block.id for block in selected_blocks],
            customizations={},
            latex=result["latex"],
            pdf_path=result["pdf_path"],
        )
        db.add(generated_cv)
        db.commit()
        db.refresh(generated_cv)

        # Update job reference
        job.generated_cv_id = generated_cv.id
        job.cv = result["pdf_path"]
        db.commit()

        task["result"] = schemas.CVGenerationResponse(
            cv_id=generated_cv.id,
            selected_blocks=[schemas.LegoBlockResponse.from_orm(block) for block in selected_blocks],
            latex=result["latex"],
            pdf_path=result["pdf_path"],
            page_count=result["page_count"],
            checks=result["checks"],
        ).model_dump()
        task["status"] = "done"
    except Exception as e:
        db.rollback()
        logger.exception(f"CV generation task {task_id} failed")
        task["error"] = f"CV generation failed: {e}"
        task["status"] = "failed"
    finally:
        db.close()


def _run_cover_letter_generation(task_id: str, job_id: int, style: str):
    from cv_generator import cv_generator

    task = generation_tasks[task_id]
    db = SessionLocal()
    try:
        job = db.query(models.Job).filter(models.Job.id == job_id).first()
        # Reuse the CV block selection so the letter draws on the same evidence
        selected_blocks = cv_generator.select_blocks(job_id, db, max_blocks=5)
        result = document_pipeline.generate_cover_letter(job, selected_blocks)

        generated_letter = models.GeneratedCoverLetter(
            job_id=job_id,
            content=result["latex"],
            template_used=style,
            pdf_path=result["pdf_path"],
        )
        db.add(generated_letter)
        db.commit()
        db.refresh(generated_letter)

        # Update job reference
        job.generated_cover_letter_id = generated_letter.id
        job.cover_letter = result["pdf_path"]
        db.commit()

        task["result"] = schemas.CoverLetterGenerationResponse(
            letter_id=generated_letter.id,
            content=result["latex"],
            pdf_path=result["pdf_path"],
            page_count=result["page_count"],
            checks=result["checks"],
        ).model_dump()
        task["status"] = "done"
    except Exception as e:
        db.rollback()
        logger.exception(f"Cover letter generation task {task_id} failed")
        task["error"] = f"Cover letter generation failed: {e}"
        task["status"] = "failed"
    finally:
        db.close()


@app.post("/jobs/{job_id}/generate-cv", response_model=schemas.GenerationTaskCreated, status_code=202)
def generate_cv(
    job_id: int,
    request: schemas.CVGenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    username: str = Depends(verify_auth)
):
    """Start CV generation (draft -> review -> compile -> verify) as a background task."""
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    task_id = _create_generation_task("cv")
    background_tasks.add_task(_run_cv_generation, task_id, job_id, request.max_blocks)
    return schemas.GenerationTaskCreated(task_id=task_id)


@app.get("/generation-tasks/{task_id}", response_model=schemas.GenerationTaskStatus)
def get_generation_task(task_id: str, username: str = Depends(verify_auth)):
    """Poll the status of a CV / cover letter generation task."""
    task = generation_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Generation task not found (it may have expired or the server restarted)")
    return schemas.GenerationTaskStatus(
        task_id=task_id,
        kind=task["kind"],
        status=task["status"],
        error=task["error"],
        result=task["result"],
    )


@app.get("/jobs/{job_id}/generated-cv", response_model=schemas.CVGenerationResponse)
def get_generated_cv(job_id: int, db: Session = Depends(get_db), username: str = Depends(verify_auth)):
    """Return the most recently generated CV for this job, or 404 if none exists."""
    row = (
        db.query(models.GeneratedCV)
        .filter(models.GeneratedCV.job_id == job_id)
        .order_by(models.GeneratedCV.created_at.desc())
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="No generated CV found for this job")
    return schemas.CVGenerationResponse(
        cv_id=row.id,
        selected_blocks=[],
        latex=row.latex or "",
        pdf_path=row.pdf_path,
        page_count=None,
        checks=None,
    )


@app.get("/jobs/{job_id}/generated-cover-letter", response_model=schemas.CoverLetterGenerationResponse)
def get_generated_cover_letter(job_id: int, db: Session = Depends(get_db), username: str = Depends(verify_auth)):
    """Return the most recently generated cover letter for this job, or 404 if none exists."""
    row = (
        db.query(models.GeneratedCoverLetter)
        .filter(models.GeneratedCoverLetter.job_id == job_id)
        .order_by(models.GeneratedCoverLetter.created_at.desc())
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="No generated cover letter found for this job")
    return schemas.CoverLetterGenerationResponse(
        letter_id=row.id,
        content=row.content,
        pdf_path=row.pdf_path,
        page_count=None,
        checks=None,
    )


# ==================== COVER LETTER ENDPOINTS ====================

@app.post("/jobs/{job_id}/generate-cover-letter", response_model=schemas.GenerationTaskCreated, status_code=202)
def generate_cover_letter(
    job_id: int,
    request: schemas.CoverLetterGenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    username: str = Depends(verify_auth)
):
    """Start cover letter generation (draft -> review -> compile -> verify) as a background task."""
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    task_id = _create_generation_task("cover_letter")
    background_tasks.add_task(_run_cover_letter_generation, task_id, job_id, request.style)
    return schemas.GenerationTaskCreated(task_id=task_id)


@app.put("/generated-cover-letters/{letter_id}", response_model=schemas.CoverLetterGenerationResponse)
def update_cover_letter(
    letter_id: int,
    request: schemas.CoverLetterUpdateRequest,
    db: Session = Depends(get_db),
    username: str = Depends(verify_auth)
):
    """Update an existing cover letter based on user instructions."""
    try:
        from cover_letter_generator import cover_letter_generator

        # Get existing cover letter
        letter = db.query(models.GeneratedCoverLetter).filter(
            models.GeneratedCoverLetter.id == letter_id
        ).first()
        if not letter:
            raise HTTPException(status_code=404, detail="Cover letter not found")

        # Customize with instructions
        new_content = cover_letter_generator.customize(letter.content, request.instructions)

        # Recompile so the stored PDF matches the revised content
        page_count = None
        checks = None
        if "\\documentclass" in new_content:
            import time as _time
            stem = f"cover_letter_{letter.id}_{int(_time.time())}"
            try:
                _, pdf_path, page_count = latex_service.compile_tex(new_content, stem, "xelatex")
                letter.pdf_path = pdf_path
                checks = {"compiled": True, "page_count_ok": page_count == 1}
            except (latex_service.LatexCompileError, latex_service.LatexNotInstalled):
                checks = {"compiled": False, "page_count_ok": False}

        # Update in database
        letter.content = new_content
        db.commit()
        db.refresh(letter)

        return schemas.CoverLetterGenerationResponse(
            letter_id=letter.id,
            content=letter.content,
            pdf_path=letter.pdf_path,
            page_count=page_count,
            checks=checks,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Cover letter update failed: {str(e)}")


# ==================== CONTACT TRACKING ENDPOINTS ====================

@app.get("/jobs/{job_id}/contact-history", response_model=List[schemas.ContactHistoryResponse])
async def get_job_contact_history(job_id: int, db: Session = Depends(get_db), username: str = Depends(verify_auth)):
    """Get all contact history for a specific job"""
    # Verify job exists
    job = crud.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get contact history
    return crud.get_contact_history(db, job_id)


@app.post("/jobs/{job_id}/contact-history", response_model=schemas.ContactHistoryResponse, status_code=201)
async def record_contact(
    job_id: int,
    contact: schemas.ContactHistoryCreate,
    db: Session = Depends(get_db),
    username: str = Depends(verify_auth)
):
    """Record a new contact interaction with a recruiter"""
    # Verify job exists
    job = crud.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Create contact history record
    return crud.create_contact_history(db, job_id, contact)


@app.get("/jobs/{job_id}/generate-followup")
async def generate_followup_message(
    job_id: int,
    message_type: str = Query(default="email", regex="^(email|linkedin)$"),
    db: Session = Depends(get_db),
    username: str = Depends(verify_auth)
):
    """Generate a follow-up message for a job application"""
    # Get the job
    job = crud.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Generate the follow-up message
    return MessageGenerator.generate_followup(job, message_type)


@app.get("/jobs/{job_id}/staleness")
async def get_staleness(job_id: int, db: Session = Depends(get_db), username: str = Depends(verify_auth)):
    """Get staleness metrics for a job application"""
    # Get the job
    job = crud.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Calculate staleness
    staleness = crud.get_job_staleness(job)

    # Get contact history
    contacts = crud.get_contact_history(db, job_id)

    # Build response
    return {
        **staleness,
        'contact_count': len(contacts),
        'last_contact_date': contacts[0].contacted_at if contacts else None
    }