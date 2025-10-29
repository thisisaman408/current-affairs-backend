"""
Create database tables
Run once: python create_tables.py
"""
from src.database.base import Base
from src.database.session import engine

# Import ALL models (existing + new)
from src.models.pdf_job import PDFJob
from src.models.question import Question
from src.models.user import User
from src.models.user_preferences import UserPreferences
from src.models.device_token import DeviceToken
from src.models.delivery_log import DeliveryLog

import logging

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)


def create_tables():
    """Create all tables (only creates missing ones)"""
    logger.info("Creating database tables...")
    
    # This will ONLY create tables that don't exist yet
    # Existing tables (pdf_jobs, questions) won't be touched
    Base.metadata.create_all(bind=engine)
    
    logger.info("✅ Tables created successfully!")
    logger.info("Tables: pdf_jobs, questions, users, user_preferences, device_tokens, delivery_logs")


if __name__ == "__main__":
    create_tables()
