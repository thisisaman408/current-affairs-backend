"""
Worker 1: PDF Text Extraction
Listens to: pdf_processing_queue
Outputs to: ai_processing_queue
"""
import sys
import os
from dotenv import load_dotenv
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
backend_dir = Path(__file__).parent.parent
load_dotenv(backend_dir / '.env')
import fitz  
import tempfile
from src.integrations.redis_queue import redis_queue
from src.integrations.r2_storage import r2_storage
from src.database.session import SessionLocal
from src.core.repositories.pdf_job_repository import PDFJobRepository
import logging
import time
import re
from src.models.user import User
from src.models.subscription_history import SubscriptionHistory
from src.models.user_preferences import UserPreferences
from src.models.device_token import DeviceToken
from src.models.delivery_log import DeliveryLog
from src.models.pdf_job import PDFJob
from src.models.question import Question

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

class PDFProcessor:
    """Extract and chunk PDF text"""
    
    def extract_text(self, pdf_path: str) -> str:
        """Extract all text from PDF"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            logger.info(f"✅ Extracted {len(text)} characters from PDF")
            return text
        except Exception as e:
            logger.error(f"❌ PDF extraction failed: {e}")
            return ""
    
    def chunk_by_topics(self, text: str) -> list[str]:
        """
        Split text into topic chunks
        Looks for numbered sections like "2.1 TOPIC NAME"
        """
        chunks = []
        current_chunk = []
        
        lines = text.split('\n')
        for line in lines:
            # Detect topic headers (e.g., "2.1. INDIA-CHINA")
            if re.match(r'^\d+\.\d+\.?\s+[A-Z]', line):
                if current_chunk:
                    chunk_text = '\n'.join(current_chunk)
                    if len(chunk_text) > 200:  # Skip tiny chunks
                        chunks.append(chunk_text)
                current_chunk = [line]
            else:
                current_chunk.append(line)
        
        # Add last chunk
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            if len(chunk_text) > 200:
                chunks.append(chunk_text)
        
        logger.info(f"✅ Split into {len(chunks)} topic chunks")
        return chunks
    
    def process_job(self, job_data: dict):
        """Main processing logic"""
        job_id = job_data['job_id']
        r2_key = job_data['r2_key']
        
        logger.info(f"🔄 Processing Job {job_id}...")
        
        # Update status to processing
        db = SessionLocal()
        repo = PDFJobRepository(db)
        repo.mark_processing(job_id)
        
        try:
            # Download PDF from R2
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                tmp_path = tmp.name
                r2_storage.download_pdf(r2_key, tmp_path)
                logger.info(f"✅ Downloaded PDF to {tmp_path}")
            
            # Extract text
            full_text = self.extract_text(tmp_path)
            
            if not full_text:
                raise Exception("No text extracted from PDF")
            
            # Chunk into topics
            chunks = self.chunk_by_topics(full_text)
            
            if not chunks:
                # If no structured topics, split by size
                chunk_size = 3000
                chunks = [full_text[i:i+chunk_size] for i in range(0, len(full_text), chunk_size)]
                logger.info(f"✅ Created {len(chunks)} size-based chunks")
            
            # Push each chunk to AI processing queue
            for idx, chunk in enumerate(chunks):
                ai_job = {
                    "job_id": job_id,
                    "chunk_index": idx,
                    "total_chunks": len(chunks),
                    "text": chunk[:5000],  # Limit chunk size
                    "exam_types": job_data['exam_types'],
                    "date_from": job_data['date_from'],
                    "date_to": job_data['date_to']
                }
                redis_queue.push("ai_processing_queue", ai_job)
            
            logger.info(f"✅ Job {job_id}: Queued {len(chunks)} chunks for AI processing")
            
            # Clean up
            os.unlink(tmp_path)
            
        except Exception as e:
            logger.error(f"❌ Job {job_id} failed: {e}")
            repo.update_status(job_id, "failed", str(e))
        finally:
            db.close()
    
    def run(self):
        """Main worker loop"""
        logger.info("🚀 PDF Processor Worker started")
        logger.info("👂 Listening to: pdf_processing_queue")
        
        while True:
            try:
                job = redis_queue.pop("pdf_processing_queue", timeout=5)
                if job:
                    self.process_job(job)
                else:
                    time.sleep(1)  # No jobs, wait a bit
            except KeyboardInterrupt:
                logger.info("🛑 Worker stopped")
                break
            except Exception as e:
                logger.error(f"❌ Worker error: {e}")
                time.sleep(5)

if __name__ == "__main__":
    processor = PDFProcessor()
    processor.run()
