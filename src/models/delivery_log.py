# backend/src/models/delivery_log.py
"""
Delivery Log Model - Track Notification History
"""
# Import Enum directly from sqlalchemy for casting
from sqlalchemy import (
    Column, Integer, ForeignKey, DateTime, String, Text, Enum as SQLEnum,
    cast, type_coerce
)
# Keep your Python enum definition
import enum
from sqlalchemy.orm import relationship
from src.models.base import BaseModel
# Import the PG Enum type explicitly if needed (though SQLEnum should handle it with native_enum=True)
# from sqlalchemy.dialects.postgresql import ENUM as PGEnum

# Your Python enum (looks correct)
class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"

# Create the SQLAlchemy Enum type instance *once* outside the class
# Use native_enum=True and ensure the DB type name matches 'notification_status'
notification_status_enum = SQLEnum(
    NotificationStatus,
    name="notification_status", # Match PG type name
    native_enum=True,
    create_type=False,
    values_callable=lambda obj: [e.value for e in obj] # Keep this for clarity
)

class DeliveryLog(BaseModel):
    """Log of delivered notifications to users"""
    __tablename__ = "delivery_logs"

    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    user = relationship("User", back_populates="delivery_logs")

    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False, index=True)
    question = relationship("Question")

    delivered_at = Column(DateTime(timezone=True), nullable=False, index=True)
    platform = Column(String(20), default="mobile", nullable=False)

    # --- Use the pre-defined SQLEnum instance ---
    # This ensures consistency and might help SQLAlchemy resolve the type correctly
    delivery_status = Column(
        notification_status_enum, # Use the instance created above
        nullable=False
        # Default is handled in repository logic
    )
    # --- END MODIFICATION ---

    fcm_message_id = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)

    def __repr__(self):
        # Access .value for representation if delivery_status holds the enum object
        status_repr = self.delivery_status.value if isinstance(self.delivery_status, NotificationStatus) else self.delivery_status
        return f"<DeliveryLog user_id={self.user_id} question_id={self.question_id} status={status_repr}>"
