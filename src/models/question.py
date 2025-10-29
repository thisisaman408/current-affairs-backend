"""
Question/Fact Model - Stores both MCQs and facts
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from src.models.base import BaseModel
from typing import Optional


class Question(BaseModel):
    """Questions and Facts for daily delivery"""
    __tablename__ = "questions"
    
    # Content - for BOTH facts and questions
    text = Column(Text, nullable=False)  # Short text (backward compat)
    title = Column(String(500), nullable=True)  # Hindi title
    description = Column(Text, nullable=True)  # Detailed Hinglish description
    explanation = Column(Text, nullable=True)  # Explanation (for both)
    
    # MCQ-specific fields (NULL for facts)
    options = Column(JSON, nullable=True)  # ["A) option1", "B) option2", ...]
    correct_answer = Column(String(10), nullable=True)  # "A", "B", "C", "D"
    
    # Metadata
    content_type = Column(String(20), nullable=False)  # "fact" or "question"
    exam_type = Column(String(50), nullable=False)  # "UPSC", "SSC", etc.
    category = Column(String(100), nullable=True)  # "Polity", "Geography", etc.
    
    # Date range (when this content is relevant)
    date_from = Column(Date, nullable=False)
    date_to = Column(Date, nullable=False)
    
    # Source tracking
    source_pdf_id = Column(Integer, ForeignKey("pdf_jobs.id"), nullable=True)
    
    # Delivery tracking
    total_delivered = Column(Integer, default=0)
    last_delivered_at = Column(DateTime(timezone=True), nullable=True)
    
    # Quality control
    quality_score = Column(Integer, default=0)  # For future use
    
    def __repr__(self):
        return f"<Question {self.content_type} - {self.exam_type}>"
