"""
Application Configuration
All settings loaded from .env file with IST timezone
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
import pytz

class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_HOST: str = "0.0.0.0"
    ADMIN_API_PORT: int = 8000
    USER_API_PORT: int = 8001
    
    # Timezone (IST everywhere!)
    TIMEZONE: str = "Asia/Kolkata"
    TZ: str = "Asia/Kolkata"
    
    @property
    def IST(self):
        """Get IST timezone object"""
        return pytz.timezone(self.TIMEZONE)
    
    # Database (Render PostgreSQL)
    DATABASE_URL: Optional[str] = None
    
    # Redis (Render Redis)
    REDIS_URL: Optional[str] = None
    
    # Celery
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""
    CELERY_TIMEZONE: str = "Asia/Kolkata"
    CELERY_ENABLE_UTC: bool = False
    
    @property
    def get_celery_broker(self):
        return self.CELERY_BROKER_URL or self.REDIS_URL
    
    @property
    def get_celery_result_backend(self):
        return self.CELERY_RESULT_BACKEND or self.REDIS_URL
    
    # Firebase (Auth + FCM)
    FIREBASE_TYPE: Optional[str] = None
    FIREBASE_PROJECT_ID: Optional[str] = None
    FIREBASE_PRIVATE_KEY_ID: Optional[str] = None
    FIREBASE_PRIVATE_KEY: Optional[str] = None
    FIREBASE_CLIENT_EMAIL: Optional[str] = None
    FIREBASE_CLIENT_ID: Optional[str] = None
    FIREBASE_AUTH_URI: Optional[str] = None
    FIREBASE_TOKEN_URI: Optional[str] = None
    FIREBASE_AUTH_PROVIDER_CERT_URL: Optional[str] = None
    FIREBASE_CLIENT_CERT_URL: Optional[str] = None
    FIREBASE_UNIVERSE_DOMAIN: str = "googleapis.com"
    
    # FCM
    FCM_MAX_BATCH_SIZE: int = 500
    FCM_RETRY_ATTEMPTS: int = 3
    
    # Cloudflare R2 (PDF Storage)
    R2_ENDPOINT: Optional[str] = None
    R2_ACCESS_KEY_ID: Optional[str] = None
    R2_SECRET_ACCESS_KEY: Optional[str] = None
    R2_BUCKET_NAME: Optional[str] = None
    R2_REGION: str = "auto"
    
    # PDF Config
    PDF_MAX_SIZE_MB: int = 50
    PDF_ALLOWED_EXAMS: str = "General,UPSC,SSC,Banking,Railway,Defence"
    
    @property
    def get_allowed_exams(self) -> List[str]:
        """Parse comma-separated exam types"""
        return [exam.strip() for exam in self.PDF_ALLOWED_EXAMS.split(",")]
    
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    GROQ_MAX_TOKENS: int = 4048
    GROQ_TEMPERATURE: float = 0.7
    
    # Security
    SECRET_KEY: Optional[str] = None
    JWT_SECRET_KEY: Optional[str] = None
    ADMIN_API_KEY: str = Field(default="change-me-in-production")
    
    # Rate Limiting
    RATE_LIMIT_ADMIN_UPLOADS: int = 10
    RATE_LIMIT_USER_API: int = 100


    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "/var/app/logs"


    #misc
    PROCESSING_MODE:str = "slow"
    CHUNK_DELAY_SECONDS: int = 120  
    FAST_CHUNK_DELAY_SECONDS: int = 5 
    
    class Config:
        from pathlib import Path
        env_file = Path(__file__).resolve().parent.parent / ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()
