import os
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class SupabaseConfig(BaseModel):
    """Supabase configuration"""
    url: str = Field(..., description="Supabase project URL")
    key: str = Field(..., description="Supabase anon/service key")
    schema: str = Field(default="public", description="Database schema to use")


class RedisConfig(BaseModel):
    """Redis cache configuration"""
    enabled: bool = Field(default=True, description="Enable Redis caching")
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    default_ttl: int = Field(default=3600, description="Default TTL in seconds")
    key_prefix: str = Field(default="data_layer:", description="Key prefix for cache entries")


class DatabaseConfig(BaseModel):
    """Database configuration for fallback PostgreSQL"""
    enabled: bool = Field(default=False, description="Enable PostgreSQL fallback")
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    database: str = Field(..., description="Database name")
    username: str = Field(..., description="Database username")
    password: str = Field(..., description="Database password")
    pool_size: int = Field(default=5, description="Connection pool size")


class DatabricksConfig(BaseModel):
    """Databricks configuration for analytics"""
    enabled: bool = Field(default=False, description="Enable Databricks integration")
    server_hostname: Optional[str] = Field(None, description="Databricks server hostname")
    http_path: Optional[str] = Field(None, description="Databricks HTTP path")
    access_token: Optional[str] = Field(None, description="Databricks access token")


class RoutingConfig(BaseModel):
    """Query routing configuration"""
    default_source: str = Field(default="supabase", description="Default data source")
    enable_fallback: bool = Field(default=True, description="Enable fallback routing")
    health_check_interval: int = Field(default=60, description="Health check interval in seconds")


class DataLayerSettings(BaseSettings):
    """Main data layer configuration settings"""
    
    # Data source configurations
    supabase: Optional[SupabaseConfig] = None
    redis: RedisConfig = Field(default_factory=RedisConfig)
    database: Optional[DatabaseConfig] = None
    databricks: Optional[DatabricksConfig] = None
    
    # Routing configuration
    routing: RoutingConfig = Field(default_factory=RoutingConfig)
    
    # Performance settings
    query_timeout: int = Field(default=30, description="Query timeout in seconds")
    max_concurrent_queries: int = Field(default=10, description="Max concurrent queries")
    
    # Logging
    log_queries: bool = Field(default=True, description="Log all queries")
    log_performance: bool = Field(default=True, description="Log performance metrics")
    
    class Config:
        env_prefix = "DATA_LAYER_"
        env_nested_delimiter = "__"


def create_data_layer_config() -> Dict[str, Any]:
    """Create data layer configuration from environment variables"""
    try:
        # Check if data layer should be enabled
        data_layer_enabled = os.getenv("DATA_LAYER_ENABLED", "false").lower() == "true"
        
        if not data_layer_enabled:
            # Return minimal configuration for disabled data layer
            return {
                "enabled": False,
                "sources": {},
                "cache": {"enabled": False},
                "routing": {"default_source": None, "enable_fallback": False},
                "performance": {"query_timeout": 30, "max_concurrent_queries": 10},
                "logging": {"log_queries": False, "log_performance": False}
            }
        
        # Check if Supabase configuration is available
        supabase_url = os.getenv("DATA_LAYER_SUPABASE__URL", "")
        supabase_key = os.getenv("DATA_LAYER_SUPABASE__KEY", "")
        
        # Create settings - only create Supabase config if credentials are available
        supabase_config = None
        if supabase_url and supabase_key:
            supabase_config = SupabaseConfig(
                url=supabase_url,
                key=supabase_key,
                schema=os.getenv("DATA_LAYER_SUPABASE__SCHEMA", "public")
            )
        
        # Create settings with optional Supabase
        if supabase_config:
            settings = DataLayerSettings(supabase=supabase_config)
        else:
            # Data layer enabled but no Supabase - use fallback configuration
            return get_fallback_config()
        
        # Build configuration dictionary
        config = {
            "sources": {
                "supabase": {
                    "url": settings.supabase.url,
                    "key": settings.supabase.key,
                    "schema": settings.supabase.schema
                }
            },
            "cache": {
                "enabled": settings.redis.enabled,
                "redis_url": settings.redis.redis_url,
                "default_ttl": settings.redis.default_ttl,
                "key_prefix": settings.redis.key_prefix
            },
            "routing": {
                "default_source": settings.routing.default_source,
                "enable_fallback": settings.routing.enable_fallback,
                "health_check_interval": settings.routing.health_check_interval
            },
            "performance": {
                "query_timeout": settings.query_timeout,
                "max_concurrent_queries": settings.max_concurrent_queries
            },
            "logging": {
                "log_queries": settings.log_queries,
                "log_performance": settings.log_performance
            }
        }
        
        # Add optional database config
        if settings.database and settings.database.enabled:
            config["sources"]["postgresql"] = {
                "host": settings.database.host,
                "port": settings.database.port,
                "database": settings.database.database,
                "username": settings.database.username,
                "password": settings.database.password,
                "pool_size": settings.database.pool_size
            }
        
        # Add optional Databricks config
        if settings.databricks and settings.databricks.enabled:
            config["sources"]["databricks"] = {
                "server_hostname": settings.databricks.server_hostname,
                "http_path": settings.databricks.http_path,
                "access_token": settings.databricks.access_token
            }
        
        return config
        
    except Exception as e:
        raise ValueError(f"Failed to create data layer configuration: {e}")


def get_fallback_config() -> Dict[str, Any]:
    """Get fallback configuration when data layer is enabled but Supabase is not configured"""
    return {
        "enabled": True,
        "sources": {},  # No sources available
        "cache": {
            "enabled": True,
            "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            "default_ttl": 3600,
            "key_prefix": "data_layer:"
        },
        "routing": {
            "default_source": None,
            "enable_fallback": False,
            "health_check_interval": 60
        },
        "performance": {
            "query_timeout": 30,
            "max_concurrent_queries": 10
        },
        "logging": {
            "log_queries": True,
            "log_performance": True
        }
    }


def get_default_config() -> Dict[str, Any]:
    """Get default configuration for development/testing"""
    return {
        "sources": {
            "supabase": {
                "url": "http://localhost:54321",
                "key": "your-anon-key",
                "schema": "public"
            }
        },
        "cache": {
            "enabled": True,
            "redis_url": "redis://localhost:6379/0",
            "default_ttl": 3600,
            "key_prefix": "data_layer:"
        },
        "routing": {
            "default_source": "supabase",
            "enable_fallback": True,
            "health_check_interval": 60
        },
        "performance": {
            "query_timeout": 30,
            "max_concurrent_queries": 10
        },
        "logging": {
            "log_queries": True,
            "log_performance": True
        }
    }


def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate data layer configuration"""
    errors = []
    
    # Validate required sources
    sources = config.get("sources", {})
    if not sources:
        errors.append("At least one data source must be configured")
    
    # Validate Supabase config if present
    if "supabase" in sources:
        supabase_config = sources["supabase"]
        if not supabase_config.get("url"):
            errors.append("Supabase URL is required")
        if not supabase_config.get("key"):
            errors.append("Supabase key is required")
    
    # Validate cache config
    cache_config = config.get("cache", {})
    if cache_config.get("enabled", True):
        redis_url = cache_config.get("redis_url", "")
        if not redis_url.startswith(("redis://", "rediss://")):
            errors.append("Invalid Redis URL format")
    
    # Validate performance settings
    performance = config.get("performance", {})
    if performance.get("query_timeout", 30) <= 0:
        errors.append("Query timeout must be positive")
    if performance.get("max_concurrent_queries", 10) <= 0:
        errors.append("Max concurrent queries must be positive")
    
    if errors:
        raise ValueError("Configuration validation failed: " + "; ".join(errors))
    
    return config


def create_test_config() -> Dict[str, Any]:
    """Create configuration for testing"""
    return {
        "sources": {
            "supabase": {
                "url": "http://localhost:54321",
                "key": "test-key",
                "schema": "public"
            }
        },
        "cache": {
            "enabled": False,  # Disable cache for testing
            "redis_url": "redis://localhost:6379/1",  # Use different DB
            "default_ttl": 300,
            "key_prefix": "test_data_layer:"
        },
        "routing": {
            "default_source": "supabase",
            "enable_fallback": False,  # Disable fallback for testing
            "health_check_interval": 10
        },
        "performance": {
            "query_timeout": 10,
            "max_concurrent_queries": 5
        },
        "logging": {
            "log_queries": True,
            "log_performance": False
        }
    }