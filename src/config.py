"""Configuration management for image-optimizer service."""
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables.
    
    Only includes settings that may need to be tuned per deployment.
    Internal paths and constants are in constants.py.
    """

    # Image processing settings (tuneable)
    target_width: int = 2560
    target_height: int = 1440
    jpeg_quality: int = 95

    # Logging
    log_level: str = "INFO"

    class Config:
        """Pydantic settings configuration."""
        env_file = "/app/config/app.env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
