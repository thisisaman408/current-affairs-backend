"""
PDF Job Model
"""
from sqlalchemy import Column, String, Date, DateTime, Text, Integer
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from src.models.base import BaseModel

class PDFJob(BaseModel):
    """PDF upload and processing jobs"""
    __tablename__ = "pdf_jobs"
    
    # File info
    filename = Column(String(255), nullable=False)
    r2_key = Column(String(500), nullable=False)  # Path in R2
    
    # Exam types (PostgreSQL array)
    exam_types = Column(ARRAY(String), nullable=False)
    
    # Date range (IST dates)
    date_from = Column(Date, nullable=False)
    date_to = Column(Date, nullable=False)
    
    # Status: pending/processing/completed/failed
    status = Column(String(20), default="pending", nullable=False)
    
    # Admin who uploaded
    uploaded_by = Column(String(255), nullable=True)
    
    # Processing timestamps
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Extracted JSON from PDF
    extracted_content = Column(JSONB, nullable=True)
    
    # Stats
    total_questions_generated = Column(Integer, default=0)
    total_facts_generated = Column(Integer, default=0)
