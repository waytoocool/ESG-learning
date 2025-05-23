# services/redis.py
import redis
import time
from flask import current_app

# Global redis client instance
redis_client = None

def init_redis(app):
    """
    Initialize Redis connection
    
    Args:
        app: Flask application instance
    """
    global redis_client
    
    redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
    redis_client = redis.Redis.from_url(
        redis_url,
        decode_responses=True,
        socket_timeout=5
    )
    
    # Test the connection
    try:
        redis_client.ping()
        app.logger.info("Redis connection established")
    except redis.ConnectionError as e:
        app.logger.error(f"Redis connection failed: {str(e)}")
        redis_client = None

def check_rate_limit(email, limit_key='verification_attempt', timeout=900):  # 15 minutes
    """
    Check if an email has hit the rate limit
    
    Args:
        email (str): Email to check
        limit_key (str): Key prefix for rate limiting
        timeout (int): Time in seconds before rate limit resets
    
    Returns:
        tuple: (bool, str) - (can_send, error_message)
    """
    if not redis_client:
        # Fallback if Redis is unavailable - allow the action
        return True, None
        
    try:
        rate_limit_key = f'{limit_key}:{email}'
        
        # Check existing attempt
        last_attempt = redis_client.get(rate_limit_key)
        if last_attempt:
            last_attempt_time = int(last_attempt)
            current_time = int(time.time())
            time_passed = current_time - last_attempt_time
            
            if time_passed < timeout:
                minutes_remaining = (timeout - time_passed) // 60
                return False, f'Please wait {minutes_remaining} minutes before trying again.'
        
        # Set new timestamp
        redis_client.setex(rate_limit_key, timeout, int(time.time()))
        return True, None
        
    except redis.ConnectionError as e:
        current_app.logger.error(f"Redis error in rate limit check: {str(e)}")
        # Fallback - allow the action
        return True, None

def get_redis_client():
    """
    Get the Redis client instance
    
    Returns:
        redis.Redis: Redis client instance or None if not initialized
    """
    return redis_client
