"""
Base Service (SOLID - Single Responsibility)
All services inherit from this
"""
from abc import ABC

class BaseService(ABC):
    """
    Abstract base service for business logic
    All service classes inherit from this
    """
    
    def __init__(self):
        """Initialize base service"""
        pass
