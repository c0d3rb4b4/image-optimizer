"""Configuration management for image-optimizer service."""
import logging
import os
from functools import lru_cache

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


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
    rabbitmq_vhost: str = "/"

    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    class Config:
        """Pydantic settings configuration."""

        env_file = "/app/config/app.env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields in env file


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings()
    
    # Log all settings on first load
    logger.info("=== Settings loaded ===")
    logger.info(f"ENV OUTPUT_PATH: {os.environ.get('OUTPUT_PATH', 'NOT SET')}")
    logger.info(f"settings.output_path: {settings.output_path}")
    logger.info(f"settings.target_width: {settings.target_width}")
    logger.info(f"settings.target_height: {settings.target_height}")
    logger.info(f"Env file path: /app/config/app.env")
    logger.info(f"Env file exists: {os.path.exists('/app/config/app.env')}")
    
    # Try to read env file contents
    try:
        if os.path.exists('/app/config/app.env'):
            with open('/app/config/app.env', 'r') as f:
                logger.info("=== app.env contents ===")
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Mask passwords
                        if 'PASSWORD' in line.upper():
                            key = line.split('=')[0]
                            logger.info(f"{key}=***MASKED***")
                        else:
                            logger.info(line)
    except Exception as e:
        logger.error(f"Failed to read env file: {e}")
    
    return settings
