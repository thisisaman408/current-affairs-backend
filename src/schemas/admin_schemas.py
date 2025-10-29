"""
Admin API Schemas (Pydantic models)
"""
from pydantic import BaseModel, Field
from typing import List
from datetime import date

class PDFUploadRequest(BaseModel):
    """Request schema for PDF upload"""
    exam_types: List[str] = Field(..., description="List of exam types")
    date_from: str = Field(..., description="Start date (YYYY-MM-DD)")
    date_to: str = Field(..., description="End date (YYYY-MM-DD)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "exam_types": ["UPSC", "SSC"],
                "date_from": "2025-10-01",
                "date_to": "2025-10-07"
            }
        }

class PDFUploadResponse(BaseModel):
    """Response schema for PDF upload"""
    success: bool
    job_id: int | None
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "job_id": 123,
                "message": "PDF uploaded successfully and queued for processing"
            }
        }

class JobStatusResponse(BaseModel):
    """Job status response"""
    job_id: int
    status: str
    filename: str
    exam_types: List[str]
    date_from: date
    date_to: date
    created_at: str
    total_questions_generated: int | None = None
    total_facts_generated: int | None = None
