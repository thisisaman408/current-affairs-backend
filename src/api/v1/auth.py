"""
Authentication API Routes
User registration, login, device management
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database.session import get_db
from src.schemas.user_schemas import (
    FirebaseLoginRequest,
    CompleteProfileResponse,
    DeviceRegistrationRequest,
    DeviceRegistrationResponse,
    LogoutRequest
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

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/login", response_model=CompleteProfileResponse)
async def login(
    request: FirebaseLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login or register user with Firebase token
    
    - Verifies Firebase ID token
    - Creates new user if first time login
    - Returns user profile with preferences
    """
    # Initialize repositories and service
    user_repo = UserRepository(db)
    preference_repo = PreferenceRepository(db)
    device_token_repo = DeviceTokenRepository(db)
    
    user_service = UserService(user_repo, preference_repo, device_token_repo)
    
    # Register or login
    profile = user_service.register_or_login(request.firebase_token)
    
    if not profile:
        raise HTTPException(
            status_code=401,
            detail="Firebase authentication failed"
        )
    
    return profile

@router.post("/register-device", response_model=DeviceRegistrationResponse)
async def register_device(
    request: DeviceRegistrationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Register device for push notifications
    
    - Stores FCM token
    - Handles token updates if device changes
    - Required for receiving notifications
    """
    device_token_repo = DeviceTokenRepository(db)
    user_repo = UserRepository(db)
    preference_repo = PreferenceRepository(db)
    
    user_service = UserService(user_repo, preference_repo, device_token_repo)
    result = user_service.register_device(
        user_id=cast(int, user.id),
        fcm_token=request.fcm_token,
        platform=request.platform,
        device_id=request.device_id,
        device_name=request.device_name,
        app_version=request.app_version
    )
    
    
    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Device registration failed")
        )
    
    return result

@router.post("/logout")
async def logout(
    request: LogoutRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout user - deactivates device token
    
    - Stops push notifications to this device
    - User remains logged in on other devices
    """
    device_token_repo = DeviceTokenRepository(db)
    success = device_token_repo.deactivate_token(request.fcm_token)
    
    return {
        "success": success,
        "message": "Logged out successfully" if success else "Device token not found"
    }
