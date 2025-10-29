"""
Database Session with IST Timezone
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from src.config import settings
from typing import Generator
import logging

# ✅ IMPORT ALL MODELS
import src.models

logger = logging.getLogger(__name__)

if settings.DATABASE_URL is None:
    raise RuntimeError("DATABASE_URL is not set in settings")

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)  # ✅ ADDED CLOSING PARENTHESIS


# Force IST timezone on every connection
@event.listens_for(engine, "connect")
def set_timezone(dbapi_conn, connection_record):
    """Set timezone to Asia/Kolkata for all connections"""
    cursor = dbapi_conn.cursor()
    cursor.execute("SET timezone='Asia/Kolkata'")
    cursor.close()
    logger.info("✅ Database connection with IST timezone")


# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI routes
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # ✅ ONLY ONE CLOSE
