"""
Test Database and Redis Connections
Run before development: python test_connections.py
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.config import settings
from src.database.session import engine
from sqlalchemy import text
import redis

def test_database():
    """Test PostgreSQL with IST timezone"""
    print("\n🔍 Testing PostgreSQL...")
    try:
        with engine.connect() as conn:
            # Check connection
            result = conn.execute(text("SELECT NOW()"))
            row = result.fetchone()
            if row is None:
                print("❌ PostgreSQL returned no rows for SELECT NOW()")
                return False
            db_time = row[0]
            
            # Check timezone
            result = conn.execute(text("SHOW timezone"))
            row = result.fetchone()
            if row is None:
                print("❌ PostgreSQL returned no rows for SHOW timezone")
                return False
            timezone = row[0]
            
            print(f"✅ PostgreSQL Connected!")
            print(f"   Timezone: {timezone}")
            print(f"   Current Time: {db_time}")
            
            if timezone != "Asia/Kolkata":
                print(f"⚠️  WARNING: Expected Asia/Kolkata, got {timezone}")
                return False
            
            return True
    except Exception as e:
        print(f"❌ PostgreSQL Failed: {e}")
        return False

def test_redis():
    """Test Redis connection"""
    print("\n🔍 Testing Redis...")
    try:
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)
        r.ping()
        
        # Test set/get
        r.set("test_key", "test_value")
        value = r.get("test_key")
        r.delete("test_key")
        
        print(f"✅ Redis Connected!")
        # Safely handle the case where REDIS_URL may be None
        url = settings.REDIS_URL if settings.REDIS_URL else "MISSING"
        if url == "MISSING":
            print(f"   URL: {url}")
        else:
            display = url[:40] + ("..." if len(url) > 40 else "")
            print(f"   URL: {display}")
        print(f"   Test read/write: OK")
        return True
    except Exception as e:
        print(f"❌ Redis Failed: {e}")
        return False

def test_env_vars():
    """Check critical env variables"""
    print("\n🔍 Checking Environment Variables...")
    
    required = {
        "DATABASE_URL": settings.DATABASE_URL,
        "REDIS_URL": settings.REDIS_URL,
        "GROQ_API_KEY": (settings.GROQ_API_KEY[:20] + "...") if settings.GROQ_API_KEY else "MISSING",
        "R2_ENDPOINT": settings.R2_ENDPOINT,
        "ADMIN_API_KEY": "***" if settings.ADMIN_API_KEY else "MISSING"
    }
    
    all_ok = True
    for key, value in required.items():
        if value and value != "MISSING":
            print(f"   ✅ {key}: {value[:50]}...")
        else:
            print(f"   ❌ {key}: NOT SET")
            all_ok = False
    
    return all_ok

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 TESTING CONNECTIONS - PHASE 0")
    print("=" * 60)
    
    env_ok = test_env_vars()
    db_ok = test_database()
    redis_ok = test_redis()
    
    print("\n" + "=" * 60)
    if env_ok and db_ok and redis_ok:
        print("✅ ALL TESTS PASSED!")
        print("\n🎉 Ready for PHASE 1: Admin PDF Upload")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        print("\n📝 Fix issues in .env file and try again")
        sys.exit(1)
