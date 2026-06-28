"""
Copyright (c) 2026 Clove Twilight
Licensed under the ESAL-1.3 Licence.
See LICENCE.md in the project root for full licence information.
"""

"""
Simple in-memory caching utility
"""

import time
from typing import Any, Optional

_cache = {}

def get_from_cache(key: str) -> Optional[Any]:
    """
    Get a value from cache if it exists and hasn't expired
    
    Args:
        key: Cache key
    
    Returns:
        Cached value or None if expired/not found
    """
    if key in _cache:
        value, expire_time = _cache[key]
        if time.time() < expire_time:
            return value
        else:
            del _cache[key]  # Clean up expired entry
    return None

def set_in_cache(key: str, value: Any, ttl: int = 30):
    """
    Set a value in cache with TTL
    
    Args:
        key: Cache key
        value: Value to cache
        ttl: Time to live in seconds (default: 30)
    """
    expire_time = time.time() + ttl
    _cache[key] = (value, expire_time)

def clear_cache(key: Optional[str] = None):
    """
    Clear cache entry or entire cache
    
    Args:
        key: Specific key to clear, or None to clear all
    """
    if key:
        _cache.pop(key, None)
    else:
        _cache.clear()