"""
Application configuration using Pydantic Settings.
All secrets and configuration are loaded from environment variables.
No hardcoded credentials - ever.
"""

from functools import lru_cache
from typing import List, Union
from pydantic import Field, field_validator, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    All sensitive values must be provided via .env or environment.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_parse_none_str="none",
    )
    
    # Application
    APP_NAME: str = "ForensicCTF"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = Field(..., description="Main application secret key")
    FLAG_SECRET_KEY: str = Field(..., description="Secret key for HMAC flag generation")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour - shorter for security
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7 days for refresh tokens
    
    # Trusted proxy configuration (IPs that can set X-Forwarded-For)
    TRUSTED_PROXIES: List[str] = ["127.0.0.1"]
    
    @field_validator("TRUSTED_PROXIES", mode="before")
    @classmethod
    def parse_trusted_proxies(cls, v):
        if isinstance(v, str):
            return [proxy.strip() for proxy in v.split(",")]
        return v
    
    # Account security
    MAX_LOGIN_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 15
    
    # Flag expiration (anti-leak protection)
    FLAG_EXPIRY_MINUTES: int = 60  # Flags expire after 1 hour
    FLAG_SALT_ROTATION_HOURS: int = 24  # User salt rotates every 24 hours
    
    # Password hashing (Argon2)
    ARGON2_TIME_COST: int = 3
    ARGON2_MEMORY_COST: int = 65536  # 64 MB
    ARGON2_PARALLELISM: int = 4
    ARGON2_HASH_LEN: int = 32
    ARGON2_SALT_LEN: int = 16
    
    # Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = Field(..., description="PostgreSQL username")
    POSTGRES_PASSWORD: str = Field(..., description="PostgreSQL password")
    POSTGRES_DB: str = "forensic_ctf"
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    @property
    def DATABASE_URL_SYNC(self) -> str:
        """Sync database URL for Alembic migrations."""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    # MinIO / S3 Storage
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_PUBLIC_ENDPOINT: str = "localhost:9000"  # Public URL for presigned URLs (browser access)
    MINIO_ACCESS_KEY: str = Field(..., description="MinIO access key")
    MINIO_SECRET_KEY: str = Field(..., description="MinIO secret key")
    MINIO_BUCKET_NAME: str = "forensic-artifacts"
    MINIO_USE_SSL: bool = False
    
    # Rate Limiting
    RATE_LIMIT_SUBMISSIONS_PER_MINUTE: int = 10
    RATE_LIMIT_AUTH_PER_MINUTE: int = 5
    
    # CORS
    ALLOWED_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://localhost:3001"
    
    @field_validator("ALLOWED_ORIGINS", mode="after")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            # Handle comma-separated string
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v if isinstance(v, list) else [v]


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()


# Global settings instance
settings = get_settings()
