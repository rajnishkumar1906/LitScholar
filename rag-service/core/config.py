from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import os
from typing import List, Optional, Union

class Settings(BaseSettings):
    # Database
    DB_URL_NEON: str

    # JWT Settings (keep for potential internal use, but rag-service won't decode)
    JWT_SECRET: str = "dev-secret-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    
    # Identity Service URL
    IDENTITY_SERVICE_URL: str = "http://localhost:8000"  # Identity service endpoint

    # OAuth / Session (remove SessionMiddleware)
    SESSION_SECRET_KEY: str = "dev-session-secret-change-this-in-production"
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "https://lit-scholar.vercel.app"
    ]

    # Frontend
    FRONTEND_URL: str = "https://lit-scholar.vercel.app"

    # API Keys
    GEMINI_API_KEY: str = ""

    # Microservice URLs
    PAYMENT_SERVICE_URL: str = "http://localhost:8003"

    # Environment
    ENVIRONMENT: str = "development"
    RENDER: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, str):
            origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
            return [o for o in origins if o]
        return self.CORS_ORIGINS

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production" or self.RENDER

settings = Settings()

# Auto-detect Render environment
if os.environ.get('RENDER'):
    settings.RENDER = True
    settings.ENVIRONMENT = "production"
    
    if settings.JWT_SECRET == "dev-secret-change-this-in-production":
        settings.JWT_SECRET = os.environ.get('JWT_SECRET', settings.JWT_SECRET)
    
    if settings.SESSION_SECRET_KEY == "dev-session-secret-change-this-in-production":
        settings.SESSION_SECRET_KEY = os.environ.get('SESSION_SECRET_KEY', settings.SESSION_SECRET_KEY)
    
    if settings.FRONTEND_URL.endswith('/'):
        settings.FRONTEND_URL = settings.FRONTEND_URL.rstrip('/')
    
    # Override identity service URL in production if needed
    if os.environ.get('IDENTITY_SERVICE_URL'):
        settings.IDENTITY_SERVICE_URL = os.environ.get('IDENTITY_SERVICE_URL')

if not settings.is_production:
    print("\n" + "="*50)
    print("🔍 RAG SERVICE CONFIGURATION:")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Identity Service URL: {settings.IDENTITY_SERVICE_URL}")
    print(f"CORS Origins: {settings.cors_origins_list}")
    print("="*50 + "\n")