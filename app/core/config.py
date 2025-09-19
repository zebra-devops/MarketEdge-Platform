from typing import List, Optional, Union, Dict, Any
from pydantic import field_validator, Field
from pydantic_settings import BaseSettings
import os
from pydantic import BaseModel


class Settings(BaseSettings):
    PROJECT_NAME: str = "Platform Wrapper"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str
    DATABASE_URL_TEST: Optional[str] = None
    TEST_DATABASE_URL: Optional[str] = None
    REDIS_URL: str = "redis://localhost:6379"
    
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    AUTH0_DOMAIN: str
    AUTH0_CLIENT_ID: str
    AUTH0_CLIENT_SECRET: str
    AUTH0_CALLBACK_URL: str = "http://localhost:3000/callback"
    
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "info"
    
    # Production Cookie Security Settings
    COOKIE_SECURE: bool = True  # Force HTTPS in production
    COOKIE_SAMESITE: str = "lax"  # Options: strict, lax, none
    COOKIE_HTTPONLY: bool = True  # Prevent XSS
    COOKIE_DOMAIN: Optional[str] = None  # Set for production domain
    COOKIE_PATH: str = "/"
    
    # Session Security Settings
    SESSION_TIMEOUT_MINUTES: int = 30
    SESSION_ABSOLUTE_TIMEOUT_HOURS: int = 8
    SESSION_RENEWAL_THRESHOLD_MINUTES: int = 15
    
    # Security Headers Configuration
    SECURITY_HEADERS_ENABLED: bool = True
    CSP_ENABLED: bool = True
    HSTS_MAX_AGE: int = 31536000  # 1 year
    HSTS_INCLUDE_SUBDOMAINS: bool = True
    
    CORS_ORIGINS: Union[str, List[str]] = Field(default=["http://localhost:3000", "http://localhost:3001"])
    
    # Rate Limiting Configuration
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    RATE_LIMIT_BURST_SIZE: int = 10
    RATE_LIMIT_TENANT_REQUESTS_PER_MINUTE: int = 1000
    RATE_LIMIT_ADMIN_REQUESTS_PER_MINUTE: int = 5000
    RATE_LIMIT_STORAGE_URL: str = "redis://localhost:6379/1"
    
    # Redis Security Configuration
    REDIS_PASSWORD: Optional[str] = None
    REDIS_SSL_ENABLED: bool = False
    REDIS_SSL_CA_CERTS: Optional[str] = None
    REDIS_SSL_CERT_REQS: str = "none"  # Options: none, optional, required
    REDIS_CONNECTION_POOL_SIZE: int = 50
    REDIS_HEALTH_CHECK_INTERVAL: int = 30
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5
    REDIS_SOCKET_TIMEOUT: int = 2
    REDIS_RETRY_ON_TIMEOUT: bool = True
    REDIS_MAX_CONNECTIONS: int = 50

    class SupabaseConfig(BaseModel):
        URL: str
        KEY: str

    # Data Layer Configuration - Optional
    DATA_LAYER_ENABLED: bool = False
    DATA_LAYER_SUPABASE: Optional[SupabaseConfig] = None
    
    @field_validator("DATA_LAYER_SUPABASE", mode="before")
    @classmethod
    def validate_supabase_config(cls, v, info):
        """Validate Supabase configuration - only required if DATA_LAYER_ENABLED is True"""
        # Get DATA_LAYER_ENABLED value from the same model
        data_layer_enabled = info.data.get("DATA_LAYER_ENABLED", False)
        
        if not data_layer_enabled:
            # If data layer is disabled, Supabase config is not required
            return None
        
        # If data layer is enabled, try to build Supabase config from environment
        if v is None:
            supabase_url = os.getenv("DATA_LAYER_SUPABASE__URL")
            supabase_key = os.getenv("DATA_LAYER_SUPABASE__KEY")
            
            if supabase_url and supabase_key:
                return cls.SupabaseConfig(URL=supabase_url, KEY=supabase_key)
            else:
                # Data layer enabled but no Supabase config - this is okay, will use fallback
                return None
        
        return v
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        """Parse CORS_ORIGINS from various formats: JSON array, comma-separated string, or single URL"""
        if isinstance(v, str):
            # Handle empty or whitespace-only strings
            if not v.strip():
                return ["http://localhost:3000"]
                
            if v.startswith("[") and v.endswith("]"):
                # Handle JSON-like format: ["url1","url2"]
                import json
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    # Fall back to comma-separated parsing
                    v = v.strip("[]").replace('"', '').replace("'", "")
                    return [i.strip() for i in v.split(",") if i.strip()]
            else:
                # Handle comma-separated format: url1,url2 or single URL
                return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        # Return default if we can't parse
        return ["http://localhost:3000"]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def cookie_secure(self) -> bool:
        """Determine if cookies should be secure based on environment"""
        if self.is_production:
            return True
        # Development: Use False for HTTP localhost development
        if self.ENVIRONMENT.lower() == "development":
            return False
        return self.COOKIE_SECURE
    
    @property
    def cookie_samesite(self) -> str:
        """Get appropriate SameSite setting for environment"""
        if self.is_production:
            return "none"  # Allow cross-domain with Secure=true
        return self.COOKIE_SAMESITE
    
    def get_cookie_settings(self) -> Dict[str, Any]:
        """Get complete cookie configuration for current environment"""
        settings = {
            "secure": self.cookie_secure,
            "httponly": self.COOKIE_HTTPONLY,
            "samesite": self.cookie_samesite,
            "path": self.COOKIE_PATH
        }
        
        if self.COOKIE_DOMAIN:
            settings["domain"] = self.COOKIE_DOMAIN
            
        return settings
    
    def get_test_database_url(self) -> str:
        """Get appropriate database URL for testing environment with proper isolation"""
        if self.TEST_DATABASE_URL:
            return self.TEST_DATABASE_URL
        elif self.DATABASE_URL_TEST:
            # Fix Docker hostname resolution in test URL
            test_url = self.DATABASE_URL_TEST
            docker_hosts = ["db", "postgres", "postgresql"]
            for host in docker_hosts:
                if f"@{host}:" in test_url and "localhost" not in test_url:
                    test_url = test_url.replace(f"@{host}:", "@localhost:")
                    break
            return test_url
        else:
            # Environment-aware test database configuration
            if self.ENVIRONMENT == "test" or os.getenv("PYTEST_CURRENT_TEST"):
                # Use unique SQLite database per test run for complete isolation
                import uuid
                unique_id = str(uuid.uuid4())[:8]
                return f"sqlite:///./test_tenant_security_{unique_id}.db"
            elif "railway.internal" in self.DATABASE_URL or self.ENVIRONMENT == "production":
                # Use Railway's internal PostgreSQL service for tests
                return self.DATABASE_URL.replace("/railway", "/test_database")
            else:
                # Local development - convert any docker hostnames to localhost
                base_url = self.DATABASE_URL
                # Replace common docker hostnames with localhost for local testing
                docker_hosts = ["db", "postgres", "postgresql"]
                for host in docker_hosts:
                    if f"@{host}:" in base_url:
                        base_url = base_url.replace(f"@{host}:", "@localhost:")
                        break
                
                # Change database name for testing
                if base_url.endswith("/platform_wrapper"):
                    return base_url.replace("/platform_wrapper", "/test_tenant_security")
                else:
                    return "postgresql://test_user:test_pass@localhost:5432/test_tenant_security"
    
    def get_database_url_for_environment(self) -> str:
        """Get database URL based on current environment with hostname resolution"""
        base_url = self.DATABASE_URL
        
        # Environment-specific hostname resolution
        if self.ENVIRONMENT == "development":
            # Development: Convert docker hostnames to localhost if needed
            docker_hosts = ["db", "postgres", "postgresql"] 
            for host in docker_hosts:
                if f"@{host}:" in base_url and "localhost" not in base_url:
                    # Check if we can connect to localhost instead
                    base_url = base_url.replace(f"@{host}:", "@localhost:")
                    break
        elif self.ENVIRONMENT == "production":
            # Production: Should already have correct Railway internal hostnames
            pass
        
        return base_url
    
    def get_redis_url_for_environment(self) -> str:
        """Get Redis URL based on current environment with hostname resolution"""
        base_url = self.REDIS_URL
        
        # Environment-specific hostname resolution for Redis
        if self.ENVIRONMENT == "development":
            # Development: Convert docker hostnames to localhost if needed
            docker_hosts = ["redis", "redis-server"]
            for host in docker_hosts:
                if f"//{host}:" in base_url and "localhost" not in base_url:
                    # Check if we can connect to localhost instead
                    base_url = base_url.replace(f"//{host}:", "//localhost:")
                    break
        elif self.ENVIRONMENT == "production":
            # Production: Should already have correct Railway internal hostnames
            pass
        elif self.ENVIRONMENT == "test":
            # Test: Use localhost for Redis tests
            docker_hosts = ["redis", "redis-server"]
            for host in docker_hosts:
                if f"//{host}:" in base_url:
                    base_url = base_url.replace(f"//{host}:", "//localhost:")
                    break
        
        return base_url
    
    def get_rate_limit_redis_url_for_environment(self) -> str:
        """Get rate limit Redis URL based on current environment with hostname resolution"""
        base_url = self.RATE_LIMIT_STORAGE_URL
        
        # Environment-specific hostname resolution for rate limit Redis
        if self.ENVIRONMENT == "development":
            # Development: Convert docker hostnames to localhost if needed
            docker_hosts = ["redis", "redis-server"]
            for host in docker_hosts:
                if f"//{host}:" in base_url and "localhost" not in base_url:
                    base_url = base_url.replace(f"//{host}:", "//localhost:")
                    break
        elif self.ENVIRONMENT == "production":
            # Production: Should already have correct Railway internal hostnames
            pass
        elif self.ENVIRONMENT == "test":
            # Test: Use localhost for Redis tests
            docker_hosts = ["redis", "redis-server"]
            for host in docker_hosts:
                if f"//{host}:" in base_url:
                    base_url = base_url.replace(f"//{host}:", "//localhost:")
                    break
        
        return base_url
    
    def get_redis_connection_config(self) -> Dict[str, Any]:
        """Get Redis connection configuration for the current environment"""
        config = {
            "encoding": "utf-8",
            "decode_responses": True,
            "socket_connect_timeout": self.REDIS_SOCKET_CONNECT_TIMEOUT,
            "socket_timeout": self.REDIS_SOCKET_TIMEOUT,
            "retry_on_timeout": self.REDIS_RETRY_ON_TIMEOUT,
            "health_check_interval": self.REDIS_HEALTH_CHECK_INTERVAL,
            "max_connections": self.REDIS_MAX_CONNECTIONS
        }
        
        # Only add password if provided
        if self.REDIS_PASSWORD:
            config["password"] = self.REDIS_PASSWORD
            
        # Only add SSL configuration if enabled
        if self.REDIS_SSL_ENABLED:
            config["ssl"] = True
            if self.REDIS_SSL_CA_CERTS:
                config["ssl_ca_certs"] = self.REDIS_SSL_CA_CERTS
            config["ssl_cert_reqs"] = self.REDIS_SSL_CERT_REQS
        
        return config
    
    model_config = {
        "env_file": ".env",
        "env_nested_delimiter": "__",
        "case_sensitive": True,
    }


settings = Settings()