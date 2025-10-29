"""
API Dependencies - Authentication & Authorization
"""
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from src.database.session import get_db
from src.core.repositories.user_repository import UserRepository
from src.integrations.firebase_auth import firebase_auth_client
from src.models.user import User
from typing import Optional, cast
import logging

logger = logging.getLogger(__name__)

async def get_current_user(
    authorization: str = Header(..., description="Bearer <firebase_token>"),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to authenticate user via Firebase token
    
    Usage in routes:
        @router.get("/profile")
        async def get_profile(user: User = Depends(get_current_user)):
            return user
    
    Args:
        authorization: Authorization header with Firebase ID token
        db: Database session
    
    Returns:
        Authenticated User object
    
    Raises:
        HTTPException 401: If authentication fails
    """
    # Extract token from "Bearer <token>"
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format. Use: Bearer <token>"
        )
    
    token = authorization.replace("Bearer ", "").strip()
    
    # Verify Firebase token
    token_data = firebase_auth_client.verify_id_token(token)
    if not token_data:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired Firebase token"
        )
    
    firebase_uid = token_data.get("uid")
    # Ensure firebase_uid is a valid string; raise if missing or wrong type to satisfy type checker
    if not firebase_uid or not isinstance(firebase_uid, str):
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload: missing 'uid'"
        )
    
    # Fetch user from database
    user_repo = UserRepository(db)
    user = user_repo.get_by_firebase_uid(firebase_uid)
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found. Please register first."
        )
    
    # cast user.is_active to bool so the static type checker doesn't treat it as a Column[bool]
    if not cast(bool, user.is_active):
        raise HTTPException(
            status_code=403,
            detail="User account is deactivated"
        )
    
    logger.info(f"✅ Authenticated user: {user.email or user.firebase_uid}")
    return user

async def get_optional_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Optional authentication - returns User or None
    Use for endpoints that work with or without auth
    """
    if not authorization:
        return None
    
    try:
        return await get_current_user(authorization, db)
    except HTTPException:
        return None
