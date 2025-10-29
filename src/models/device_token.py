"""
Device Token Model - FCM Push Notification Tokens
"""
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from src.models.base import BaseModel

class DeviceToken(BaseModel):
    """FCM device tokens for push notifications"""
    __tablename__ = "device_tokens"
    
    # Foreign key to users
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    user = relationship("User", back_populates="device_tokens")
    
    # FCM token (unique per device)
    fcm_token = Column(String(500), nullable=False, unique=True, index=True)
    
    # Device metadata
    platform = Column(String(20), nullable=False)  
    device_id = Column(String(255), nullable=True)
    device_name = Column(String(255), nullable=True) 
    app_version = Column(String(50), nullable=True)   
    
    # Token validity
    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<DeviceToken {self.platform} - {self.device_name}>"
