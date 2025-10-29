# src/api/v1/content.py
"""
Content API Routes
Daily content sync for mobile app with OFFLINE-FIRST support
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database.session import get_db
from src.api.dependencies import get_current_user
from src.models.user import User
from src.schemas.content_schemas import (
    DailySyncResponse,
    FetchDailyRequest,
    FetchDailyResponse,
    MarkDeliveredRequest,
    MarkDeliveredResponse
)
from src.core.repositories.content_repository import ContentRepository
from src.core.services.content_service import ContentService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/content", tags=["content"])


@router.post("/fetch-daily", response_model=FetchDailyResponse)
async def fetch_daily_content(
    request: FetchDailyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    📱 OFFLINE-FIRST: Fetch content for entire day/period
    
    Frontend calls this:
    1. Every night at 11:59 PM to fetch tomorrow's content
    2. When user changes preferences (more notifications, different times)
    3. When user opens app and local SQLite has insufficient content
    
    Backend returns:
    - Content for all notification times in the period
    - Pre-scheduled with exact IST timestamps
    - Mix of facts (85%) and questions (15%)
    - Based on user's exam preferences
    - Only content NOT recently delivered to this user
    
    Frontend then:
    - Stores in local SQLite
    - Schedules LOCAL notifications (works offline)
    - Sends notifications even without internet
    """
    try:
        logger.info(f"📥 Fetch daily content request from user {current_user.id}")
        logger.info(f"   Period: {request.from_time} to {request.to_time}")
        logger.info(f"   Notification times: {request.notification_times}")
        logger.info(f"   Items per notification: {request.daily_item_count}")
        
        content_service = ContentService()
        
        # Fetch content for the entire period
        result = content_service.fetch_daily_content(
            user=current_user,
            from_time=request.from_time,
            to_time=request.to_time,
            notification_times=request.notification_times,
            daily_item_count=request.daily_item_count,
            content_type_ratio=request.content_type_ratio,
            exam_types=request.exam_types,
            db=db
        )
        
        if not result['success']:
            logger.warning(f"⚠️ Fetch failed for user {current_user.id}: {result.get('error')}")
            raise HTTPException(status_code=404, detail=result.get('error', 'No content available'))
        
        logger.info(f"✅ Fetched {len(result['items'])} items for user {current_user.id}")
        
        return FetchDailyResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fetch daily failed for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch content: {str(e)}")


@router.get("/daily-sync", response_model=DailySyncResponse)
async def daily_sync(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ⚠️ DEPRECATED: Use /fetch-daily instead
    
    Get today's daily content for user
    - Fetches content based on user's exam preferences
    - Returns 3 items for FREE, 10 for PREMIUM/TRIAL
    - Mix of 85% facts, 15% questions
    - Only returns undelivered content
    """
    try:
        logger.info(f"📥 Daily sync request from user {current_user.id}")

        content_service = ContentService()
        result = content_service.get_daily_content_for_user(current_user, db)

        if not result['success']:
            logger.warning(f"⚠️ No content available for user {current_user.id}: {result.get('error')}")

        return DailySyncResponse(**result)

    except Exception as e:
        logger.error(f"❌ Daily sync failed for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch daily content: {str(e)}")


@router.post("/{content_id}/read")
async def mark_content_as_read(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark a single content item as read (viewed) by user
    
    Called when user:
    - Answers a question
    - Views a fact
    - Expands explanation
    """
    try:
        logger.info(f"✅ Marking content {content_id} as read for user {current_user.id}")

        content_repo = ContentRepository()
        success = content_repo.mark_as_delivered(
            user_id=current_user.id,
            question_ids=[content_id],
            db=db
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to mark content as read")

        return {
            "success": True,
            "message": "Content marked as read",
            "content_id": content_id
        }

    except Exception as e:
        logger.error(f"❌ Failed to mark content {content_id} as read for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to mark as read: {str(e)}")


@router.get("/random-fact")
async def get_random_fact(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a single random fact based on user's exam preferences
    """
    try:
        logger.info(f"📚 Random fact request from user {current_user.id}")
        
        content_service = ContentService()
        result = content_service.get_random_content(
            user=current_user,
            content_type='fact',
            db=db
        )
        
        if not result['success'] or not result['content']:
            raise HTTPException(status_code=404, detail="No facts available")
        
        return {"success": True, "content": result['content'][0]}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get random fact: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/random-question")
async def get_random_question(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a single random question based on user's exam preferences
    """
    try:
        logger.info(f"❓ Random question request from user {current_user.id}")
        
        content_service = ContentService()
        result = content_service.get_random_content(
            user=current_user,
            content_type='question',
            db=db
        )
        
        if not result['success'] or not result['content']:
            raise HTTPException(status_code=404, detail="No questions available")
        
        return {"success": True, "content": result['content'][0]}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get random question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_content_history(
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's content history (past 30 days)
    Premium users only
    """
    try:
        logger.info(f"📜 History request from user {current_user.id}")
        
        # Check if premium
        if current_user.subscription_status not in ['premium', 'trial']:
            raise HTTPException(
                status_code=403, 
                detail="Premium subscription required for history access"
            )
        
        content_service = ContentService()
        result = content_service.get_user_history(
            user=current_user,
            page=page,
            limit=limit,
            db=db
        )
        
        return DailySyncResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mark-delivered", response_model=MarkDeliveredResponse)
async def mark_delivered(
    request: MarkDeliveredRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"✅ Marking {len(request.question_ids)} items as delivered for user {current_user.id}")
        content_repo = ContentRepository()
        # This now delegates fully to DeliveryLogRepository inside ContentRepository
        success = content_repo.mark_as_delivered(
            user_id=current_user.id,
            question_ids=request.question_ids,
            db=db
        )
        if not success:
            raise HTTPException(status_code=500, detail="Failed to mark content as delivered")
        return MarkDeliveredResponse(
            success=True,
            message="Content marked as delivered successfully",
            delivered_count=len(request.question_ids)
        )
    except Exception as e:
        logger.error(f"❌ Failed to mark delivered for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to mark as delivered: {str(e)}")

@router.get("/scheduled")
async def get_scheduled_content(
    start_time: str,
    end_time: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get scheduled content for a time range"""
    try:
        logger.info(f"📅 Scheduled content request from user {current_user.id}")
        logger.info(f"   Range: {start_time} to {end_time}")
        
        # ✅ CONVERT ISO STRINGS TO DATETIME WITH TIMEZONE
        from datetime import datetime
        from src.utils.timezone_utils import to_ist
        
        start_dt = to_ist(start_time)  # Convert ISO string to datetime
        end_dt = to_ist(end_time)
        
        # Get user preferences
        from src.core.repositories.preference_repository import PreferenceRepository
        pref_repo = PreferenceRepository(db)
        prefs = pref_repo.get_by_user_id(current_user.id)
        
        if not prefs:
            raise HTTPException(status_code=404, detail="User preferences not found")
        
        # Use fetch_daily_content
        content_service = ContentService()
        result = content_service.fetch_daily_content(
            user=current_user,
            from_time=start_dt,  # ✅ Pass datetime object
            to_time=end_dt,       # ✅ Pass datetime object
            notification_times=prefs.notification_times or ['09:00', '13:00', '18:00', '21:00'],
            daily_item_count=prefs.daily_item_count or 3,
            content_type_ratio={'fact': 85, 'question': 15},
            exam_types=prefs.exam_types or ['UPSC'],
            db=db
        )
        
        if not result['success']:
            logger.warning(f"⚠️ No scheduled content for user {current_user.id}")
            return []
        
        logger.info(f"✅ Returning {len(result['items'])} scheduled items")
        return result['items']
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get scheduled content: {e}")
        raise HTTPException(status_code=500, detail=str(e))
