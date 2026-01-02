"""Configuration management for image-optimizer service."""
import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Image processing settings
    target_width: int = 2560
    target_height: int = 1440

    # Samba/Output settings (container path, mounted from host)
    output_path: str = "/data/images"

    # RabbitMQ settings
    rabbitmq_host: str = "rabbitmq"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"

    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    class Config:
        """Pydantic settings configuration."""

        env_file = "/app/config/app.env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
