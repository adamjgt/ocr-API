import os
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Environment
    ENV: str = "development"
    DEBUG: bool = False
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379"
    
    # OCR Processing Limits
    MAX_FILE_SIZE_MB: int = 10
    MAX_PDF_PAGES: int = 20
    OCR_TIMEOUT_PER_PAGE: int = 10
    
    # Job Queue Settings
    RESULT_TTL: int = 86400  # 24 hours in seconds
    JOB_TIMEOUT: int = 300   # 5 minutes max per job
    
    # Rate Limiting Settings
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 10  # requests per window
    RATE_LIMIT_WINDOW: str = "minute"  # second, minute, hour, day
    
    # API Key Authentication
    API_KEY_ENABLED: bool = True
    API_KEYS: str = ""  # Comma-separated list of valid API keys
    API_KEY_HEADER: str = "X-API-Key"
    
    @property
    def api_keys_list(self) -> list:
        """Parse comma-separated API keys into list."""
        if not self.API_KEYS:
            return []
        return [key.strip() for key in self.API_KEYS.split(",") if key.strip()]
    
    # Allowed file types
    ALLOWED_EXTENSIONS: set = {"png", "jpg", "jpeg", "pdf"}
    
    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Get settings instance. Not cached during testing."""
    return Settings()


# Create settings instance at module load
settings = get_settings()
