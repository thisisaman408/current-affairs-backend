"""
User Model - Firebase Authentication Sync
"""
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from src.models.base import BaseModel
import enum
from datetime import datetime
from typing import cast
from src.utils.timezone_utils import now_ist

class SubscriptionStatus(str, enum.Enum):
    """User subscription tiers"""
    FREE = "free"
    PREMIUM = "premium"
    TRIAL = "trial"


class User(BaseModel):
    """User accounts synced with Firebase Auth"""
    __tablename__ = "users"
    
    # Firebase UID (primary identifier from Firebase Auth)
    firebase_uid = Column(String(255), unique=True, nullable=False, index=True)
    
    # Contact info
    email = Column(String(255), nullable=True, unique=True, index=True)
    phone = Column(String(20), nullable=True)
    
    # Profile
    display_name = Column(String(255), nullable=True)
    photo_url = Column(String(500), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_notification_enabled = Column(Boolean, default=True, nullable=False)
    
    # Subscription
    subscription_status = Column(
        String,
        default=SubscriptionStatus.FREE.value,
        nullable=False
    )
    subscription_expires_at = Column(DateTime(timezone=True), nullable=True)
    subscription_started_at = Column(DateTime(timezone=True), nullable=True)
    
    # Activity tracking (IST)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    device_tokens = relationship("DeviceToken", back_populates="user", cascade="all, delete-orphan")
    delivery_logs = relationship("DeliveryLog", back_populates="user", cascade="all, delete-orphan")
    subscription_history = relationship("SubscriptionHistory", back_populates="user", cascade="all, delete-orphan")
    
    @property
    def is_premium(self) -> bool:
        """Check if user has premium subscription"""
        # Check if subscription is PREMIUM or TRIAL (both get premium features)
        if self.subscription_status in (SubscriptionStatus.PREMIUM.value, SubscriptionStatus.TRIAL.value):
            # If trial/premium, check expiry (explicit None check avoids SQLAlchemy Column truthiness)
            if self.subscription_expires_at is not None:
                expires = cast(datetime, self.subscription_expires_at)
                # If it's not a runtime datetime (e.g. a SQLAlchemy expression), fall back safely.
                if not isinstance(expires, datetime):
                    return True
                return expires > now_ist()
            return True  # Premium without expiry (lifetime)
        return False
    
    def __repr__(self):
        return f"<User {self.email or self.firebase_uid}>"
