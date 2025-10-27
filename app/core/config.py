"""
Application configuration management using Pydantic Settings.

This module handles all environment variables and application settings.
Settings are automatically loaded from .env file and environment variables.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings can be overridden via environment variables or .env file.
    """

    # Application
    APP_NAME: str = "Coffee Shop API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str

    # JWT Configuration
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Verification
    VERIFICATION_CODE_EXPIRATION: int = 3  # 3 minutes
    UNVERIFIED_USER_DELETE_DAYS: int = 2

    # Redis (for Celery)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Email Configuration (Optional - for verification emails)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@coffeeshop.com"

    # CORS (if needed for frontend)
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Initial Admin User
    FIRST_ADMIN_EMAIL: str
    FIRST_ADMIN_PASSWORD: str

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )


# Create a global settings instance
settings = Settings()
