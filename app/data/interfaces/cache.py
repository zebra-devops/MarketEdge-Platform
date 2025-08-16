from abc import ABC, abstractmethod
from typing import Any, Optional
from datetime import timedelta


class ICacheManager(ABC):
    """Interface for cache management"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        pass
    
    @abstractmethod
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[timedelta] = None
    ) -> bool:
        """Set value in cache with optional TTL"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        pass
    
    @abstractmethod
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern"""
        pass
    
    @abstractmethod
    async def get_ttl(self, key: str) -> Optional[int]:
        """Get TTL for a key in seconds"""
        pass
    
    @abstractmethod
    def generate_cache_key(
        self, 
        source: str, 
        method: str, 
        **kwargs
    ) -> str:
        """Generate standardized cache key"""
        pass