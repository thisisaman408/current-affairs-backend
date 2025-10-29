# src/schemas/content_schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class ContentItem(BaseModel):
    """Single content item (fact or question)"""
    id: int
    content_type: str
    exam_type: str
    title: str
    description: str
    explanation: Optional[str] = None
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    category: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    scheduled_time: Optional[str] = None  # IST timestamp for this item
    delivered_at: Optional[str]


class FetchDailyRequest(BaseModel):
    """Request to fetch content for a time period"""
    from_time: datetime = Field(..., description="Start time (IST)")
    to_time: datetime = Field(..., description="End time (IST)")
    notification_times: List[str] = Field(..., description="Notification times in HH:MM format", example=["09:00", "13:00", "18:00", "21:00"])
    daily_item_count: int = Field(default=3, ge=1, le=10, description="Items per notification")
    content_type_ratio: Dict[str, int] = Field(default={"fact": 85, "question": 15})
    exam_types: List[str] = Field(..., description="User's exam preferences")


class FetchDailyResponse(BaseModel):
    """Response with content for entire period"""
    success: bool
    items: List[ContentItem]
    metadata: Dict
    error: Optional[str] = None


class DailySyncResponse(BaseModel):
    """Legacy daily sync response"""
    success: bool
    content: List[ContentItem]
    metadata: Dict
    error: Optional[str] = None


class MarkDeliveredRequest(BaseModel):
    """Mark content as delivered"""
    question_ids: List[int]


class MarkDeliveredResponse(BaseModel):
    """Response after marking delivered"""
    success: bool
    message: str
    delivered_count: int
