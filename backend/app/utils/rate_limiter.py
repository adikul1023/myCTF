"""
Rate Limiter - In-memory rate limiting with sliding window.

For production, this should be replaced with Redis-based rate limiting.
This implementation is suitable for single-instance deployments.
"""

import asyncio
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Tuple


class RateLimiter:
    """
    In-memory rate limiter using sliding window algorithm.
    
    For production deployments with multiple instances,
    replace this with a Redis-based implementation.
    """
    
    def __init__(
        self,
        requests_per_minute: int = 10,
        key_prefix: str = "default",
    ):
        """
        Initialize the rate limiter.
        
        Args:
            requests_per_minute: Maximum requests allowed per minute.
            key_prefix: Prefix for rate limit keys.
        """
        self.requests_per_minute = requests_per_minute
        self.key_prefix = key_prefix
        self.window_size = 60  # seconds
        
        # Storage: key -> list of timestamps
        self._requests: Dict[str, List[float]] = defaultdict(list)
        self._lock = asyncio.Lock()
    
    async def is_allowed(self, key: str) -> bool:
        """
        Check if a request is allowed under the rate limit.
        
        Args:
            key: The rate limit key (e.g., user_id or IP).
        
        Returns:
            True if the request is allowed, False otherwise.
        """
        full_key = f"{self.key_prefix}:{key}"
        now = datetime.now(timezone.utc).timestamp()
        window_start = now - self.window_size
        
        async with self._lock:
            # Clean up old requests outside the window
            self._requests[full_key] = [
                ts for ts in self._requests[full_key]
                if ts > window_start
            ]
            
            # Check if under limit
            if len(self._requests[full_key]) >= self.requests_per_minute:
                return False
            
            # Add current request
            self._requests[full_key].append(now)
            return True
    
    async def get_remaining(self, key: str) -> Tuple[int, float]:
        """
        Get remaining requests and time until reset.
        
        Args:
            key: The rate limit key.
        
        Returns:
            Tuple of (remaining requests, seconds until oldest expires)
        """
        full_key = f"{self.key_prefix}:{key}"
        now = datetime.now(timezone.utc).timestamp()
        window_start = now - self.window_size
        
        async with self._lock:
            # Clean up old requests
            self._requests[full_key] = [
                ts for ts in self._requests[full_key]
                if ts > window_start
            ]
            
            current_count = len(self._requests[full_key])
            remaining = max(0, self.requests_per_minute - current_count)
            
            if self._requests[full_key]:
                oldest = min(self._requests[full_key])
                reset_in = max(0, oldest + self.window_size - now)
            else:
                reset_in = 0.0
            
            return remaining, reset_in
    
    async def reset(self, key: str) -> None:
        """
        Reset rate limit for a key.
        
        Args:
            key: The rate limit key.
        """
        full_key = f"{self.key_prefix}:{key}"
        async with self._lock:
            self._requests.pop(full_key, None)
    
    async def cleanup(self) -> int:
        """
        Clean up expired entries from all keys.
        
        Returns:
            Number of keys cleaned up.
        """
        now = datetime.now(timezone.utc).timestamp()
        window_start = now - self.window_size
        cleaned = 0
        
        async with self._lock:
            keys_to_remove = []
            
            for key, timestamps in self._requests.items():
                # Filter out expired timestamps
                valid = [ts for ts in timestamps if ts > window_start]
                
                if not valid:
                    keys_to_remove.append(key)
                    cleaned += 1
                else:
                    self._requests[key] = valid
            
            for key in keys_to_remove:
                del self._requests[key]
        
        return cleaned


# Background task to periodically clean up expired entries
async def rate_limiter_cleanup_task(
    limiter: RateLimiter,
    interval: int = 300,  # 5 minutes
) -> None:
    """
    Background task to periodically clean up expired rate limit entries.
    
    Args:
        limiter: The RateLimiter instance.
        interval: Cleanup interval in seconds.
    """
    while True:
        await asyncio.sleep(interval)
        await limiter.cleanup()
