"""
User Repository - Database Operations for Users
"""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from src.models.user import User
from src.core.repositories.base_repository import BaseRepository
from datetime import datetime
from src.config import settings
import logging

logger = logging.getLogger(__name__)

class UserRepository(BaseRepository[User]):
    """Repository for user CRUD operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, User)
    
    def get_by_firebase_uid(self, firebase_uid: str) -> Optional[User]:
        """Get user by Firebase UID"""
        return self.db.query(User).filter(User.firebase_uid == firebase_uid).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def create_user(
        self,
        firebase_uid: str,
        email: Optional[str] = None,
        display_name: Optional[str] = None,
        photo_url: Optional[str] = None,
        phone: Optional[str] = None
    ) -> User:
        """Create new user"""
        user_data = {
            "firebase_uid": firebase_uid,
            "email": email,
            "display_name": display_name,
            "photo_url": photo_url,
            "phone": phone,
            "is_active": True,
            "is_notification_enabled": True,
            "subscription_status": "free",
            "last_login_at": datetime.now(settings.IST)
        }
        
        user = self.create(user_data)
        logger.info(f"✅ User created: {user.email or user.firebase_uid}")
        return user
    
    def update_last_login(self, user_id: int) -> Optional[User]:
        """Update last login timestamp"""
        # Use a DB-level update to avoid assigning to a Column[...] attribute (type-checker issue)
        updated = self.db.query(User).filter(User.id == user_id).update({
            "last_login_at": datetime.now(settings.IST)
        }, synchronize_session="fetch")

        if updated:
            self.db.commit()
            user = self.get_by_id(user_id)
            if user:
                self.db.refresh(user)
            logger.info(f"✅ Updated last_login_at for user {user_id}")
            return user

        return None
    
    def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all active users with preferences"""
        return self.db.query(User).filter(
            User.is_active == True,
            User.is_notification_enabled == True
        ).options(
            joinedload(User.preferences),
            joinedload(User.device_tokens)
        ).offset(skip).limit(limit).all()
    
    def get_users_by_notification_time(self, time_str: str) -> List[User]:
        """
        Get users who have notifications scheduled at specific time
        Used by Celery hourly scheduler
        
        Args:
            time_str: Time in "HH:MM" format (IST)
        
        Returns:
            List of users with matching notification time
        """
        from src.models.user_preferences import UserPreferences
        
        return self.db.query(User).join(
            UserPreferences, User.id == UserPreferences.user_id
        ).filter(
            User.is_active == True,
            User.is_notification_enabled == True,
            UserPreferences.notification_times.contains([time_str])  # PostgreSQL array contains
        ).options(
            joinedload(User.preferences),
            joinedload(User.device_tokens)
        ).all()
    
    def upgrade_to_premium(self, user_id: int, expires_at: datetime) -> Optional[User]:
        """Upgrade user to premium subscription"""
        # Use a DB-level update to avoid static typing issues with ORM Column attributes
        updated = self.db.query(User).filter(User.id == user_id).update({
            "subscription_status": "premium",
            "subscription_expires_at": expires_at
        }, synchronize_session="fetch")

        if updated:
            self.db.commit()
            user = self.get_by_id(user_id)
            logger.info(f"✅ User {user_id} upgraded to premium")
            return user

        return None
