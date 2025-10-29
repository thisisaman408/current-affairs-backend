from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class GrantTrialRequest(BaseModel):
    user_email: str
    days: int = Field(ge=1, le=365, description="Trial duration (1-365 days)")
    notes: Optional[str] = None

class GrantPremiumRequest(BaseModel):
    user_email: str
    plan_name: str  # "premium_monthly" or "premium_yearly"
    notes: Optional[str] = None

class ApplyPromoRequest(BaseModel):
    code: str = Field(min_length=3, max_length=50)
    device_id: Optional[str] = None

class CreatePromoRequest(BaseModel):
    code: str = Field(min_length=3, max_length=50)
    device_id: Optional[str] = None
    promo_type: str  # "discount" or "trial"
    discount_percent: Optional[int] = Field(default=0, ge=0, le=100)
    discount_fixed_inr: Optional[float] = Field(default=0, ge=0)
    trial_days: Optional[int] = Field(default=0, ge=0, le=365)
    max_uses: int = Field(default=100, ge=1)
    expires_at: Optional[datetime] = None
    
    @validator('promo_type')
    def validate_type(cls, v):
        if v not in ['discount', 'trial']:
            raise ValueError("promo_type must be 'discount' or 'trial'")
        return v

class UpdatePlanRequest(BaseModel):
    price_inr: Optional[float] = None
    duration_days: Optional[int] = None
    max_notification_times: Optional[int] = None
    max_daily_items: Optional[int] = None
    features: Optional[dict] = None
