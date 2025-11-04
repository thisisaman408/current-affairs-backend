"""
User Preferences Repository
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from src.models.user_preferences import UserPreferences
from src.core.repositories.base_repository import BaseRepository
import logging

logger = logging.getLogger(__name__)

class PreferenceRepository(BaseRepository[UserPreferences]):
    """Repository for user preferences CRUD"""
    
    def __init__(self, db: Session):
        super().__init__(db, UserPreferences)
    
    def get_by_user_id(self, user_id: int) -> Optional[UserPreferences]:
        """Get preferences by user ID"""
        return self.db.query(UserPreferences).filter(
            UserPreferences.user_id == user_id
        ).first()
    
    def create_default_preferences(self, user_id: int) -> UserPreferences:
        """Create default preferences for new user"""
        prefs_data = {
            "user_id": user_id,
            "exam_types": ['General'],
            "notification_times": ["09:00", "13:00", "18:00", "21:00"],
            "daily_item_count": 3,
            "content_type_ratio": {"facts": 85, "questions": 15}
        }
        
        prefs = self.create(prefs_data)
        logger.info(f"✅ Default preferences created for user {user_id}")
        return prefs
    
    def update_preferences(
        self, 
        user_id: int, 
        exam_types: Optional[List[str]] = None,
        notification_times: Optional[List[str]] = None,
        daily_item_count: Optional[int] = None,
        content_type_ratio: Optional[dict] = None
    ) -> Optional[UserPreferences]:
        """Update user preferences"""
        prefs = self.get_by_user_id(user_id)
        if not prefs:
            logger.error(f"❌ Preferences not found for user {user_id}")
            return None
        
        # Build update dict
        update_data = {}
        if exam_types is not None:
            update_data["exam_types"] = exam_types
        if notification_times is not None:
            update_data["notification_times"] = notification_times
        if daily_item_count is not None:
            update_data["daily_item_count"] = daily_item_count
        if content_type_ratio is not None:
            logger.warning(f"⚠️ User {user_id} tried to change content_type_ratio. BLOCKED.")
        
        # Update via query (type-safe)
        if update_data:
            self.db.query(UserPreferences).filter(
                UserPreferences.user_id == user_id
            ).update(update_data, synchronize_session="fetch")
            self.db.commit()
            
            # Refresh object
            self.db.refresh(prefs)
            logger.info(f"✅ Preferences updated for user {user_id}")
        
        return prefs
    
    def validate_notification_times(self, times: List[str], is_premium: bool) -> tuple[bool, Optional[str]]:
        """
        Validate notification times format and count
        
        Returns:
            (is_valid, error_message)
        """
        if not times:
            return False, "At least one notification time required"
        
        # Check count based on subscription
        max_times = float('inf') if is_premium else 4
        if len(times) > max_times:
            return False, f"Free users limited to 4 notification times"
        
        # Validate format HH:MM
        for time_str in times:
            try:
                parts = time_str.split(':')
                if len(parts) != 2:
                    return False, f"Invalid time format: {time_str}"
                
                hour, minute = int(parts[0]), int(parts[1])
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    return False, f"Invalid time values: {time_str}"
            except (ValueError, AttributeError):
                return False, f"Time must be in HH:MM format: {time_str}"
        
        return True, None


    def update_notification_times(self, user_id: int, notification_times: List[str]) -> Optional[UserPreferences]:
        """Update ONLY notification_times field"""
        prefs = self.db.query(UserPreferences).filter(
            UserPreferences.user_id == user_id
        ).first()
        
        if not prefs:
            return None
        
        prefs.notification_times = notification_times
        self.db.commit()
        self.db.refresh(prefs)
        
        return prefs