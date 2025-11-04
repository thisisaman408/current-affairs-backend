# src/core/services/content_service.py
"""
Content Service
Business logic for daily content sync
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from src.core.services.base_service import BaseService
from src.core.repositories.content_repository import ContentRepository
from src.core.repositories.preference_repository import PreferenceRepository
from src.models.user import User, SubscriptionStatus
from sqlalchemy import cast
import logging
from datetime import datetime, timedelta
from src.utils.timezone_utils import now_ist, to_ist 
from src.core.repositories.delivery_log_repository import DeliveryLogRepository
logger = logging.getLogger(__name__)


class ContentService(BaseService):
    """Service for daily content operations"""

    def __init__(self):
        """Initialize content service with repository"""
        super().__init__()
        self.content_repo = ContentRepository()


    #this is an old function!

    # def get_daily_content_for_user(
    #     self,
    #     user: User,
    #     db: Session
    # ) -> Dict[str, Any]:
    #     """
    #     Get daily content for user based on subscription and preferences
        
    #     Args:
    #         user: User object
    #         db: Database session
            
    #     Returns:
    #         Dict with content list and metadata
    #     """
    #     try:
    #         # Initialize repos with db session
    #         preference_repo = PreferenceRepository(db)

    #         # Get user preferences
    #         preferences = preference_repo.get_by_user_id(user.id)
    #         if not preferences:
    #             logger.warning(f"⚠️ No preferences found for user {user.id}")
    #             return {
    #                 "success": False,
    #                 "error": "User preferences not set",
    #                 "content": [],
    #                 "metadata": {
    #                     "total_items": 0,
    #                     "fact_count": 0,
    #                     "question_count": 0,
    #                     "exam_types": [],
    #                     "subscription_status": user.subscription_status
    #                 }
    #             }

    #         # ✅ FIX: Calculate total items = notifications × items_per_notification
    #         # FREE: 4 notifications × 3 items = 12 total items
    #         # PREMIUM: custom notifications × custom items (1-10 per notification)
    #         total_items = len(preferences.notification_times) * preferences.daily_item_count
            
    #         logger.info(
    #             f"📊 User {user.id} ({user.subscription_status}): "
    #             f"{len(preferences.notification_times)} notifications × "
    #             f"{preferences.daily_item_count} items = {total_items} total items"
    #         )

    #         # Calculate fact/question ratio (85% facts, 15% questions) - GLOBAL CONSTANT
    #         content_ratio = preferences.content_type_ratio  # Always {"facts": 85, "questions": 15}
    #         fact_ratio = content_ratio.get("facts", 85) / 100
    #         question_ratio = content_ratio.get("questions", 15) / 100
            
    #         fact_count = int(total_items * fact_ratio)
    #         question_count = total_items - fact_count

    #         # Ensure at least 1 of each if total > 1
    #         if total_items > 1:
    #             fact_count = max(1, fact_count)
    #             question_count = max(1, question_count)

    #         logger.info(
    #             f"📊 Content split: {fact_count} facts ({int(fact_ratio*100)}%), "
    #             f"{question_count} questions ({int(question_ratio*100)}%)"
    #         )

    #         # Get undelivered content
    #         content = self.content_repo.get_undelivered_questions(
    #             user_id=user.id,
    #             exam_types=preferences.exam_types,
    #             limit=total_items,
    #             fact_count=fact_count,
    #             question_count=question_count,
    #             db=db
    #         )

    #         if not content:
    #             # Check if there's any content available at all
    #             available = self.content_repo.get_total_available_content(
    #                 exam_types=preferences.exam_types,
    #                 db=db
    #             )
                
    #             if available['total'] == 0:
    #                 return {
    #                     "success": False,
    #                     "error": "No content available for selected exam types",
    #                     "content": [],
    #                     "metadata": {
    #                         "total_items": 0,
    #                         "fact_count": 0,
    #                         "question_count": 0,
    #                         "exam_types": preferences.exam_types,
    #                         "subscription_status": user.subscription_status
    #                     }
    #                 }
    #             else:
    #                 return {
    #                     "success": False,
    #                     "error": "All available content has been delivered. Please wait for new content.",
    #                     "content": [],
    #                     "available_content": available,
    #                     "metadata": {
    #                         "total_items": 0,
    #                         "fact_count": 0,
    #                         "question_count": 0,
    #                         "exam_types": preferences.exam_types,
    #                         "subscription_status": user.subscription_status
    #                     }
    #                 }

    #         # Format content for mobile
    #         formatted_content = self._format_content_for_mobile(content)

    #         return {
    #             "success": True,
    #             "content": formatted_content,
    #             "metadata": {
    #                 "total_items": len(formatted_content),
    #                 "fact_count": len([c for c in content if c.content_type == 'fact']),
    #                 "question_count": len([c for c in content if c.content_type == 'question']),
    #                 "exam_types": preferences.exam_types,
    #                 "subscription_status": user.subscription_status
    #             }
    #         }

    #     except Exception as e:
    #         logger.error(f"❌ Failed to get daily content for user {user.id}: {e}")
    #         return {
    #             "success": False,
    #             "error": str(e),
    #             "content": [],
    #             "metadata": {
    #                 "total_items": 0,
    #                 "fact_count": 0,
    #                 "question_count": 0,
    #                 "exam_types": [],
    #                 "subscription_status": user.subscription_status
    #             }
    #         }

    def _format_content_for_mobile(self, scheduled_items: List) -> List[Dict[str, Any]]:
        """Format content items (which now have a .scheduled_time attribute) for the mobile app response."""
        formatted = []
        for q in scheduled_items: # Iterate through items that *have* been scheduled
            item_data = {
                "id": q.id,
                "content_type": q.content_type,
                "exam_type": q.exam_type,
                "title": q.title,
                "description": q.description,
                "explanation": q.explanation,
                "date_from": q.date_from.isoformat() if q.date_from else None,
                "date_to": q.date_to.isoformat() if q.date_to else None,
                "category": q.category,
                # Use the assigned scheduled_time attribute
                "scheduled_time": getattr(q, 'scheduled_time', None),
                "delivered_at": None,
            }
            if q.content_type == 'question' and q.options:
                item_data["options"] = q.options
                item_data["correct_answer"] = q.correct_answer
            formatted.append(item_data)
        return formatted
    def get_random_content(self, user: User, content_type: str, db: Session) -> Dict[str, Any]:
        """Get a single random content item"""
        try:
            exam_types = user.preferences.exam_types if user.preferences else ['UPSC']
            
            # Get random content from repo
            from sqlalchemy import and_, func, not_
            from src.models.question import Question
            from src.models.delivery_log import DeliveryLog
            
            # Subquery: delivered content
            delivered_ids = db.query(DeliveryLog.question_id).filter(
                DeliveryLog.user_id == user.id
            ).subquery() 
            
            # Get undelivered random content
            content = db.query(Question).filter(
                and_(
                    Question.exam_type.in_(exam_types),
                    Question.content_type == content_type,
                    not_(Question.id.in_(delivered_ids))
                )
            ).order_by(func.random()).limit(1).all()
            
            if not content:
                # If all delivered, get any random one
                content = db.query(Question).filter(
                    and_(
                        Question.exam_type.in_(exam_types),
                        Question.content_type == content_type
                    )
                ).order_by(func.random()).limit(1).all()
            
            formatted = self._format_content_for_mobile(content) if content else []
            
            return {
                'success': True,
                'content': formatted
            }
        
        except Exception as e:
            logger.error(f"Error getting random content: {e}")
            return {
                'success': False,
                'content': [],
                'error': str(e)
            }
    
   # In backend/src/core/services/content_service.py

    def get_user_history(self, user: User, page: int, limit: int, db: Session) -> Dict[str, Any]:
        """
        Retrieves user's content history via DeliveryLogRepository.
        """
        try:
            delivery_repo = DeliveryLogRepository()
            return delivery_repo.get_user_history(user, page, limit, db)
        except Exception as e:
            logger.error(f"Error getting history for user {user.id}: {e}")
            return {'success': False, 'content': [], 'metadata': {}, 'error': str(e)}
            

    def fetch_daily_content(
        self,
        user: User,
        from_time: datetime, # Expected to be timezone-aware (UTC from frontend)
        to_time: datetime,   # Expected to be timezone-aware (UTC from frontend)
        notification_times: List[str], # List of "HH:MM" strings
        daily_item_count: int,
        content_type_ratio: Dict[str, int],
        exam_types: List[str],
        db: Session
    ) -> Dict[str, Any]:
        try:
            from_time_ist = to_ist(from_time) # Convert request start time to IST
            to_time_ist = to_ist(to_time)     # Convert request end time to IST
            now = now_ist()

            logger.info(f"📅 Fetch content for User ID {user.id} requested range (IST): {from_time_ist.isoformat()} to {to_time_ist.isoformat()}")

            # --- START OF CORRECTED LOGIC ---

            # Determine the effective start time *for scheduling today's content*.
            # This determines *which* of today's slots should be filled.
            effective_start_time_for_today = now # Default: only schedule future slots (e.g., for preference changes)

            user_creation_time_ist = to_ist(user.created_at)

            # Check if this request looks like a full-day sync request (sent from start of day IST)
            is_full_day_sync_request = from_time_ist.hour == 0 and from_time_ist.minute == 0

            if is_full_day_sync_request:
                # If user was created today, start scheduling from their creation time.
                if user_creation_time_ist.date() == now.date():
                    effective_start_time_for_today = user_creation_time_ist
                    logger.info(f"User created today. Effective start time for today's schedule: {effective_start_time_for_today.isoformat()}")
                # If user is existing, schedule for the entire day (start from midnight IST).
                else:
                    effective_start_time_for_today = from_time_ist # Use the request's start time (midnight)
                    logger.info(f"Existing user full-day sync. Effective start time for today's schedule: {effective_start_time_for_today.isoformat()}")
            else:
                 # If it's not a full-day sync request, it's likely a preference change,
                 # so only schedule for future slots relative to 'now'.
                 logger.info(f"Mid-day request detected (likely preference change). Effective start time for today's schedule (future only): {effective_start_time_for_today.isoformat()}")


            # 1. Determine the relevant notification slots for TODAY based on the effective start time.
            todays_slots = []
            if from_time_ist.date() <= now.date() < to_time_ist.date(): # Check if today is within the request range
                for time_str in notification_times:
                    h, m = map(int, time_str.split(":"))
                    # Create a datetime object for today's notification time in IST
                    notification_time_today = now.replace(hour=h, minute=m, second=0, microsecond=0)
                    # Include the slot if its time is on or after the calculated effective start time
                    if notification_time_today >= effective_start_time_for_today:
                        todays_slots.append(time_str)

            # 2. Determine the number of notification slots for TOMORROW.
            slots_for_tomorrow = 0
            # Check if tomorrow is within the request range
            if to_time_ist.date() > now.date():
                 slots_for_tomorrow = len(notification_times)

            # 3. Calculate the TOTAL number of items to fetch.
            total_slots_to_fill = len(todays_slots) + slots_for_tomorrow
            total_items_to_fetch = total_slots_to_fill * daily_item_count

            # --- END OF CORRECTED LOGIC ---

            logger.info(f"Slots calculated: Today={len(todays_slots)}, Tomorrow={slots_for_tomorrow}, Total Slots={total_slots_to_fill}")
            logger.info(f"Total items to fetch: {total_slots_to_fill} slots * {daily_item_count} items/slot = {total_items_to_fetch}")

            if total_items_to_fetch <= 0:
                logger.info("No slots require content. Returning empty list.")
                return {
                    "success": True,
                    "items": [],
                    "metadata": { # Include metadata even if empty
                        "total_items": 0, "fact_count": 0, "question_count": 0,
                        "exam_types": exam_types, "subscription_status": user.subscription_status,
                        "period_start": from_time.isoformat(), "period_end": to_time.isoformat(),
                        "notification_times": notification_times
                    }
                }

            # Calculate fact/question split
            fr = content_type_ratio.get('fact', 85) / 100
            qr = content_type_ratio.get('question', 15) / 100
            fact_count = int(total_items_to_fetch * fr)
            question_count = total_items_to_fetch - fact_count
            # Ensure at least one question if possible and needed, adjust fact count
            if question_count == 0 and total_items_to_fetch > 0 and fr < 1.0:
                 question_count = 1
                 fact_count = total_items_to_fetch - 1
            elif fact_count == 0 and total_items_to_fetch > 0 and qr < 1.0:
                 fact_count = 1
                 question_count = total_items_to_fetch - 1


            logger.info(f"Requesting {fact_count} facts and {question_count} questions.")

            # Fetch undelivered content 
            content = self.content_repo.get_undelivered_questions(
                user_id=user.id,
                exam_types=exam_types,
                limit=total_items_to_fetch, # Request the total needed
                fact_count=fact_count,       # Guide the type split
                question_count=question_count,
                db=db,
            )
            if(len(content) == 0): logger.info(f"The content is 0 {content}")
            actual_fetched_count = len(content)
            if actual_fetched_count < total_items_to_fetch:
                logger.warning(f"Fetch Shortfall for user {user.id}: Wanted {total_items_to_fetch}, Got {actual_fetched_count}.")

            # Assign scheduled times to the fetched content
            scheduled = self._assign_scheduled_times(
                content=content,
                todays_slots=todays_slots, # Only pass the slots we determined are valid for today
                tomorrows_slots=notification_times if slots_for_tomorrow > 0 else [], # Pass all slots if tomorrow is needed
                base_time_ist=from_time_ist.replace(hour=0, minute=0, second=0, microsecond=0), # Use start of day for anchoring dates
                items_per_notification=daily_item_count
            )

            formatted = self._format_content_for_mobile(scheduled)
            final_item_count = len(formatted)

            logger.info(f"Returning {final_item_count} scheduled items for user {user.id}")

            return {
                "success": True,
                "items": formatted,
                "metadata": {
                    "total_items": final_item_count, # Report count of *scheduled* items
                    "fact_count": len([c for c in scheduled if c.content_type == 'fact']), # Count facts *actually scheduled*
                    "question_count": len([c for c in scheduled if c.content_type == 'question']), # Count questions *actually scheduled*
                    "exam_types": exam_types,
                    "subscription_status": user.subscription_status,
                    "period_start": from_time.isoformat(), # Use original request boundaries for metadata
                    "period_end": to_time.isoformat(),
                    "notification_times": notification_times # Return the user's full preference list
                }
            }
        except Exception as e:
            logger.error(f"❌ fetch_daily_content failed for user {user.id}: {e}", exc_info=True)
            # Ensure metadata keys exist even on error
            return {"success": False, "error": "Server error while fetching daily content.", "items": [], "metadata": {
                    "total_items": 0, "fact_count": 0, "question_count": 0,
                    "exam_types": exam_types, "subscription_status": user.subscription_status,
                    "period_start": from_time.isoformat(), "period_end": to_time.isoformat(),
                    "notification_times": notification_times
            }}

    def _assign_scheduled_times(
        self,
        content: List,
        todays_slots: List[str],      # Slots determined by fetch_daily_content logic
        tomorrows_slots: List[str],  # Will be empty if tomorrow wasn't needed
        base_time_ist: datetime,       # Start of the day IST for anchoring
        items_per_notification: int
    ) -> List:
        """
        Assigns scheduled IST timestamps to content items based on calculated slots.
        """
        scheduled_content = []
        item_index = 0
      
        now = now_ist()
        today_date = now.date() 

        # 1. Schedule for Today's calculated slots
        logger.info(f"Assigning times for today ({today_date}) for slots: {sorted(todays_slots)}")
        skipped_past_slots_today = 0
        assigned_today_count = 0
        for time_str in sorted(todays_slots):
            if item_index >= len(content): break
            hour, minute = map(int, time_str.split(":"))
            scheduled_time = now.replace(hour=hour, minute=minute)
            if scheduled_time > now:
                for _ in range(items_per_notification):
                    if item_index < len(content):
                        content[item_index].scheduled_time = scheduled_time.isoformat()
                        scheduled_content.append(content[item_index])
                        item_index += 1
                        assigned_today_count += 1
                    else:
                        logger.warning(f"Ran out of content while scheduling for today's slot {time_str}.")
                        break
                if item_index >= len(content): break
            else:
                # Skip slots that are in the past relative to 'now'
                skipped_past_slots_today += 1
                logger.info(f"Skipping assignment for past/present slot today: {time_str} ({scheduled_time.isoformat()})")

        # 2. Schedule for Tomorrow's slots (if needed and content remains)
        if item_index < len(content) and tomorrows_slots:
            tomorrow_date = today_date + timedelta(days=1)
            logger.info(f"Assigning times for tomorrow ({tomorrow_date}) for slots: {sorted(tomorrows_slots)}")
            for time_str in sorted(tomorrows_slots):
                if item_index >= len(content): break
                hour, minute = map(int, time_str.split(":"))
                scheduled_time = now.replace(
                    year=tomorrow_date.year, month=tomorrow_date.month, day=tomorrow_date.day,
                    hour=hour, minute=minute
                )
                for _ in range(items_per_notification):
                    if item_index < len(content):
                        content[item_index].scheduled_time = scheduled_time.isoformat()
                        scheduled_content.append(content[item_index])
                        item_index += 1
                    else:
                        logger.warning(f"Ran out of content while scheduling for tomorrow's slot {time_str}.")
                        break

        final_scheduled_count = len(scheduled_content)
        logger.info(f"✅ Assigned scheduled times to {final_scheduled_count} items.")
        if item_index < len(content):
            logger.warning(f"⚠️ {len(content) - item_index} fetched items were not assigned a schedule time (insufficient slots or fetch shortfall).")

        return scheduled_content