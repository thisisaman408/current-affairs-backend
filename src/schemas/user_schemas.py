"""
User API Schemas - Request/Response Models
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime

# ========== AUTH SCHEMAS ==========

class FirebaseLoginRequest(BaseModel):
    """Firebase login request"""
    firebase_token: str = Field(..., description="Firebase ID token from mobile app")
class LogoutRequest(BaseModel):
    """Logout request"""
    fcm_token: str = Field(..., description="FCM token of the device to deactivate")

class DeviceRegistrationRequest(BaseModel):
    """Register device for push notifications"""
    fcm_token: str = Field(..., description="Firebase Cloud Messaging token")
    platform: str = Field(..., description="Device platform: 'android' or 'ios'")
    device_id: Optional[str] = Field(None, description="Device unique identifier")
    device_name: Optional[str] = Field(None, description="Device name (e.g., 'Pixel 7')")
    app_version: Optional[str] = Field(None, description="App version (e.g., '1.0.5')")
    
    @validator('platform')
    def validate_platform(cls, v):
        if v not in ['android', 'ios']:
            raise ValueError("Platform must be 'android' or 'ios'")
        return v

class DeviceRegistrationResponse(BaseModel):
    """Device registration response"""
    success: bool
    device_id: Optional[int] = None
    platform: Optional[str] = None
    message: str

# ========== USER PROFILE SCHEMAS ==========

class UserProfileResponse(BaseModel):
    """User profile response"""
    id: int
    firebase_uid: str
    email: Optional[str]
    display_name: Optional[str]
    photo_url: Optional[str]
    phone: Optional[str]
    is_active: bool
    is_notification_enabled: bool
    subscription_status: str
    subscription_started_at: Optional[str]
    subscription_expires_at: Optional[str]
    last_login_at: Optional[str]
    created_at: str

class UserPreferencesResponse(BaseModel):
    """User preferences response"""
    exam_types: List[str]
    notification_times: List[str]
    daily_item_count: int
    content_type_ratio: Dict[str, int]

class CompleteProfileResponse(BaseModel):
    """Complete user profile with preferences"""
    user: UserProfileResponse
    preferences: UserPreferencesResponse
    device_count: int

class UpdateProfileRequest(BaseModel):
    """Update user profile"""
    display_name: Optional[str] = Field(None, max_length=255)
    photo_url: Optional[str] = Field(None, max_length=500)
    is_notification_enabled: Optional[bool] = None

# ========== PREFERENCES SCHEMAS ==========

class UpdatePreferencesRequest(BaseModel):
    """Update user preferences"""
    exam_types: Optional[List[str]] = Field(None, description="Exam types: General,UPSC, SSC, Banking, Railway, Defence")
    notification_times: Optional[List[str]] = Field(None, description="Times in HH:MM format (IST)")
    daily_item_count: Optional[int] = Field(None, ge=1, le=10, description="Items per notification (1-10)")
    content_type_ratio: Optional[Dict[str, int]] = Field(None, description="Facts/Questions ratio")
    
    @validator('exam_types')
    def validate_exam_types(cls, v):
        if v is not None:
            valid_exams = ["General","UPSC", "SSC", "Banking", "Railway", "Defence"]
            for exam in v:
                if exam not in valid_exams:
                    raise ValueError(f"Invalid exam type: {exam}. Valid: {valid_exams}")
        return v
    
    @validator('notification_times')
    def validate_times(cls, v):
        if v is not None:
            for time_str in v:
                try:
                    parts = time_str.split(':')
                    if len(parts) != 2:
                        raise ValueError()
                    hour, minute = int(parts[0]), int(parts[1])
                    if not (0 <= hour <= 23 and 0 <= minute <= 59):
                        raise ValueError()
                except (ValueError, AttributeError):
                    raise ValueError(f"Time must be in HH:MM format: {time_str}")
        return v
    
    @validator('content_type_ratio')
    def validate_ratio(cls, v):
        if v is not None:
            if 'facts' not in v or 'questions' not in v:
                raise ValueError("Ratio must include 'facts' and 'questions' keys")
            total = v['facts'] + v['questions']
            if total != 100:
                raise ValueError("Facts + Questions must equal 100")
        return v
    @validator('daily_item_count')
    def validate_item_count(cls, v, values):
        # TODO: Get user subscription from database
        # For now, allow up to 10 (will enforce in service layer)
        if not (1 <= v <= 10):
            raise ValueError("daily_item_count must be between 1 and 10")
        return v


class UpdatePreferencesResponse(BaseModel):
    """Preferences update response"""
    success: bool
    preferences: UserPreferencesResponse
    message: str
