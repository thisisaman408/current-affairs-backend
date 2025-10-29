"""
Redis Queue Client
Simple queue operations for job processing
"""
import redis
import json
from src.config import settings
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class RedisQueue:
    """Redis queue handler"""
    
    def __init__(self):
        self.client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )
        logger.info("✅ Redis Queue initialized")
    
    def push(self, queue_name: str, job_data: dict) -> bool:
        """Push job to queue"""
        try:
            job_json = json.dumps(job_data)
            self.client.rpush(queue_name, job_json)
            logger.info(f"✅ Pushed to {queue_name}: Job {job_data.get('job_id')}")
            return True
        except Exception as e:
            logger.error(f"❌ Queue push failed: {e}")
            return False
    
    def pop(self, queue_name: str, timeout: int = 5) -> Optional[dict]:
        """Pop job from queue (blocking)"""
        try:
            # blpop returns tuple: (queue_name, value) or None
            result = self.client.blpop([queue_name], timeout=timeout)
            
            if result:
                # result[1] is the job JSON string
                job_json = result[1]
                return json.loads(job_json)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Queue pop failed: {e}")
            return None
    
    def length(self, queue_name: str) -> int:
        """Get queue length"""
        try:
            return int(self.client.llen(queue_name))
        except Exception as e:
            logger.error(f"❌ Queue length failed: {e}")
            return 0

# Global instance
redis_queue = RedisQueue()