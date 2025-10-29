"""
Subscription Management API - Admin & User Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from src.api.dependencies import get_db, get_current_user
from src.schemas.subscription_schemas import *
from src.core.services.subscription_service import SubscriptionService
from src.config import settings
from src.models.user import User
from typing import cast
import logging

logger = logging.getLogger(__name__)

# Separate admin and user routers
admin_router = APIRouter(prefix="/admin/subscriptions", tags=["Admin - Subscriptions"])
user_router = APIRouter(prefix="/subscriptions", tags=["User - Subscriptions"])


def require_admin(api_key: str = Header(..., alias="X-Admin-Key")):
    """Admin authentication via API key"""
    if api_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin credentials")
    return {"email": "admin@currentaffairs.com"}


# ==================== ADMIN ROUTES ====================

@admin_router.post("/grant-trial")
def grant_trial(
    request: GrantTrialRequest,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin)
):
    """
    Grant free trial to user
    Body: {"user_email": "user@example.com", "days": 7, "notes": "Launch promo"}
    """
    logger.info(f"📝 Admin granting {request.days}-day trial to {request.user_email}")
    service = SubscriptionService(db)
    result = service.grant_trial(
        user_email=request.user_email,
        days=request.days,
        granted_by=admin['email'],
        notes=request.notes
    )
    logger.info(f"✅ Trial granted successfully to {request.user_email}")
    return {
        "success": True,
        "user": {
            "email": result.email,
            "subscription_status": result.subscription_status
        }
    }


@admin_router.post("/grant-premium")
def grant_premium(
    request: GrantPremiumRequest,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin)
):
    """
    Manually grant premium (no payment)
    Body: {"user_email": "user@example.com", "plan_name": "premium_monthly", "notes": "VIP user"}
    """
    logger.info(f"📝 Admin granting premium ({request.plan_name}) to {request.user_email}")
    service = SubscriptionService(db)
    result = service.grant_premium(
        user_email=request.user_email,
        plan_name=request.plan_name,
        granted_by=admin['email'],
        notes=request.notes
    )
    logger.info(f"✅ Premium granted successfully to {request.user_email}")
    return {
        "success": True,
        "user": {
            "email": result.email,
            "subscription_status": result.subscription_status
        }
    }


@admin_router.post("/promo-codes")
def create_promo_code(
    request: CreatePromoRequest,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin)
):
    """
    Create new promo code
    Body: {
      "code": "FIRST50",
      "promo_type": "discount",
      "discount_percent": 50,
      "max_uses": 100,
      "expires_at": "2025-12-31T23:59:59"
    }
    """
    logger.info(f"📝 Admin creating promo code: {request.code}")
    service = SubscriptionService(db)
    promo = service.create_promo_code(request.dict())
    logger.info(f"✅ Promo code created: {request.code}")
    return {
        "success": True,
        "promo_code": {
            "code": promo.code,
            "type": promo.promo_type
        }
    }


@admin_router.get("/promo-codes")
def list_promo_codes(
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin)
):
    """Get all promo codes (active and expired)"""
    logger.info("📝 Admin fetching all promo codes")
    service = SubscriptionService(db)
    codes = service.list_promo_codes()
    return {
        "success": True,
        "promo_codes": [
            {
                "code": c.code,
                "type": c.promo_type,
                "used": c.used_count,
                "max": c.max_uses,
                "expires_at": c.expires_at.isoformat() if c.expires_at is not None else None
            }
            for c in codes
        ]
    }


@admin_router.put("/plans/{plan_name}")
def update_plan(
    plan_name: str,
    request: UpdatePlanRequest,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin)
):
    """
    Update plan pricing/features
    Body: {"price_inr": 149, "max_daily_items": 15}
    """
    logger.info(f"📝 Admin updating plan: {plan_name}")
    service = SubscriptionService(db)
    plan = service.update_plan(plan_name, request.dict(exclude_unset=True))
    logger.info(f"✅ Plan updated: {plan_name}")
    return {
        "success": True,
        "plan": {
            "name": plan.plan_name,
            "price": plan.price_inr
        }
    }


# ==================== USER ROUTES ====================

@user_router.post("/apply-promo")
async def apply_promo_code(
    request: ApplyPromoRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    User applies promo code
    Body: {"code": "TRIAL7"}
    
    Examples:
    - TRIAL7: 7-day free trial
    - LAUNCH50: 50% discount on premium
    """
    logger.info(f"📝 User {current_user.email} applying promo code: {request.code}")
    
    service = SubscriptionService(db)
    
    try:
        result_data = service.apply_promo_code(
            user_id=cast(int, current_user.id),
            code=request.code,
            device_id=request.device_id
        )
        
        updated_user = result_data.get("user")
        message = result_data.get("message", "Promo code applied successfully!")

        if not updated_user:
            raise HTTPException(status_code=500, detail="Failed to retrieve user after applying promo code")

        logger.info(f"✅ Promo code {request.code} applied successfully for {current_user.email}")
        
        # Normalize returned user (may be a dict from the service or an ORM model)
        if isinstance(updated_user, dict):
            status_obj = updated_user.get("subscription_status")
            expires_obj = updated_user.get("subscription_expires_at")
        else:
            status_obj = getattr(updated_user, "subscription_status", None)
            expires_obj = getattr(updated_user, "subscription_expires_at", None)
        
        # Extract value if it's an Enum or leave as-is
        if status_obj is None:
            status = None
        elif hasattr(status_obj, "value"):
            status = status_obj.value
        else:
            status = status_obj

        # Convert datetime-like to ISO string if possible, handle None safely
        if expires_obj is None:
            expires = None
        elif hasattr(expires_obj, "isoformat"):
            try:
                expires = expires_obj.isoformat()
            except Exception:
                # Fallback to string representation if isoformat fails
                expires = str(expires_obj)
        else:
            expires = expires_obj

        return {
            "success": True,
            "message": message, 
            "user": {
                "subscription_status": status,
                "subscription_expires_at": expires
            }
        }
    except ValueError as e:
        logger.warning(f"❌ Invalid promo code {request.code}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        # Re-raise HTTPExceptions from the service layer directly
        raise
    except Exception as e:
        logger.error(f"❌ Unhandled error applying promo code: {str(e)}")
        raise HTTPException(status_code=500, detail="A server error occurred while applying the promo code.")