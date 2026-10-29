"""
Application configuration loaded from environment variables.
Uses pydantic-settings for validation and type coercion.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional, List
import os


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────
    DATABASE_URL: str = "mysql://root:password@localhost:3306/plagiarism_db"

    # ── Redis / Celery ────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Session & Authentication Security ─────────────────────
    SECRET_KEY: str = "dev-secret-key-do-not-use-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours fallback

    SESSION_COOKIE_NAME: str = "session_id"
    SESSION_IDLE_TIMEOUT: int = 1800        # 30 minutes idle timeout
    SESSION_MAX_AGE: int = 86400            # 24 hours absolute maximum session lifetime
    
    COOKIE_SECURE: bool = False             # Set to True in production (requires HTTPS)
    COOKIE_SAMESITE: str = "lax"            # "lax" | "strict" | "none"
    CSRF_COOKIE_NAME: str = "csrf_token"

    # ── CORS Origins ──────────────────────────────────────────
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5176",
        "http://localhost:5177",
        "http://127.0.0.1:5177",
        "http://localhost:5178",
        "http://127.0.0.1:5178",
    ]

    # ── File Upload ───────────────────────────────────────────
    UPLOAD_DIR: str = "uploads"

    # ── SMTP Email Configuration ──────────────────────────────
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: str = "PlagiarismAI Support"
    FRONTEND_URL: str = "http://localhost:5173"

    # ── Password Reset Security ───────────────────────────────
    PASSWORD_RESET_TOKEN_EXPIRY_MINUTES: int = 20
    PASSWORD_RESET_RATE_LIMIT_IP: int = 5
    PASSWORD_RESET_RATE_LIMIT_EMAIL: int = 3
    PASSWORD_RESET_RATE_LIMIT_WINDOW: int = 900       # 15 minutes
    PASSWORD_RESET_OTP_EXPIRY_MINUTES: int = 10
    PASSWORD_RESET_MAX_OTP_ATTEMPTS: int = 5
    SECURITY_NOTIFICATION_ENABLED: bool = True

    # ── Admin Default User Password ───────────────────────────
    DEFAULT_USER_PASSWORD: str = "Welcome@123"

    # Allow extra environment variables in .env without raising ValidationErrors
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton — reads .env once."""
    return Settings()
