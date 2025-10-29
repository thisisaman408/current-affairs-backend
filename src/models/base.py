"""
Base Model with IST Timezone
"""
from sqlalchemy import Column, Integer, DateTime
from datetime import datetime
from src.database.base import Base
from src.config import settings

class BaseModel(Base):
    """Abstract base model with common fields"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(settings.IST),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(settings.IST),
        onupdate=lambda: datetime.now(settings.IST),
        nullable=False
    )
