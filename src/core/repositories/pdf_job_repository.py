"""
PDF Job Repository
Database operations for PDF jobs
"""
from typing import List, Optional, Any, cast
from sqlalchemy.orm import Session
from src.models.pdf_job import PDFJob
from src.core.repositories.base_repository import BaseRepository
from src.constants import JobStatus
import logging

logger = logging.getLogger(__name__)

class PDFJobRepository(BaseRepository[PDFJob]):
    """Repository for PDF job CRUD operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, PDFJob)
    
    def create_job(
        self,
        filename: str,
        r2_key: str,
        exam_types: List[str],
        date_from: str,
        date_to: str,
        uploaded_by: Optional[str] = None
    ) -> PDFJob:
        """
        Create new PDF job
        """
        job_data = {
            "filename": filename,
            "r2_key": r2_key,
            "exam_types": exam_types,
            "date_from": date_from,
            "date_to": date_to,
            "status": JobStatus.PENDING.value,
            "uploaded_by": uploaded_by
        }
        
        job = self.create(job_data)
        logger.info(f"✅ PDF job created: ID {job.id}, Exams: {exam_types}")
        return job
    
    def get_pending_jobs(self, limit: int = 10) -> List[PDFJob]:
        """Get pending jobs for processing"""
        return self.db.query(PDFJob)\
            .filter(PDFJob.status == JobStatus.PENDING.value)\
            .limit(limit)\
            .all()
    
    def update_status(
        self,
        job_id: int,
        status: str,
        error_message: Optional[str] = None
    ) -> Optional[PDFJob]:
        """Update job status"""
        job = self.get_by_id(job_id)
        if job:
            job.status = cast(Any, status)
            if error_message:
                job.error_message = cast(Any, error_message)
            self.db.commit()
            logger.info(f"✅ Job {job_id} status updated: {status}")
        return job
    
    def mark_processing(self, job_id: int) -> Optional[PDFJob]:
        """Mark job as processing"""
        from datetime import datetime
        from src.config import settings
        
        job = self.get_by_id(job_id)
        if job:
            job.status = cast(Any, JobStatus.PROCESSING.value)
            job.processing_started_at = cast(Any, datetime.now(settings.IST))
            self.db.commit()
            logger.info(f"✅ Job {job_id} marked as processing")
        return job
    
    def mark_completed(self, job_id: int, stats: dict) -> Optional[PDFJob]:
        """Mark job as completed with stats"""
        from datetime import datetime
        from src.config import settings
        
        job = self.get_by_id(job_id)
        if job:
            job.status = cast(Any, JobStatus.COMPLETED.value)
            job.processing_completed_at = cast(Any, datetime.now(settings.IST))
            job.total_questions_generated = stats.get('questions', 0)
            job.total_facts_generated = stats.get('facts', 0)
            self.db.commit()
            logger.info(f"✅ Job {job_id} completed: {stats}")
        return job
