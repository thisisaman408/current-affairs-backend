# src/core/repositories/content_repository.py
"""
Content Repository
Handles fetching daily content for users
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, not_
from src.models.question import Question
from src.models.delivery_log import DeliveryLog
from datetime import datetime, date
from src.core.repositories.delivery_log_repository import DeliveryLogRepository
import logging
from src.models.delivery_log import NotificationStatus

logger = logging.getLogger(__name__)

class ContentRepository:
    """Repository for daily content operations"""

    def get_undelivered_questions(
        self,
        user_id: int,
        exam_types: List[str],
        limit: int,
        fact_count: int,
        question_count: int,
        db: Session,
    ) -> List[Question]:
        """
        Get the newest undelivered facts/questions for a specific user.
        1. Never returns a question already delivered to this user (DeliveryLog)
        2. Respects exam_types.
        3. Respects fact_count/question_count ratio. Will always return at least one of each if possible.
        """
        try:
            # Subquery of all delivered for user
            delivered_ids = db.query(DeliveryLog.question_id).filter(
                DeliveryLog.user_id == user_id
            ).distinct()
            logger.info(f"The fact count here is : {fact_count} and question count is : {question_count}")
            # Fetch facts: newest first, not delivered, for allowed exams
            facts_query = (
                db.query(Question)
                .filter(and_(
                    Question.exam_type.in_(exam_types),
                    Question.content_type == 'fact',
                    not_(Question.id.in_(delivered_ids))
                ))
                .order_by(Question.created_at.desc())
                .limit(fact_count)
            )

            # Fetch questions: newest first, not delivered, for allowed exams
            questions_query = (
                db.query(Question)
                .filter(and_(
                    Question.exam_type.in_(exam_types),
                    Question.content_type == 'question',
                    not_(Question.id.in_(delivered_ids))
                ))
                .order_by(Question.created_at.desc())
                .limit(question_count)
            )

            facts = facts_query.all()
            questions = questions_query.all()

            content = facts + questions  # preserves facts-first
            logger.info(f"✅ {len(content)} (facts={len(facts)}, questions={len(questions)}) found for user {user_id}")
            return content

        except Exception as e:
            logger.error(f"❌ Failed in get_undelivered_questions: {e}")
            return []

    def mark_as_delivered(self, user_id: int, question_ids: List[int], db: Session,delivered_at: Optional[datetime] = None) -> bool:
        """
        Uses DeliveryLogRepository for robust delivery marking (atomic, NO repeats).
        """
        try:
            delivery_repo = DeliveryLogRepository()
            return delivery_repo.mark_as_delivered(
                user_id=user_id,
                question_ids=question_ids,
                db=db,
                platform='mobile',
                delivery_status=NotificationStatus.SENT,
                delivered_at=delivered_at 
            )
        except Exception as e:
            logger.error(f"Failed to mark as delivered for user {user_id}: {e}")
            return False

    def get_total_available_content(
        self,
        exam_types: List[str],
        db: Session
    ) -> dict:
        """
        Get total available content count by type
        
        Args:
            exam_types: List of exam types
            db: Database session
            
        Returns:
            Dict with fact_count and question_count
        """
        try:
            fact_count = db.query(Question).filter(
                and_(
                    Question.exam_type.in_(exam_types),
                    Question.content_type == 'fact'
                )
            ).count()

            question_count = db.query(Question).filter(
                and_(
                    Question.exam_type.in_(exam_types),
                    Question.content_type == 'question'
                )
            ).count()

            return {
                "fact_count": fact_count,
                "question_count": question_count,
                "total": fact_count + question_count
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get available content: {e}")
            return {"fact_count": 0, "question_count": 0, "total": 0}