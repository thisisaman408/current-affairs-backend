"""
Complete Cleanup Script
Clears Redis + Database for fresh start
"""
import redis
from src.config import settings
from src.database.session import SessionLocal, engine
from src.models.pdf_job import PDFJob
from src.models.question import Question
from sqlalchemy import text

print("🧹 Starting complete cleanup...\n")

# 1. Clear Redis
print("📦 Clearing Redis...")
r = redis.from_url(settings.REDIS_URL, decode_responses=True)
r.flushall()
print("✅ Redis flushed!\n")

# 2. Clear Database Tables
print("🗄️  Clearing Database...")
db = SessionLocal()

try:
    # Delete all questions
    questions_deleted = db.query(Question).delete()
    print(f"   Deleted {questions_deleted} questions")
    
    # Delete all PDF jobs
    jobs_deleted = db.query(PDFJob).delete()
    print(f"   Deleted {jobs_deleted} PDF jobs")
    
    db.commit()
    print("✅ Database cleared!\n")
    
except Exception as e:
    print(f"❌ Database cleanup failed: {e}")
    db.rollback()
finally:
    db.close()

# 3. Verify cleanup
print("🔍 Verifying cleanup...")
db = SessionLocal()
question_count = db.query(Question).count()
job_count = db.query(PDFJob).count()
redis_keys = r.keys("*")

print(f"   Questions in DB: {question_count}")
print(f"   PDF Jobs in DB: {job_count}")
print(f"   Redis keys: {len(redis_keys)}")

if question_count == 0 and job_count == 0 and len(redis_keys) == 0:
    print("\n✅ CLEANUP SUCCESSFUL! Ready for fresh start 🎉")
else:
    print("\n⚠️  Some data still exists")

db.close()
