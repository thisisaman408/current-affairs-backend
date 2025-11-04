from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
# Add import for explicit casting if needed, though usually not required for native enums
# from sqlalchemy import cast, Enum as SQLEnumType -- Probably not needed yet

from src.models.delivery_log import DeliveryLog, NotificationStatus
from src.utils.timezone_utils import now_ist
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DeliveryLogRepository:
    def mark_as_delivered(self, user_id: int, question_ids: List[int], db: Session, platform="mobile", delivery_status: NotificationStatus = NotificationStatus.SENT,delivered_at: Optional[datetime] = None) -> bool:
        """
        Mark items as delivered for a user, respecting atomic upserts (no repeats).
        """
        try:
            delivery_timestamp = delivered_at if delivered_at else now_ist()
            new_logs = []
            # --- DEBUG LOGGING START ---
            logger.info(f"Attempting to mark {len(question_ids)} items for user {user_id}. Status enum provided: {delivery_status}, Enum value: {delivery_status.value}")
            # --- DEBUG LOGGING END ---

            for qid in question_ids:
                already = db.query(DeliveryLog).filter(
                    DeliveryLog.user_id == user_id,
                    DeliveryLog.question_id == qid
                ).first()
                if already:
                    logger.info(f"Skipping already delivered item: user={user_id}, question={qid}")
                    continue

                # Prepare the status value explicitly and log it
                status_value_to_insert = delivery_status.value
                # --- DEBUG LOGGING START ---
                logger.info(f"Preparing Log Entry for QID {qid}: user={user_id}, question={qid}, status_value='{status_value_to_insert}' (Type: {type(status_value_to_insert)})")
                # --- DEBUG LOGGING END ---

                # Try creating the object
                try:
                    log = DeliveryLog(
                        user_id=user_id,
                        question_id=qid,
                        delivered_at=delivery_timestamp,
                        platform=platform,
                        # Ensure using the lowercase string value
                        delivery_status=status_value_to_insert,
                        retry_count=0
                    )
                    # --- DEBUG LOGGING START ---
                    # Log the delivery_status attribute *after* object creation but *before* adding to session
                    # This helps check if SQLAlchemy modifies it during object initialization
                    logger.debug(f"Log object created for QID {qid}. delivery_status attribute on object: {log.delivery_status} (Type: {type(log.delivery_status)})")
                    # --- DEBUG LOGGING END ---
                    new_logs.append(log)
                except Exception as create_exc:
                    logger.error(f"Error creating DeliveryLog object for QID {qid}: {create_exc}", exc_info=True)
                    # Optionally re-raise or handle, but this helps isolate the object creation step
                    raise create_exc # Re-raise to see if creation itself fails

            if new_logs:
                logger.info(f"Adding {len(new_logs)} new log entries to session for user {user_id}")
                db.add_all(new_logs)
                logger.info("Session prepared with new logs. Attempting commit...")
                db.commit() # This is where the psycopg2 error likely occurs if the value is wrong at flush time
                logger.info(f"Successfully committed {len(new_logs)} logs for user {user_id}")
            else:
                 logger.info(f"No new logs to add for user {user_id} (all items previously delivered).")
            return True
        except Exception as e:
            # Log the exception with traceback information for commit errors
            logger.error(f"DeliveryLog: failed mark_as_delivered during commit/add for user {user_id}: {e}", exc_info=True)
            try:
                db.rollback() # Attempt rollback
                logger.info("Rollback successful after error.")
            except Exception as rb_exc:
                logger.error(f"Exception during rollback: {rb_exc}", exc_info=True)
            return False

    def get_user_history(self, user, page: int, limit: int, db: Session):
        """
        Get user's 30-day/past delivered content history, respecting overall requirements.
        """
        try:
            from datetime import timedelta, datetime
            from sqlalchemy import and_
            from src.models.question import Question
            from src.utils.timezone_utils import now_ist, today_ist

            thirty_days_ago = now_ist() - timedelta(days=30)
            subscription_start = getattr(user, 'subscription_started_at', None)

            # Ensure subscription_start is timezone-aware if it exists
            if subscription_start and subscription_start.tzinfo is None:
                from src.utils.timezone_utils import to_ist
                subscription_start = to_ist(subscription_start)

            # Determine actual start date for history (later of 30 days ago or subscription start)
            history_start = max(thirty_days_ago, subscription_start) if subscription_start else thirty_days_ago
            # End date should be beginning of today (exclude future items)
            history_end = today_ist()  # today_ist returns a date object

            logger.debug(f"History Query for User {user.id}: Start={history_start}, End={history_end}, Page={page}, Limit={limit}")

            exam_types = getattr(user.preferences, "exam_types", ['General'])
            offset = (page - 1) * limit

            # Query to get Question objects and their corresponding delivered_at timestamp
            content_query = db.query(
                Question,
                DeliveryLog.delivered_at
            ).join(
                DeliveryLog, DeliveryLog.question_id == Question.id
            ).filter(
                and_(
                    DeliveryLog.user_id == user.id,
                    DeliveryLog.delivered_at >= history_start,
                    # Compare date part for history_end since it's a date object
                    DeliveryLog.delivered_at < datetime.combine(history_end, datetime.min.time()).replace(tzinfo=history_start.tzinfo),
                    Question.exam_type.in_(exam_types)
                )
            ).order_by(DeliveryLog.delivered_at.desc())

            # Execute the query with offset and limit
            content_tuples = content_query.offset(offset).limit(limit).all()
            logger.debug(f"History Query for User {user.id}: Found {len(content_tuples)} raw items for page {page}")
            logger.info(f"[DEBUG] Sample tuple structure: {content_tuples[0] if content_tuples else 'EMPTY'}")
            logger.info(f"[DEBUG] First item type: {type(content_tuples[0]) if content_tuples else 'N/A'}")
            if content_tuples:
                first_tuple = content_tuples[0]
                logger.info(f"[DEBUG] Tuple length: {len(first_tuple)}")
                logger.info(f"[DEBUG] Element 0 (Question): {first_tuple[0].id if hasattr(first_tuple[0], 'id') else first_tuple[0]}")
                logger.info(f"[DEBUG] Element 1 (delivered_at): {first_tuple[1] if len(first_tuple) > 1 else 'MISSING'}")
                        # Build formatted list directly from query tuples ensuring delivered_at is correctly matched
            formatted = []
            for q, delivered_at_ts in content_tuples:
                formatted.append({
                    "id": q.id,
                    "content_type": q.content_type,
                    "exam_type": q.exam_type,
                    "title": q.title,
                    "description": q.description,
                    "explanation": q.explanation,
                    "options": q.options,
                    "correct_answer": q.correct_answer,
                    "category": q.category,
                    "date_from": q.date_from.isoformat() if q.date_from else None,
                    "date_to": q.date_to.isoformat() if q.date_to else None,
                    "delivered_at": delivered_at_ts.isoformat() if delivered_at_ts else None,
                    "scheduled_time": None  # History items don't have a future schedule
                })

            facts = [c for c, dt in content_tuples if c.content_type == 'fact']
            questions = [c for c, dt in content_tuples if c.content_type == 'question']

            logger.info(f"Successfully retrieved history page {page} for user {user.id}. Items: {len(formatted)}")

            return {
                'success': True,
                'content': formatted,
                'metadata': {
                    'total_items': len(formatted),  # This is count for the page, not total history
                    'fact_count': len(facts),
                    'question_count': len(questions),
                    'exam_types': exam_types,
                    'subscription_status': user.subscription_status
                }
            }
        except Exception as e:
            logger.error(f"Error getting history for user {user.id}: {e}", exc_info=True)
            return {
                'success': False,
                'content': [],
                'metadata': {
                    'total_items': 0,
                    'fact_count': 0,
                    'question_count': 0,
                    'exam_types': getattr(user.preferences, "exam_types", []) if hasattr(user, 'preferences') else [],
                    'subscription_status': user.subscription_status
                },
                'error': f"Failed fetching user content history: {e}"
            }
