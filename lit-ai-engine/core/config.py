from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from typing import List, Union

class Settings(BaseSettings):
    # Database
    DB_URL_NEON: str = ""

    # JWT Settings (kept for compatibility)
    JWT_SECRET: str = "dev-secret-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    
    # user-service URL (auth verification source)
    USER_SERVICE_URL: str = "http://localhost:8000"

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
        else:
            origins = [str(origin).strip() for origin in self.CORS_ORIGINS]

        origins = [o for o in origins if o]

        # Ensure frontend URL is always allowed.
        frontend = self.normalized_frontend_url
        if frontend and frontend not in origins:
            origins.append(frontend)

        # Helpful defaults for local dev.
        dev_defaults = ["http://localhost:5173", "http://127.0.0.1:5173"]
        for origin in dev_defaults:
            if origin not in origins:
                origins.append(origin)

        return origins

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production" or self.RENDER

    @property
    def normalized_frontend_url(self) -> str:
        return self.FRONTEND_URL.rstrip("/") if self.FRONTEND_URL else ""

    @property
    def normalized_user_service_url(self) -> str:
        return self.USER_SERVICE_URL.rstrip("/") if self.USER_SERVICE_URL else ""

settings = Settings()

# Auto-detect Render environment
if os.environ.get('RENDER'):
    settings.RENDER = True
    settings.ENVIRONMENT = "production"
    
    if settings.JWT_SECRET == "dev-secret-change-this-in-production":
        settings.JWT_SECRET = os.environ.get('JWT_SECRET', settings.JWT_SECRET)
    
    # Prefer current env var, fallback to old name for compatibility
    if os.environ.get('USER_SERVICE_URL'):
        settings.USER_SERVICE_URL = os.environ.get('USER_SERVICE_URL')
    elif os.environ.get('IDENTITY_SERVICE_URL'):
        settings.USER_SERVICE_URL = os.environ.get('IDENTITY_SERVICE_URL')

# Generic deployment compatibility (non-Render too)
if os.environ.get("ENVIRONMENT", "").lower() == "production":
    settings.ENVIRONMENT = "production"

if os.environ.get("FRONTEND_URL"):
    settings.FRONTEND_URL = os.environ.get("FRONTEND_URL")

if os.environ.get("USER_SERVICE_URL"):
    settings.USER_SERVICE_URL = os.environ.get("USER_SERVICE_URL")
elif os.environ.get("IDENTITY_SERVICE_URL"):
    settings.USER_SERVICE_URL = os.environ.get("IDENTITY_SERVICE_URL")

# Normalize URLs once after env overrides.
settings.FRONTEND_URL = settings.normalized_frontend_url
settings.USER_SERVICE_URL = settings.normalized_user_service_url

# Guard rail for production deployments.
if settings.is_production and not settings.JWT_SECRET:
    raise RuntimeError("JWT_SECRET must be set in production")

if not settings.is_production:
    print("\n" + "="*50)
    print("🔍 LIT-AI-ENGINE CONFIGURATION:")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"User Service URL: {settings.normalized_user_service_url}")
    print(f"CORS Origins: {settings.cors_origins_list}")
    print("="*50 + "\n")