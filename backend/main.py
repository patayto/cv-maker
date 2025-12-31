from fastapi import FastAPI, Depends, HTTPException, Query, Body, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db, engine
from models import Base, ApplicationStatus
import models
import schemas
import crud
from job_parser import job_parser
from message_generator import MessageGenerator
from auth import verify_auth
from pydantic import BaseModel
import aiofiles
import os
from pathlib import Path
import uuid

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
    url: str
    use_llm: bool = True

class ParseUrlResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    missing_fields: List[str] = []
    error: Optional[str] = None

@app.post("/parse-job-url", response_model=ParseUrlResponse)
async def parse_job_url(request: ParseUrlRequest, username: str = Depends(verify_auth)):
    """
    Parse a job posting URL and extract job details.
    Uses web scraping and optionally Claude AI to extract information.
    """
    try:
        job_data, missing_fields = job_parser.parse_job_url(request.url, use_llm=request.use_llm)

        return ParseUrlResponse(
            success=True,
            data=job_data,
            missing_fields=missing_fields
        )
    except Exception as e:
        return ParseUrlResponse(
            success=False,
            error=str(e),
            missing_fields=[]
        )

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
    """Create a new job application"""
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


@app.post("/jobs/{job_id}/generate-cv", response_model=schemas.CVGenerationResponse)
def generate_cv(
    job_id: int,
    request: schemas.CVGenerationRequest,
    db: Session = Depends(get_db),
    username: str = Depends(verify_auth)
):
    """Generate a CV for a specific job by selecting top-ranked lego blocks."""
    try:
        from cv_generator import cv_generator

        # Verify job exists
        job = db.query(models.Job).filter(models.Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Select blocks
        selected_blocks = cv_generator.select_blocks(job_id, db, max_blocks=request.max_blocks)

        # Generate LaTeX
        latex = cv_generator.generate_latex(selected_blocks)

        # Save to database
        generated_cv = models.GeneratedCV(
            job_id=job_id,
            selected_blocks=[block.id for block in selected_blocks],
            customizations={}
        )
        db.add(generated_cv)
        db.commit()
        db.refresh(generated_cv)

        # Update job reference
        job.generated_cv_id = generated_cv.id
        db.commit()

        return schemas.CVGenerationResponse(
            cv_id=generated_cv.id,
            selected_blocks=[schemas.LegoBlockResponse.from_orm(block) for block in selected_blocks],
            latex=latex
        )
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="CV generator module not available. Please ensure cv_generator.py is in the backend directory."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"CV generation failed: {str(e)}")


# ==================== COVER LETTER ENDPOINTS ====================

@app.post("/jobs/{job_id}/generate-cover-letter", response_model=schemas.CoverLetterGenerationResponse)
def generate_cover_letter(
    job_id: int,
    request: schemas.CoverLetterGenerationRequest,
    db: Session = Depends(get_db),
    username: str = Depends(verify_auth)
):
    """Generate a cover letter for a specific job."""
    try:
        from cover_letter_generator import cover_letter_generator

        # Verify job exists
        job = db.query(models.Job).filter(models.Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Generate cover letter
        content = cover_letter_generator.generate(job_id, db, style=request.style)

        # Save to database
        generated_letter = models.GeneratedCoverLetter(
            job_id=job_id,
            content=content,
            template_used=request.style
        )
        db.add(generated_letter)
        db.commit()
        db.refresh(generated_letter)

        # Update job reference
        job.generated_cover_letter_id = generated_letter.id
        db.commit()

        return schemas.CoverLetterGenerationResponse(
            letter_id=generated_letter.id,
            content=content
        )
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Cover letter generator module not available. Please ensure cover_letter_generator.py is in the backend directory."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Cover letter generation failed: {str(e)}")


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

        # Update in database
        letter.content = new_content
        db.commit()
        db.refresh(letter)

        return schemas.CoverLetterGenerationResponse(
            letter_id=letter.id,
            content=letter.content
        )
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Cover letter generator module not available. Please ensure cover_letter_generator.py is in the backend directory."
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