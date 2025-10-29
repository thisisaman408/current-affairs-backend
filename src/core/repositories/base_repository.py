"""
Base Repository (SOLID - Dependency Inversion)
All repositories inherit from this
"""
from abc import ABC
from typing import Generic, TypeVar, List, Optional
from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")

class BaseRepository(ABC, Generic[ModelType]):
    """Abstract repository for database operations"""
    
    def __init__(self, db: Session, model: type):
        self.db = db
        self.model = model
    
    def create(self, obj_in: dict) -> ModelType:
        """Create new record"""
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def get_by_id(self, id: int) -> Optional[ModelType]:
        """Get record by ID"""
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Get all records with pagination"""
        return self.db.query(self.model).offset(skip).limit(limit).all()
    
    def update(self, id: int, obj_in: dict) -> Optional[ModelType]:
        """Update record"""
        db_obj = self.get_by_id(id)
        if db_obj:
            for key, value in obj_in.items():
                setattr(db_obj, key, value)
            self.db.commit()
            self.db.refresh(db_obj)
        return db_obj
    
    def delete(self, id: int) -> bool:
        """Delete record"""
        db_obj = self.get_by_id(id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()
            return True
        return False
