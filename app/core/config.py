from typing import List, Optional, Union
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
    LOG_LEVEL: str = "INFO"
    
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

    class SupabaseConfig(BaseModel):
        URL: str
        KEY: str

    DATA_LAYER_SUPABASE: SupabaseConfig
    
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
    
    model_config = {
        "env_file": ".env",
        "env_nested_delimiter": "__",
        "case_sensitive": True,
    }


settings = Settings()