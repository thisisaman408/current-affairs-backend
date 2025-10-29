"""
Admin API Routes
PDF upload and job management
"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List, cast
from datetime import date
from src.database.session import get_db
from src.schemas.admin_schemas import PDFUploadResponse, JobStatusResponse
from src.core.repositories.pdf_job_repository import PDFJobRepository
from src.core.services.pdf_service import PDFService
from src.api.middleware.auth_middleware import verify_admin_key
from src.integrations.redis_queue import redis_queue
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/upload-pdf", response_model=PDFUploadResponse)
async def upload_pdf(
    pdf: UploadFile = File(..., description="PDF file to upload"),
    exam_types: str = Form(..., description="Comma-separated exam types"),
    date_from: str = Form(..., description="Start date (YYYY-MM-DD)"),
    date_to: str = Form(..., description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_key)
):
    """
    Upload PDF for current affairs processing
    
    **Authentication:** Requires `X-Admin-API-Key` header
    
    **Example:**
    ```
    curl -X POST "http://localhost:8000/api/v1/admin/upload-pdf" \
      -H "X-Admin-API-Key: your-admin-key" \
      -F "pdf=@current_affairs.pdf" \
      -F "exam_types=UPSC,SSC" \
      -F "date_from=2025-10-01" \
      -F "date_to=2025-10-07"
    ```
    """
    # Parse exam types
    exam_list = [e.strip() for e in exam_types.split(",")]
    
    # Read file content
    file_content = await pdf.read()
    
    # Ensure filename is present and of type str
    if pdf.filename is None:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename")
    filename = pdf.filename

    # Initialize services
    pdf_repo = PDFJobRepository(db)
    pdf_service = PDFService(pdf_repo)
    
    # Upload PDF
    result = pdf_service.upload_pdf(
        file_content=file_content,
        filename=filename,
        exam_types=exam_list,
        date_from=date_from,
        date_to=date_to,
        uploaded_by="admin"  # Can be enhanced with Firebase auth later
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # Queue to Redis for processing
    queue_job = {
        "job_id": result["job_id"],
        "filename": filename,
        "r2_key": result.get("r2_key"),
        "exam_types": exam_list,
        "date_from": date_from,
        "date_to": date_to
    }
    redis_queue.push("pdf_processing_queue", queue_job)
    logger.info(f"📤 Upload request: {filename}, Exams: {exam_types}, Dates: {date_from} to {date_to}")
    
    return PDFUploadResponse(
        success=True,
        job_id=result["job_id"],
        message=f"PDF uploaded successfully! Job ID: {result['job_id']} queued for processing"
    )

@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_key)
):
    """
    Get PDF job status
    
    **Authentication:** Requires `X-Admin-API-Key` header
    """
    pdf_repo = PDFJobRepository(db)
    job = pdf_repo.get_by_id(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return JobStatusResponse(
        job_id=cast(int, job.id),
        status=str(job.status),
        filename=cast(str, job.filename),
        exam_types=cast(list[str], job.exam_types),
        date_from=cast(date, job.date_from),
        date_to=cast(date, job.date_to),
        created_at=cast(str, job.created_at.strftime("%d %b %Y, %I:%M %p")),
        total_questions_generated=cast(int, job.total_questions_generated),
        total_facts_generated=cast(int, job.total_facts_generated)
    )
