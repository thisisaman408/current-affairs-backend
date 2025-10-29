"""
User Preferences - Notification Settings
"""
from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship, validates
from src.models.base import BaseModel
import logging

logger = logging.getLogger(__name__)

class UserPreferences(BaseModel):
    """User notification preferences and exam settings"""
    __tablename__ = "user_preferences"
    
    # Foreign key to users (one-to-one)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    user = relationship("User", back_populates="preferences")
    
    # Exam preferences (PostgreSQL array - multiple exams allowed)
    exam_types = Column(ARRAY(String), default=["UPSC"], nullable=False)
    
    # Notification times (IST hours in "HH:MM" format)
    # Free: max 4, Premium: unlimited
    notification_times = Column(
        ARRAY(String), 
        default=["09:00", "13:00", "18:00", "21:00"],
        nullable=False
    )
    
    # Items per notification (Free: max 3, Premium: up to 10)
    daily_item_count = Column(Integer, default=3, nullable=False)
    
    # Content distribution (JSONB for flexibility)
    content_type_ratio = Column(
        JSONB,
        default={"facts": 85, "questions": 15},
        nullable=False
    )
    
    @validates('notification_times')
    def validate_notification_count(self, key, value):
        """Validate notification times based on subscription tier"""
        if not value:
            raise ValueError("At least one notification time required")
        
        # Validate time format (HH:MM)
        for time_str in value:
            try:
                hour, minute = time_str.split(':')
                if not (0 <= int(hour) <= 23 and 0 <= int(minute) <= 59):
                    raise ValueError(f"Invalid time format: {time_str}")
            except (ValueError, AttributeError):
                raise ValueError(f"Time must be in HH:MM format: {time_str}")
        
        # Check subscription limits
        if hasattr(self, 'user') and self.user:
            is_premium = self.user.subscription_status == "premium"
            if not is_premium and len(value) > 4:
                raise ValueError("Free users limited to 4 notification times. Upgrade to Premium for unlimited!")
        
        return value
    
    @validates('daily_item_count')
    def validate_item_count(self, key, value):
        """Validate daily item count based on subscription"""
        if value < 1:
            raise ValueError("Daily item count must be at least 1")
        
        if hasattr(self, 'user') and self.user:
            is_premium = self.user.subscription_status == "premium"
            max_items = 10 if is_premium else 3
            if value > max_items:
                raise ValueError(f"Maximum {max_items} items per day for your subscription")
        
        return value
    
    @validates('exam_types')
    def validate_exam_types(self, key, value):
        """Ensure valid exam types"""
        if not value:
            raise ValueError("At least one exam type required")
        
        valid_exams = ["General","UPSC", "SSC", "Banking", "Railway", "Defence"]
        for exam in value:
            if exam not in valid_exams:
                raise ValueError(f"Invalid exam type: {exam}. Valid: {valid_exams}")
        
        return value
