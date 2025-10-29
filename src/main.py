"""
FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.v1 import admin, auth, user
from src.api.v1.subscription import admin_router as subscription_admin_router, user_router as subscription_user_router
from src.config import settings
from src.database.session import engine
from src.models import base
import logging
from src.api.v1 import content
# Import all models to register SQLAlchemy relationships
from src.models.user import User
from src.models.user_preferences import UserPreferences
from src.models.device_token import DeviceToken
from src.models.delivery_log import DeliveryLog
from src.models.subscription_plan import SubscriptionPlan
from src.models.promo_code import PromoCode
from src.models.subscription_history import SubscriptionHistory
from src.models.question import Question
from src.models.pdf_job import PDFJob

# Create tables
base.Base.metadata.create_all(bind=engine)

# Setup logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Current Affairs Platform",
    description="API for PDF upload, user management, and notification delivery",
    version="1.0.0"
)

# CORS middleware (allow mobile app requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your mobile app domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(admin.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1")
app.include_router(subscription_admin_router, prefix="/api/v1")  # Admin subscription routes
app.include_router(subscription_user_router, prefix="/api/v1")  # User subscription routes
app.include_router(content.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "ok",
        "message": "Current Affairs Platform API",
        "version": "1.0.0",
        "timezone": settings.TIMEZONE
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "timezone": settings.TIMEZONE,
        "services": {
            "admin_api": "active",
            "user_api": "active",
            "auth_api": "active",
            "subscriptions_api": "active"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.ADMIN_API_PORT,
        reload=settings.DEBUG
    )
