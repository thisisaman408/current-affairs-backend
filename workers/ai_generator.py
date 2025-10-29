"""
Worker 2: AI Content Generation
Smart rate limiting based on mode
"""
import sys
import os
from dotenv import load_dotenv
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
backend_dir = Path(__file__).parent.parent
load_dotenv(backend_dir / '.env')
# ✅ IMPORT MODELS FIRST!
import src.models

from src.integrations.redis_queue import redis_queue
from src.integrations.groq_client import groq_client
from src.database.session import SessionLocal
from src.models.question import Question
from src.core.repositories.pdf_job_repository import PDFJobRepository
from src.config import settings
from datetime import datetime
import logging
import time

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)


class AIGenerator:
    """Generate rich Hinglish content using Groq"""
    
    def __init__(self):
        # Smart delay based on mode
        if settings.PROCESSING_MODE == "slow":
            self.delay = settings.CHUNK_DELAY_SECONDS
            logger.info(f"🐢 SLOW MODE: {self.delay}s per chunk (production-safe)")
        else:
            self.delay = settings.FAST_CHUNK_DELAY_SECONDS
            logger.info(f"🚀 FAST MODE: {self.delay}s per chunk (testing)")
    
    def process_chunk(self, job_data: dict):
        """Process one text chunk with Groq"""
        job_id = job_data['job_id']
        chunk_idx = job_data['chunk_index']
        total = job_data['total_chunks']
        
        logger.info(f"🤖 Processing Job {job_id}, Chunk {chunk_idx+1}/{total}")
        
        # Calculate ETA
        remaining = total - chunk_idx
        eta_mins = (remaining * self.delay) / 60
        logger.info(f"⏱️  ETA for this job: {eta_mins:.1f} minutes")
        
        db = SessionLocal()
        
        try:
            # Generate content with Groq
            items = groq_client.generate_content(
                text_chunk=job_data['text'],
                exam_types=job_data['exam_types'],
                date_from=job_data['date_from'],
                date_to=job_data['date_to']
            )
            
            if not items:
                logger.warning(f"⚠️ No items generated for chunk {chunk_idx+1}")
                return
            
            # Save to database with NEW FIELDS
            facts_count = 0
            questions_count = 0
            
            for item in items:
                # Validate item structure
                if not item.get('text') or not item.get('type'):
                    logger.warning(f"⚠️ Invalid item structure: {item}")
                    continue
                
                # Create question/fact with ALL fields
                question = Question(
                    text=item.get('text', '')[:200],  # Short version
                    title=item.get('title', None),  # Hindi title
                    description=item.get('description', item.get('text', '')),  # Detailed Hinglish
                    explanation=item.get('explanation', None),  # Why/How explanation
                    options=item.get('options', None),  # For MCQs only
                    correct_answer=item.get('correct_answer', None),  # For MCQs only
                    content_type=item.get('type', 'fact'),
                    exam_type=item.get('exam', job_data['exam_types'][0]),
                    category=item.get('category', 'General'),
                    date_from=datetime.strptime(job_data['date_from'], "%Y-%m-%d").date(),
                    date_to=datetime.strptime(job_data['date_to'], "%Y-%m-%d").date(),
                    source_pdf_id=job_id
                )
                db.add(question)
                
                if item.get('type') == 'fact':
                    facts_count += 1
                else:
                    questions_count += 1
            
            db.commit()
            logger.info(f"✅ Saved {facts_count} facts + {questions_count} questions")
            
            # Smart delay
            logger.info(f"😴 Sleeping {self.delay}s to respect rate limits...")
            time.sleep(self.delay)
            
        except Exception as e:
            logger.error(f"❌ Chunk processing failed: {e}")
            db.rollback()
        finally:
            db.close()
    
    def run(self):
        """Main worker loop"""
        logger.info("🚀 AI Generator Worker started")
        logger.info("👂 Listening to: ai_processing_queue")
        logger.info(f"⚙️  Mode: {settings.PROCESSING_MODE.upper()}")
        logger.info(f"⏱️  Delay: {self.delay}s per chunk")
        
        if settings.PROCESSING_MODE == "slow":
            logger.info("📋 Production mode - safe & stable!")
            logger.info("   ✅ No rate limit errors")
            logger.info("   ✅ Monthly PDFs processed overnight")
            logger.info("   ✅ Free Groq tier stays safe")
        
        while True:
            try:
                job = redis_queue.pop("ai_processing_queue", timeout=5)
                if job:
                    self.process_chunk(job)
                else:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("🛑 Worker stopped")
                break
            except Exception as e:
                logger.error(f"❌ Worker error: {e}")
                time.sleep(5)


if __name__ == "__main__":
    generator = AIGenerator()
    generator.run()
