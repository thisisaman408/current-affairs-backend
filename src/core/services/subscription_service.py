"""
Subscription Management Service
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from src.core.repositories.user_repository import UserRepository
from src.models.user import User, SubscriptionStatus
from src.models.promo_code import PromoCode, PromoType
from src.models.subscription_plan import SubscriptionPlan
from src.models.subscription_history import SubscriptionHistory
from datetime import datetime, timedelta
from fastapi import HTTPException
import logging
from src.config import settings
from sqlalchemy import or_
logger = logging.getLogger(__name__)


class SubscriptionService:
    """Service for subscription and promo code management"""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
    
    def grant_trial(self, user_email: str, days: int, granted_by: str, notes: Optional[str] = None) -> User:
        """Grant free trial to user"""
        user = self.user_repo.get_by_email(user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update subscription
        user.subscription_status = SubscriptionStatus.TRIAL.value
        user.subscription_started_at = datetime.now(settings.IST)
        expires_at = datetime.now(settings.IST) + timedelta(days=days)
        user.subscription_expires_at = expires_at
        
        # Log history
        history = SubscriptionHistory(
            user_id=user.id,
            action="trial_granted",
            granted_by=granted_by,
            notes=notes or f"{days}-day trial"
        )
        self.db.add(history)
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"Granted {days}-day trial to user {user.email}")
        return user
    
    def grant_premium(self, user_email: str, plan_name: str, granted_by: str, notes: Optional[str] = None) -> User:
        """Grant premium without payment"""
        user = self.user_repo.get_by_email(user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        plan = self.db.query(SubscriptionPlan).filter_by(plan_name=plan_name, is_active=True).first()
        if not plan:
            raise HTTPException(status_code=404, detail=f"Plan '{plan_name}' not found")
        
        # Update subscription
        user.subscription_status = SubscriptionStatus.PREMIUM.value
        user.subscription_started_at = datetime.now(settings.IST)
        duration_days = getattr(plan, "duration_days", 0)
        duration_days_val = int(duration_days) if duration_days is not None else 0
        expires_at = datetime.now(settings.IST) + timedelta(days=duration_days_val)
        user.subscription_expires_at = expires_at
        
        # Log history
        history = SubscriptionHistory(
            user_id=user.id,
            action="premium_granted",
            plan_name=plan_name,
            granted_by=granted_by,
            notes=notes
        )
        self.db.add(history)
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"Granted premium ({plan_name}) to user {user.email}")
        return user
    
    def apply_promo_code(self, user_id: int, code: str, device_id: str | None = None) -> Dict[str, Any]:
        """User applies promo code"""
        promo = self.db.query(PromoCode).filter(PromoCode.code == code.upper()).first()
        if not promo:
            raise HTTPException(status_code=404, detail="Invalid promo code")
        
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        promo_type_val = getattr(promo, "promo_type", None)
        
        # ✅ FIX: Check trial usage with correct action names
        if promo_type_val == PromoType.TRIAL.value:
            # Check if THIS USER has ever used a trial
            user_trial_history = self.db.query(SubscriptionHistory).filter(
                SubscriptionHistory.action.in_(['trial_granted', 'trial_applied']),
                SubscriptionHistory.user_id == user_id
            ).first()
            
            if user_trial_history:
                raise HTTPException(
                    status_code=400, 
                    detail=f"You already used a free trial on {user_trial_history.created_at.strftime('%d %b %Y')}"
                )
            
            # ✅ Check if THIS DEVICE has ever been used for a trial
            if device_id:
                device_trial_history = self.db.query(SubscriptionHistory).filter(
                    SubscriptionHistory.action.in_(['trial_granted', 'trial_applied']),
                    SubscriptionHistory.device_id == device_id
                ).first()
                
                if device_trial_history:
                    raise HTTPException(
                        status_code=400, 
                        detail="A free trial has already been claimed on this device"
                    )
            else:
                logger.warning(f"⚠️ User {user.email} applying trial WITHOUT device_id - device check skipped!")
        
        # Validate promo code
        is_active_val = getattr(promo, "is_active", None)
        if is_active_val is False:
            raise HTTPException(status_code=400, detail="Promo code is no longer active")
        
        expires_at = getattr(promo, "expires_at", None)
        if expires_at is not None and isinstance(expires_at, datetime) and expires_at < datetime.now(settings.IST):
            raise HTTPException(status_code=400, detail="Promo code has expired")
        
        used_count = getattr(promo, "used_count", None)
        max_uses = getattr(promo, "max_uses", None)
        used_count_val = int(used_count) if used_count is not None else 0
        max_uses_val = int(max_uses) if max_uses is not None else 0
        if max_uses_val and used_count_val >= max_uses_val:
            raise HTTPException(status_code=400, detail="Promo code usage limit reached")
        
        # Apply promo based on type
        if promo_type_val == PromoType.TRIAL.value:
            user.subscription_status = SubscriptionStatus.TRIAL.value
            user.subscription_started_at = datetime.now(settings.IST)
            trial_days = int(getattr(promo, "trial_days", 0))
            expires_at = datetime.now(settings.IST) + timedelta(days=trial_days)
            user.subscription_expires_at = expires_at
            message = f"{trial_days}-day trial activated!"
            action_name = "trial_applied"  # ✅ FIX: Use correct action name
        else:
            discount_percent = getattr(promo, "discount_percent", 0)
            message = f"{discount_percent}% discount applied!"
            action_name = "promo_applied"
        
        promo.used_count += 1
        
        # ✅ FIX: Save history with correct action name
        history = SubscriptionHistory(
            user_id=user.id,
            action=action_name,  # ✅ Now saves "trial_applied" for trials
            promo_code=code.upper(),
            notes=message,
            device_id=device_id if device_id else None
        )
        self.db.add(history)
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"✅ User {user.email} applied {action_name} ({code}) | Device: {device_id or 'NO_DEVICE_ID'}")
        return {"message": message, "user": user}

    
    def create_promo_code(self, data: Dict[str, Any]) -> PromoCode:
        """Create new promo code"""
        existing = self.db.query(PromoCode).filter(PromoCode.code == data['code'].upper()).first()
        if existing:
            raise HTTPException(status_code=400, detail="Promo code already exists")
        
        promo = PromoCode(**data)
        promo.code = data['code'].upper()
        self.db.add(promo)
        self.db.commit()
        self.db.refresh(promo)
        
        logger.info(f"Created promo code: {promo.code}")
        return promo
    
    def list_promo_codes(self) -> list[PromoCode]:
        """Get all promo codes"""
        return self.db.query(PromoCode).order_by(PromoCode.created_at.desc()).all()
    
    def update_plan(self, plan_name: str, updates: Dict[str, Any]) -> SubscriptionPlan:
        """Update subscription plan settings"""
        plan = self.db.query(SubscriptionPlan).filter_by(plan_name=plan_name).first()
        if not plan:
            raise HTTPException(status_code=404, detail=f"Plan '{plan_name}' not found")
        
        for key, value in updates.items():
            if hasattr(plan, key):
                setattr(plan, key, value)
        
        self.db.commit()
        self.db.refresh(plan)
        
        logger.info(f"Updated plan {plan_name}: {updates}")
        return plan