"""
PDF Service
Business logic for PDF upload and processing
"""
from typing import List, BinaryIO, Optional, cast
from src.core.services.base_service import BaseService
from src.core.repositories.pdf_job_repository import PDFJobRepository
from src.integrations.r2_storage import r2_storage
from src.config import settings
import logging

logger = logging.getLogger(__name__)

class PDFService(BaseService):
    """Service for PDF operations"""
    
    def __init__(self, pdf_job_repo: PDFJobRepository):
        super().__init__()
        self.pdf_job_repo = pdf_job_repo
    
    def validate_pdf(self, file_content: bytes, filename: str) -> dict:
        """
        Validate PDF file
        Returns: {"valid": bool, "error": str}
        """
        # Check file extension
        if not filename.lower().endswith('.pdf'):
            return {"valid": False, "error": "File must be a PDF"}
        
        # Check file size (in MB)
        file_size_mb = len(file_content) / (1024 * 1024)
        if file_size_mb > settings.PDF_MAX_SIZE_MB:
            return {
                "valid": False,
                "error": f"File too large. Max size: {settings.PDF_MAX_SIZE_MB}MB"
            }
        
        # Check if it's actually a PDF (magic bytes)
        if not file_content.startswith(b'%PDF'):
            return {"valid": False, "error": "Invalid PDF file"}
        
        logger.info(f"✅ PDF validation passed: {filename} ({file_size_mb:.2f}MB)")
        return {"valid": True, "error": None}
    
    def validate_exam_types(self, exam_types: List[str]) -> dict:
        """
        Validate exam types
        """
        allowed_exams = settings.get_allowed_exams
        
        if not exam_types:
            return {"valid": False, "error": "At least one exam type required"}
        
        for exam in exam_types:
            if exam not in allowed_exams:
                return {
                    "valid": False,
                    "error": f"Invalid exam type: {exam}. Allowed: {', '.join(allowed_exams)}"
                }
        
        logger.info(f"✅ Exam types validated: {exam_types}")
        return {"valid": True, "error": None}
    
    def upload_pdf(
        self,
        file_content: bytes,
        filename: str,
        exam_types: List[str],
        date_from: str,
        date_to: str,
        uploaded_by: Optional[str] = None
    ) -> dict:
        """
        Main upload flow:
        1. Validate PDF
        2. Validate exams
        3. Upload to R2
        4. Create database entry
        5. Queue for processing
        
        Returns: {"success": bool, "job_id": int, "error": str}
        """
        
        # Step 1: Validate PDF
        pdf_validation = self.validate_pdf(file_content, filename)
        if not pdf_validation["valid"]:
            return {"success": False, "job_id": None, "error": pdf_validation["error"]}
        
        # Step 2: Validate exam types
        exam_validation = self.validate_exam_types(exam_types)
        if not exam_validation["valid"]:
            return {"success": False, "job_id": None, "error": exam_validation["error"]}
        
        try:
            # Step 3: Create database entry first (to get job_id)
            job = self.pdf_job_repo.create_job(
                filename=filename,
                r2_key="temp",  # Temporary, will update
                exam_types=exam_types,
                date_from=date_from,
                date_to=date_to,
                uploaded_by=uploaded_by
            )
            
            # Step 4: Upload to R2 with job_id (cast to int to satisfy type checker)
            r2_key = r2_storage.upload_pdf(file_content, cast(int, job.id), filename)
            # Update R2 key in database (use setattr to avoid assigning to Column descriptor)
            setattr(job, "r2_key", r2_key)
            self.pdf_job_repo.db.commit()
            
            logger.info(f"✅ PDF upload successful: Job ID {job.id}")
            
            return {
                "success": True,
                "job_id": job.id,
                "error": None,
                "r2_key": r2_key
            }
            
        except Exception as e:
            logger.error(f"❌ PDF upload failed: {str(e)}")
            return {
                "success": False,
                "job_id": None,
                "error": f"Upload failed: {str(e)}"
            }
