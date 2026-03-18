from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import os
from typing import List, Optional, Union

class Settings(BaseSettings):
    # Database
    DB_URL_NEON: str

    # JWT Settings
    JWT_SECRET: str = "dev-secret-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # OAuth / Session
    SESSION_SECRET_KEY: str = "dev-session-secret-change-this-in-production"
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""

    # CORS - can be string or list
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "https://lit-scholar.vercel.app"  # No trailing slash!
    ]

    # Frontend
    FRONTEND_URL: str = "https://lit-scholar.vercel.app"  # No trailing slash!

    # API Keys
    GEMINI_API_KEY: str = ""

    # Microservice URLs
    PAYMENT_SERVICE_URL: str = "http://localhost:8003"

    # Environment
    ENVIRONMENT: str = "development"
    
    # Render specific
    RENDER: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS to list format"""
        if isinstance(self.CORS_ORIGINS, str):
            # Split by comma and strip whitespace
            origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
            # Remove any empty strings
            return [o for o in origins if o]
        return self.CORS_ORIGINS

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT.lower() == "production" or self.RENDER

# Create settings instance
settings = Settings()

# Auto-detect Render environment
if os.environ.get('RENDER'):
    settings.RENDER = True
    settings.ENVIRONMENT = "production"
    
    # In production, ensure secrets are set from environment variables
    if settings.JWT_SECRET == "dev-secret-change-this-in-production":
        settings.JWT_SECRET = os.environ.get('JWT_SECRET', settings.JWT_SECRET)
    
    if settings.SESSION_SECRET_KEY == "dev-session-secret-change-this-in-production":
        settings.SESSION_SECRET_KEY = os.environ.get('SESSION_SECRET_KEY', settings.SESSION_SECRET_KEY)
    
    # Ensure FRONTEND_URL has no trailing slash in production
    if settings.FRONTEND_URL.endswith('/'):
        settings.FRONTEND_URL = settings.FRONTEND_URL.rstrip('/')

# Debug output (only in development)
if not settings.is_production:
    print("\n" + "="*50)
    print("🔍 ENVIRONMENT VARIABLES CHECK:")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Render detected: {settings.RENDER}")
    print(f"CORS Origins: {settings.cors_origins_list}")
    print(f"Frontend URL: {settings.FRONTEND_URL}")
    print(f"Google Redirect URI: {settings.GOOGLE_REDIRECT_URI}")
    print(f".env file exists: {Path('.env').exists()}")
    print(f"GEMINI_API_KEY from settings: '{settings.GEMINI_API_KEY[:5] if settings.GEMINI_API_KEY else 'Not set'}...'")
    print("="*50 + "\n")
