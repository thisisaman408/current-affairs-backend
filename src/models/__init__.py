"""
SQLAlchemy Models Package
Import all models here to ensure proper relationship resolution
"""

# Import base first
from src.models.base import BaseModel

# Import enums (needed by other models)
from src.models.user import SubscriptionStatus
from src.models.promo_code import PromoType
from src.models.delivery_log import NotificationStatus, notification_status_enum

# Import all models in dependency order
# (models with no foreign keys first, then those that depend on them)

# Independent models (no foreign keys to other models)
from src.models.subscription_plan import SubscriptionPlan
from src.models.promo_code import PromoCode
from src.models.pdf_job import PDFJob

# User model (referenced by many other models)
from src.models.user import User

# Models that depend on User
from src.models.user_preferences import UserPreferences
from src.models.device_token import DeviceToken
from src.models.subscription_history import SubscriptionHistory

# Question model (independent but referenced by DeliveryLog)
from src.models.question import Question

# DeliveryLog (depends on both User and Question)
from src.models.delivery_log import DeliveryLog

# Export all models and enums
__all__ = [
    # Base
    'BaseModel',
    
    # Enums
    'SubscriptionStatus',
    'PromoType',
    'NotificationStatus',
    'notification_status_enum',
    
    # Models (alphabetical for easy reference)
    'DeliveryLog',
    'DeviceToken',
    'PDFJob',
    'PromoCode',
    'Question',
    'SubscriptionHistory',
    'SubscriptionPlan',
    'User',
    'UserPreferences',
]
