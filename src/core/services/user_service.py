"""
User Service - Business Logic for User Management
"""
from typing import Optional, Dict, cast
from sqlalchemy.orm import Session
from src.core.services.base_service import BaseService
from src.core.repositories.user_repository import UserRepository
from src.core.repositories.preference_repository import PreferenceRepository
from src.core.repositories.device_token_repository import DeviceTokenRepository
from src.integrations.firebase_auth import firebase_auth_client
from src.models.user import User
from datetime import datetime
from src.config import settings
import logging

logger = logging.getLogger(__name__)

class UserService(BaseService):
    """Service for user registration and authentication"""
    
    def __init__(
        self,
        user_repo: UserRepository,
        preference_repo: PreferenceRepository,
        device_token_repo: DeviceTokenRepository
    ):
        super().__init__()
        self.user_repo = user_repo
        self.preference_repo = preference_repo
        self.device_token_repo = device_token_repo
    
    def register_or_login(self, firebase_token: str) -> Optional[Dict]:
        """
        Register new user or login existing user using Firebase token
        
        Args:
            firebase_token: Firebase ID token from mobile app
        
        Returns:
            User profile dict with preferences, or None if failed
        """
        # Verify Firebase token
        token_data = firebase_auth_client.verify_id_token(firebase_token)
        if not token_data:
            logger.error("❌ Firebase token verification failed")
            return None

        firebase_uid = token_data.get("uid")
        if not firebase_uid or not isinstance(firebase_uid, str):
            logger.error("❌ Firebase token missing or invalid uid")
            return None
        
        # Check if user exists
        user = self.user_repo.get_by_firebase_uid(firebase_uid)
        
        if user:
            # Existing user - sync profile details and update last login
            update_data = {
                "last_login_at": datetime.now(settings.IST)
            }
            name_from_token = token_data.get("name")
            picture_from_token = token_data.get("picture")

            if name_from_token and name_from_token != user.display_name:
                update_data["display_name"] = name_from_token
            if picture_from_token and picture_from_token != user.photo_url:
                update_data["photo_url"] = picture_from_token
            
            user = self.user_repo.update(cast(int, user.id), update_data)
            logger.info(f"✅ User logged in & profile synced: {getattr(user, 'email', 'unknown')}")
        else:
            # ✅ FIX: New user - Fetch full profile directly from Firebase to guarantee freshness
            logger.info("First time login, fetching full profile from Firebase...")
            firebase_user_profile = firebase_auth_client.get_user_by_uid(firebase_uid)

            if not firebase_user_profile:
                    raise Exception("Could not fetch Firebase user profile for new user.")

            user = self.user_repo.create_user(
                firebase_uid=firebase_uid,
                email=firebase_user_profile.get("email"),
                display_name=firebase_user_profile.get("display_name"),
                photo_url=firebase_user_profile.get("photo_url"),
                phone=firebase_user_profile.get("phone_number")
            )
            
            # Create default preferences
            self.preference_repo.create_default_preferences(cast(int, user.id))
            logger.info(f"✅ New user registered: {getattr(user, 'email', None) or getattr(user, 'firebase_uid', 'unknown')}")
        
        if not user:
            raise Exception("User could not be created or updated.")

        return self.get_user_profile(cast(int, user.id))
    
    def get_user_profile(self, user_id: int) -> Optional[Dict]:
        """
        Get complete user profile with preferences
        
        Args:
            user_id: User ID
        
        Returns:
            Profile dict with user info, preferences, device count
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return None
        
        preferences = self.preference_repo.get_by_user_id(user_id)
        device_count = len(self.device_token_repo.get_active_tokens_by_user(user_id))
        
        return {
            "user": {
                "id": user.id,
                "firebase_uid": user.firebase_uid,
                "email": user.email,
                "display_name": user.display_name,
                "photo_url": user.photo_url,
                "phone": user.phone,
                "is_active": user.is_active,
                "is_notification_enabled": user.is_notification_enabled,
                "subscription_status": user.subscription_status,
                "subscription_started_at": user.subscription_started_at.isoformat() if user.subscription_started_at is not None else None,
                "subscription_expires_at": user.subscription_expires_at.isoformat() if user.subscription_expires_at is not None else None,
                "last_login_at": user.last_login_at.isoformat() if user.last_login_at is not None else None,
                "created_at": user.created_at.isoformat()
            },
            "preferences": {
                "exam_types": preferences.exam_types if preferences else ["UPSC"],
                "notification_times": preferences.notification_times if preferences else ["09:00", "13:00", "18:00", "21:00"],
                "daily_item_count": preferences.daily_item_count if preferences else 3,
                "content_type_ratio": preferences.content_type_ratio if preferences else {"facts": 85, "questions": 15}
            },
            "device_count": device_count
        }
    
    def update_profile(
        self,
        user_id: int,
        display_name: Optional[str] = None,
        photo_url: Optional[str] = None,
        is_notification_enabled: Optional[bool] = None
    ) -> Optional[Dict]:
        """
        Update user profile fields
        
        Args:
            user_id: User ID
            display_name: New display name
            photo_url: New photo URL
            is_notification_enabled: Enable/disable notifications
        
        Returns:
            Updated profile or None
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return None
        
        update_data = {}
        if display_name is not None:
            update_data["display_name"] = display_name
        if photo_url is not None:
            update_data["photo_url"] = photo_url
        if is_notification_enabled is not None:
            update_data["is_notification_enabled"] = is_notification_enabled
        
        if update_data:
            user = self.user_repo.update(user_id, update_data)
            logger.info(f"✅ Profile updated for user {user_id}")
        
        return self.get_user_profile(user_id)
    
    def register_device(
        self,
        user_id: int,
        fcm_token: str,
        platform: str,
        device_id: Optional[str] = None,
        device_name: Optional[str] = None,
        app_version: Optional[str] = None
    ) -> Dict:
        """
        Register FCM device token for push notifications
        
        Args:
            user_id: User ID
            fcm_token: Firebase Cloud Messaging token
            platform: 'android' or 'ios'
            device_id: Optional device identifier
            device_name: Optional device name
            app_version: Optional app version
        
        Returns:
            Success status and device info
        """
        try:
            device = self.device_token_repo.create_or_update_token(
                user_id=user_id,
                fcm_token=fcm_token,
                platform=platform,
                device_id=device_id,
                device_name=device_name,
                app_version=app_version
            )
            
            return {
                "success": True,
                "device_id": device.id,
                "platform": device.platform,
                "message": "Device registered successfully"
            }
        except Exception as e:
            logger.error(f"❌ Device registration failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def unregister_device(self, fcm_token: str) -> bool:
        """Unregister device (logout or app uninstall)"""
        return self.device_token_repo.deactivate_token(fcm_token)
