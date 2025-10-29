"""
User Profile & Preferences API Routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database.session import get_db
from src.schemas.user_schemas import (
    CompleteProfileResponse,
    UpdateProfileRequest,
    UpdatePreferencesRequest,
    UpdatePreferencesResponse
)
from src.core.repositories.user_repository import UserRepository
from src.core.repositories.preference_repository import PreferenceRepository
from src.core.repositories.device_token_repository import DeviceTokenRepository
from src.core.services.user_service import UserService
from src.api.dependencies import get_current_user
from src.models.user import User
from typing import cast
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["user"])

@router.get("/profile", response_model=CompleteProfileResponse)
async def get_profile(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get complete user profile with preferences
    
    Returns:
    - User account info
    - Notification preferences
    - Device count
    """
    user_repo = UserRepository(db)
    preference_repo = PreferenceRepository(db)
    device_token_repo = DeviceTokenRepository(db)
    user_service = UserService(user_repo, preference_repo, device_token_repo)
    
    profile = user_service.get_user_profile(cast(int, user.id))
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return profile

@router.put("/profile")
async def update_profile(
    request: UpdateProfileRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user profile information
    
    - Display name
    - Photo URL
    - Notification enabled/disabled
    """
    user_repo = UserRepository(db)
    preference_repo = PreferenceRepository(db)
    device_token_repo = DeviceTokenRepository(db)
    
    user_service = UserService(user_repo, preference_repo, device_token_repo)
    
    profile = user_service.update_profile(
        user_id=cast(int, user.id),
        display_name=request.display_name,
        photo_url=request.photo_url,
        is_notification_enabled=request.is_notification_enabled
    )
    
    if not profile:
        raise HTTPException(status_code=400, detail="Profile update failed")
    
    return {
        "success": True,
        "message": "Profile updated successfully",
        "profile": profile
    }

@router.put("/preferences", response_model=UpdatePreferencesResponse)
async def update_preferences(
    request: UpdatePreferencesRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update notification preferences
    
    - Exam types (UPSC, SSC, etc.)
    - Notification times (IST)
    - Daily item count
    - Content ratio (facts vs questions)
    
    Free tier limits:
    - Max 4 notification times
    - Max 3 items per day
    
    Premium tier:
    - Unlimited notification times
    - Up to 10 items per day
    """
    preference_repo = PreferenceRepository(db)
    
    # Check subscription limits for notification times
    if request.notification_times:
        is_premium = user.is_premium
        is_valid, error_msg = preference_repo.validate_notification_times(
            request.notification_times,
            is_premium
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid notification times: {error_msg}"
            )
    
    # Update preferences
    preferences = preference_repo.update_preferences(
        user_id=cast(int, user.id),
        exam_types=request.exam_types,
        notification_times=request.notification_times,
        daily_item_count=request.daily_item_count,
        content_type_ratio=request.content_type_ratio
    )
    
    if not preferences:
        raise HTTPException(
            status_code=404,
            detail="Preferences not found"
        )
    
    return {
        "success": True,
        "preferences": {
            "exam_types": preferences.exam_types,
            "notification_times": preferences.notification_times,
            "daily_item_count": preferences.daily_item_count,
            "content_type_ratio": preferences.content_type_ratio
        },
        "message": "Preferences updated successfully"
    }

@router.get("/preferences")
async def get_preferences(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current notification preferences
    """
    preference_repo = PreferenceRepository(db)
    preferences = preference_repo.get_by_user_id(cast(int, user.id))
    
    if not preferences:
        raise HTTPException(
            status_code=404,
            detail="Preferences not found"
        )
    
    return {
        "exam_types": preferences.exam_types,
        "notification_times": preferences.notification_times,
        "daily_item_count": preferences.daily_item_count,
        "content_type_ratio": preferences.content_type_ratio
    }

@router.get("/devices")
async def get_devices(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all registered devices for this user
    """
    device_token_repo = DeviceTokenRepository(db)
    devices = device_token_repo.get_active_tokens_by_user(cast(int, user.id))
    
    return {
        "devices": [
            {
                "id": device.id,
                "platform": device.platform,
                "device_name": device.device_name or "Unknown Device",
                "app_version": device.app_version,
                "last_used_at": device.last_used_at.isoformat() if device.last_used_at is not None else None,
                "created_at": device.created_at.isoformat()
            }
            for device in devices
        ],
        "total": len(devices)
    }
