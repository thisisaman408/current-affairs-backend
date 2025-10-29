# backend/src/models/promo_code.py
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Enum as SQLEnum
from src.models.base import BaseModel
from datetime import datetime
import enum

class PromoType(str, enum.Enum):
    DISCOUNT = "discount"  
    TRIAL = "trial"  

class PromoCode(BaseModel):
    __tablename__ = "promo_codes"
    
    code = Column(String(50), unique=True, nullable=False)  # "FIRST50", "TRIAL7"
    promo_type = Column(String, nullable=False) 
    discount_percent = Column(Integer, default=0)  # 50 = 50% off
    discount_fixed_inr = Column(Float, default=0.0)  # ₹20 off
    trial_days = Column(Integer, default=0)  # 7 days free
    max_uses = Column(Integer, default=100)
    used_count = Column(Integer, default=0)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
