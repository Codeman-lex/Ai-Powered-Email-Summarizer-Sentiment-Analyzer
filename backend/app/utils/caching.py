import os
import functools
import json
import hashlib
import time
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, cast
import structlog
import redis

logger = structlog.get_logger(__name__)

# Redis client setup with connection pooling
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Connection pool
redis_pool = redis.ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    db=REDIS_DB,
    socket_timeout=5,
    socket_connect_timeout=5,
    decode_responses=True,
)

# Redis client
redis_client = redis.Redis(connection_pool=redis_pool)

# Define function return type
F = TypeVar('F', bound=Callable[..., Any])


def is_cache_enabled() -> bool:
    """Check if caching is enabled."""
    return os.getenv("ENABLE_EMAIL_CACHE", "True").lower() == "true"


def generate_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """Generate a cache key based on function name and arguments."""
    # Create a string representation of args and kwargs
    key_parts = [func_name]
    
    # Add positional args
    for arg in args:
        key_parts.append(str(arg))
    
    # Add keyword args (sorted for consistency)
    sorted_items = sorted(kwargs.items())
    for k, v in sorted_items:
        key_parts.append(f"{k}:{v}")
    
    # Join parts and hash
    key_string = "_".join(key_parts)
    return f"intellimail:cache:{hashlib.md5(key_string.encode()).hexdigest()}"


def serialize_for_cache(obj: Any) -> str:
    """Serialize an object for caching."""
    try:
        return json.dumps(obj)
    except (TypeError, ValueError):
        logger.warning("Could not serialize object for caching", obj_type=type(obj).__name__)
        raise ValueError(f"Object of type {type(obj).__name__} is not JSON serializable")


def deserialize_from_cache(data: str) -> Any:
    """Deserialize an object from cache."""
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        logger.warning("Could not deserialize cached data", data_sample=data[:100])
        return None


def cache(ttl: int = 3600) -> Callable[[F], F]:
    """
    Cache decorator for functions.
    
    Args:
        ttl: Time-to-live in seconds (default: 1 hour)
        
    Usage:
        @cache(ttl=300)  # Cache for 5 minutes
        def expensive_function(arg1, arg2):
            # ...
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not is_cache_enabled():
                return func(*args, **kwargs)
            
            # Generate cache key
            cache_key = generate_cache_key(func.__name__, args, kwargs)
            
            # Try to get from cache
            try:
                cached_value = redis_client.get(cache_key)
                if cached_value:
                    logger.debug("Cache hit", key=cache_key, func=func.__name__)
                    return deserialize_from_cache(cached_value)
                
                logger.debug("Cache miss", key=cache_key, func=func.__name__)
            except redis.RedisError as e:
                logger.error("Redis error when getting cache", error=str(e), func=func.__name__)
                return func(*args, **kwargs)
                
            # Call the original function
            start_time = time.time()
            result = func(*args, **kwargs)
            exec_time = time.time() - start_time
            
            # Cache the result
            try:
                serialized = serialize_for_cache(result)
                redis_client.setex(cache_key, ttl, serialized)
                logger.debug(
                    "Cached function result", 
                    key=cache_key, 
                    func=func.__name__, 
                    ttl=ttl, 
                    exec_time=exec_time
                )
            except (ValueError, redis.RedisError) as e:
                logger.error(
                    "Failed to cache result", 
                    error=str(e), 
                    func=func.__name__,
                    result_type=type(result).__name__
                )
                
            return result
            
        return cast(F, wrapper)
    
    return decorator


def invalidate_cache(pattern: str) -> int:
    """
    Invalidate cached items matching a pattern.
    
    Args:
        pattern: Redis key pattern to match
        
    Returns:
        Number of keys deleted
    """
    try:
        keys = redis_client.keys(f"intellimail:cache:{pattern}*")
        if keys:
            count = redis_client.delete(*keys)
            logger.info("Invalidated cache keys", pattern=pattern, count=count)
            return count
        return 0
    except redis.RedisError as e:
        logger.error("Redis error when invalidating cache", error=str(e), pattern=pattern)
        return 0


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    try:
        info = redis_client.info()
        key_count = len(redis_client.keys("intellimail:cache:*"))
        
        return {
            "total_keys": key_count,
            "memory_used": info.get("used_memory_human", "unknown"),
            "hits": info.get("keyspace_hits", 0),
            "misses": info.get("keyspace_misses", 0),
            "uptime": info.get("uptime_in_seconds", 0),
        }
    except redis.RedisError as e:
        logger.error("Redis error when getting cache stats", error=str(e))
        return {
            "error": str(e),
            "status": "unavailable"
        } 