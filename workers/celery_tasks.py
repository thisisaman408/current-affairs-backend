"""
Celery Background Tasks
"""
from src.config import settings
from celery import Celery
from celery.schedules import crontab
from src.database.session import SessionLocal
from src.models.user import User, SubscriptionStatus
from src.models.subscription_history import SubscriptionHistory
from datetime import datetime
import sys
import logging

logger = logging.getLogger(__name__)
if not settings.REDIS_URL:
    print("❌ ERROR: REDIS_URL environment variable is not set!")
    print("❌ Cannot start Celery worker without Redis!")
    sys.exit(1)
print(f"✅ Using Redis broker: {settings.REDIS_URL[:30]}...")
celery = Celery('current_affairs', broker=settings.REDIS_URL,backend=settings.REDIS_URL)


@celery.task
def expire_subscriptions():
    """Run daily at 00:00 IST - Downgrade expired trials/premiums to FREE"""
    db = SessionLocal()
    try:
        # Find expired subscriptions
        now = datetime.now()
        expired = db.query(User).filter(
            User.subscription_status.in_([SubscriptionStatus.TRIAL.value, SubscriptionStatus.PREMIUM.value]),
            User.subscription_expires_at < now
        ).all()
        
        for user in expired:
            old_status = user.subscription_status
            
            # Downgrade to FREE
            user.subscription_status = SubscriptionStatus.FREE.value  # type: ignore
            user.subscription_expires_at = None  # type: ignore
            
            # Log expiration
            history = SubscriptionHistory(
                user_id=user.id,
                action="subscription_expired",
                notes=f"Auto-downgraded from {old_status} to FREE",
                granted_by="system"
            )
            db.add(history)
            logger.info(f"Expired subscription for user {user.email}")
        
        db.commit()
        logger.info(f"Expired {len(expired)} subscriptions")
        return f"Expired {len(expired)} subscriptions"
    except Exception as e:
        logger.error(f"Error expiring subscriptions: {e}")
        db.rollback()
        raise
    finally:
        db.close()


# Schedule task - runs daily at midnight IST
celery.conf.beat_schedule = {
    'expire-subscriptions': {
        'task': 'workers.celery_tasks.expire_subscriptions',
        'schedule': crontab(hour='0', minute='0'),  # Daily midnight
    }
}

# Set timezone via update to avoid assigning to Settings property directly
celery.conf.update(timezone='Asia/Kolkata')
