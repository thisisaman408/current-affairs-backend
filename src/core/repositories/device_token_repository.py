"""
Device Token Repository - FCM Token Management
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from src.models.device_token import DeviceToken
from src.core.repositories.base_repository import BaseRepository
from datetime import datetime
from src.config import settings
import logging

logger = logging.getLogger(__name__)

class DeviceTokenRepository(BaseRepository[DeviceToken]):
    """Repository for FCM device tokens"""
    
    def __init__(self, db: Session):
        super().__init__(db, DeviceToken)
    
    def get_by_token(self, fcm_token: str) -> Optional[DeviceToken]:
        """Get device token by FCM token string"""
        return self.db.query(DeviceToken).filter(
            DeviceToken.fcm_token == fcm_token
        ).first()
    
    def create_or_update_token(
        self,
        user_id: int,
        fcm_token: str,
        platform: str,
        device_id: Optional[str] = None,
        device_name: Optional[str] = None,
        app_version: Optional[str] = None
    ) -> DeviceToken:
        """
        Create new token or update existing one
        Handles token reuse across users
        """
        existing = self.get_by_token(fcm_token)
        
        if existing:
            # Update existing token (may have changed user/device)
            self.db.query(DeviceToken).filter(
                DeviceToken.fcm_token == fcm_token
            ).update({
                "user_id": user_id,
                "platform": platform,
                "device_id": device_id,
                "device_name": device_name,
                "app_version": app_version,
                "is_active": True,
                "last_used_at": datetime.now(settings.IST)
            }, synchronize_session="fetch")
            self.db.commit()
            self.db.refresh(existing)
            logger.info(f"✅ FCM token updated for user {user_id}")
            return existing
        else:
            # Create new token
            token_data = {
                "user_id": user_id,
                "fcm_token": fcm_token,
                "platform": platform,
                "device_id": device_id,
                "device_name": device_name,
                "app_version": app_version,
                "is_active": True,
                "last_used_at": datetime.now(settings.IST)
            }
            token = self.create(token_data)
            logger.info(f"✅ New FCM token registered for user {user_id}")
            return token
    
    def deactivate_token(self, fcm_token: str) -> bool:
        """Mark token as inactive (user logged out or uninstalled)"""
        updated = self.db.query(DeviceToken).filter(
            DeviceToken.fcm_token == fcm_token
        ).update({"is_active": False}, synchronize_session="fetch")
        
        if updated:
            self.db.commit()
            logger.info(f"✅ FCM token deactivated: {fcm_token[:20]}...")
            return True
        return False
    
    def get_active_tokens_by_user(self, user_id: int) -> List[DeviceToken]:
        """Get all active tokens for a user"""
        return self.db.query(DeviceToken).filter(
            DeviceToken.user_id == user_id,
            DeviceToken.is_active == True
        ).all()
    
    def update_last_used(self, fcm_token: str) -> None:
        """Update last used timestamp (after successful notification)"""
        self.db.query(DeviceToken).filter(
            DeviceToken.fcm_token == fcm_token
        ).update({
            "last_used_at": datetime.now(settings.IST)
        }, synchronize_session="fetch")
        self.db.commit()
