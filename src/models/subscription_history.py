"""
Subscription History Model
"""
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from src.models.base import BaseModel


class SubscriptionHistory(BaseModel):
    """Track subscription changes"""
    __tablename__ = "subscription_history"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(50), nullable=False)  # "trial_granted", "premium_granted", "promo_applied", "subscription_expired"
    plan_name = Column(String(50), nullable=True)  # "premium_monthly"
    promo_code = Column(String(50), nullable=True)  # "TRIAL7"
    granted_by = Column(String(255), nullable=True)  # Admin email or "system"
    notes = Column(String(500), nullable=True)
    device_id = Column(String(255), nullable=True)
    
    # Relationship back to User
    user = relationship("User", back_populates="subscription_history")
    
    def __repr__(self):
        return f"<SubscriptionHistory user_id={self.user_id} action={self.action}>"
