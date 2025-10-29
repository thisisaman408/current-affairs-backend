"""
Admin Authentication Middleware
Validates ADMIN_API_KEY header
"""
from fastapi import Request, HTTPException, status
from src.config import settings
import logging

logger = logging.getLogger(__name__)

async def verify_admin_key(request: Request):
    """
    Verify admin API key from header
    Header: X-Admin-API-Key
    """
    api_key = request.headers.get("X-Admin-API-Key")
    logger.info(f"DEBUG: Comparing incoming key against settings.ADMIN_API_KEY = '{settings.ADMIN_API_KEY}'")
    if not api_key:
        logger.warning("❌ Missing admin API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide X-Admin-API-Key header"
        )
    
    if api_key != settings.ADMIN_API_KEY:
        logger.warning(f"DEBUG: Comparison failed. Received '{api_key}...', expected '{settings.ADMIN_API_KEY}...'")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    
    logger.info("✅ Admin authenticated")
    return True
