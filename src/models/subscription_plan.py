# backend/src/models/subscription_plan.py
from sqlalchemy import Column, String, Integer, Float, Boolean, JSON
from src.models.base import BaseModel

class SubscriptionPlan(BaseModel):
    __tablename__ = "subscription_plans"
    
    plan_name = Column(String(50), unique=True, nullable=False)  # "free", "premium"
    price_inr = Column(Float, default=0.0)  # ₹99, ₹499, etc.
    duration_days = Column(Integer, default=30)  # 30, 90, 365
    max_notification_times = Column(Integer, default=4)
    max_daily_items = Column(Integer, default=3)
    features = Column(JSON, default={})  # {"ad_free": true, "priority_support": true}
    is_active = Column(Boolean, default=True)
