"""
Caching and rate limiting system for Pundora.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import hashlib
import sqlite3
from collections import defaultdict, deque

class RateLimiter:
    """Rate limiting implementation."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        """Initialize rate limiter."""
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)
    
    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed."""
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        while self.requests[key] and self.requests[key][0] < window_start:
            self.requests[key].popleft()
        
        # Check if under limit
        if len(self.requests[key]) < self.max_requests:
            self.requests[key].append(now)
            return True
        
        return False
    
    def get_remaining_requests(self, key: str) -> int:
        """Get remaining requests for key."""
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        while self.requests[key] and self.requests[key][0] < window_start:
            self.requests[key].popleft()
        
        return max(0, self.max_requests - len(self.requests[key]))
    
    def get_reset_time(self, key: str) -> float:
        """Get time when rate limit resets."""
        if not self.requests[key]:
            return time.time()
        
        return self.requests[key][0] + self.window_seconds

class JokeCache:
    """Joke caching system."""
    
    def __init__(self, db_path: str = "pundora_cache.db"):
        """Initialize joke cache."""
        self.db_path = db_path
        self.memory_cache = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
        self.init_cache_db()
    
    def init_cache_db(self):
        """Initialize cache database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS joke_cache (
                cache_key TEXT PRIMARY KEY,
                joke_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at ON joke_cache(created_at)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_last_accessed ON joke_cache(last_accessed)
        """)
        
        conn.commit()
        conn.close()
    
    def _generate_cache_key(self, category: str, humor_level: str, custom_prompt: str = None) -> str:
        """Generate cache key for joke parameters."""
        key_data = f"{category}:{humor_level}:{custom_prompt or ''}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get_cached_joke(self, category: str, humor_level: str, custom_prompt: str = None) -> Optional[Dict[str, Any]]:
        """Get cached joke if available."""
        cache_key = self._generate_cache_key(category, humor_level, custom_prompt)
        
        # Check memory cache first
        if cache_key in self.memory_cache:
            self.cache_stats['hits'] += 1
            return self.memory_cache[cache_key]
        
        # Check database cache
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT joke_data, access_count FROM joke_cache WHERE cache_key = ?
        """, (cache_key,))
        
        row = cursor.fetchone()
        if row:
            joke_data = json.loads(row[0])
            access_count = row[1] + 1
            
            # Update access count and last accessed
            cursor.execute("""
                UPDATE joke_cache 
                SET access_count = ?, last_accessed = CURRENT_TIMESTAMP
                WHERE cache_key = ?
            """, (access_count, cache_key))
            
            conn.commit()
            conn.close()
            
            # Store in memory cache
            self.memory_cache[cache_key] = joke_data
            self.cache_stats['hits'] += 1
            
            return joke_data
        
        conn.close()
        self.cache_stats['misses'] += 1
        return None
    
    async def cache_joke(self, joke_data: Dict[str, Any], category: str, humor_level: str, custom_prompt: str = None):
        """Cache a joke."""
        cache_key = self._generate_cache_key(category, humor_level, custom_prompt)
        
        # Store in memory cache
        self.memory_cache[cache_key] = joke_data
        
        # Store in database cache
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO joke_cache (cache_key, joke_data)
            VALUES (?, ?)
        """, (cache_key, json.dumps(joke_data)))
        
        conn.commit()
        conn.close()
        
        # Clean up old cache entries if memory cache is too large
        if len(self.memory_cache) > 1000:
            await self._cleanup_memory_cache()
    
    async def _cleanup_memory_cache(self):
        """Clean up old memory cache entries."""
        # Remove oldest 20% of entries
        entries_to_remove = len(self.memory_cache) // 5
        if entries_to_remove > 0:
            # Simple cleanup - remove first entries (FIFO)
            keys_to_remove = list(self.memory_cache.keys())[:entries_to_remove]
            for key in keys_to_remove:
                del self.memory_cache[key]
            
            self.cache_stats['evictions'] += entries_to_remove
    
    async def cleanup_old_cache(self, max_age_hours: int = 24):
        """Clean up old cache entries from database."""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM joke_cache WHERE created_at < ?
        """, (cutoff_time,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted_count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = self.cache_stats['hits'] / total_requests if total_requests > 0 else 0
        
        return {
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'hit_rate': round(hit_rate, 3),
            'evictions': self.cache_stats['evictions'],
            'memory_cache_size': len(self.memory_cache)
        }
    
    async def clear_cache(self):
        """Clear all cache."""
        self.memory_cache.clear()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM joke_cache")
        
        conn.commit()
        conn.close()
        
        self.cache_stats = {'hits': 0, 'misses': 0, 'evictions': 0}

class APICache:
    """API response caching."""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        """Initialize API cache."""
        self.cache = {}
        self.default_ttl = default_ttl
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired."""
        return time.time() > entry['expires_at']
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value."""
        if key in self.cache:
            entry = self.cache[key]
            if not self._is_expired(entry):
                return entry['value']
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set cached value."""
        ttl = ttl or self.default_ttl
        self.cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl
        }
    
    def delete(self, key: str) -> None:
        """Delete cached value."""
        if key in self.cache:
            del self.cache[key]
    
    def clear(self) -> None:
        """Clear all cache."""
        self.cache.clear()
    
    def cleanup_expired(self) -> int:
        """Remove expired entries."""
        expired_keys = [
            key for key, entry in self.cache.items()
            if self._is_expired(entry)
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        return len(expired_keys)

class CacheManager:
    """Centralized cache management."""
    
    def __init__(self):
        """Initialize cache manager."""
        self.joke_cache = JokeCache()
        self.api_cache = APICache()
        self.rate_limiter = RateLimiter()
        
        # Start cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def _cleanup_loop(self):
        """Background cleanup loop."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                await self.joke_cache.cleanup_old_cache()
                self.api_cache.cleanup_expired()
            except Exception as e:
                print(f"Cache cleanup error: {e}")
    
    async def get_cached_joke(self, category: str, humor_level: str, custom_prompt: str = None) -> Optional[Dict[str, Any]]:
        """Get cached joke."""
        return await self.joke_cache.get_cached_joke(category, humor_level, custom_prompt)
    
    async def cache_joke(self, joke_data: Dict[str, Any], category: str, humor_level: str, custom_prompt: str = None):
        """Cache joke."""
        await self.joke_cache.cache_joke(joke_data, category, humor_level, custom_prompt)
    
    def get_cached_api_response(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Any]:
        """Get cached API response."""
        key = f"{endpoint}:{json.dumps(params or {}, sort_keys=True)}"
        return self.api_cache.get(key)
    
    def cache_api_response(self, endpoint: str, params: Dict[str, Any], response: Any, ttl: int = None):
        """Cache API response."""
        key = f"{endpoint}:{json.dumps(params or {}, sort_keys=True)}"
        self.api_cache.set(key, response, ttl)
    
    def is_rate_limited(self, key: str) -> bool:
        """Check if key is rate limited."""
        return not self.rate_limiter.is_allowed(key)
    
    def get_rate_limit_info(self, key: str) -> Dict[str, Any]:
        """Get rate limit information."""
        return {
            'allowed': self.rate_limiter.is_allowed(key),
            'remaining': self.rate_limiter.get_remaining_requests(key),
            'reset_time': self.rate_limiter.get_reset_time(key)
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        return {
            'joke_cache': self.joke_cache.get_cache_stats(),
            'api_cache_size': len(self.api_cache.cache),
            'rate_limiter_requests': sum(len(requests) for requests in self.rate_limiter.requests.values())
        }
    
    async def shutdown(self):
        """Shutdown cache manager."""
        if hasattr(self, 'cleanup_task'):
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass