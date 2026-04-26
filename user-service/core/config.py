from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Union
import os


class Settings(BaseSettings):

    # ================= DATABASE =================
    DB_URL_NEON: str

    # ================= JWT =================
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ================= GOOGLE AUTH =================
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""

    # ================= FRONTEND =================
    FRONTEND_URL: str = "http://localhost:5173"

    # ================= CORS =================
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://lit-scholar.vercel.app"
    ]

    # ================= EMAIL =================
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SENDER_EMAIL: str = ""

    # ================= INTER-SERVICE =================
    # URL for lit-ai-engine (the only other backend service)
    LIT_AI_ENGINE_URL: str = "http://localhost:8001"

    # ================= ENV =================
    ENVIRONMENT: str = "development"
    RENDER: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ================= HELPERS =================
    @property
    def cors_origins_list(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, str):
            origins = [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
        else:
            origins = [str(o).strip() for o in self.CORS_ORIGINS if str(o).strip()]

        # Ensure current frontend URL is always allowed.
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
    def normalized_lit_ai_engine_url(self) -> str:
        return self.LIT_AI_ENGINE_URL.rstrip("/") if self.LIT_AI_ENGINE_URL else ""


# ================= INSTANCE =================
settings = Settings()


# ================= RENDER AUTO CONFIG =================
if os.environ.get("RENDER"):
    settings.RENDER = True
    settings.ENVIRONMENT = "production"

    if os.environ.get("LIT_AI_ENGINE_URL"):
        settings.LIT_AI_ENGINE_URL = os.environ["LIT_AI_ENGINE_URL"]
    elif os.environ.get("AI_SERVICE_URL"):
        # Backward compatibility with older env var name
        settings.LIT_AI_ENGINE_URL = os.environ["AI_SERVICE_URL"]

# Generic deployment compatibility (non-Render too)
if os.environ.get("ENVIRONMENT", "").lower() == "production":
    settings.ENVIRONMENT = "production"

if os.environ.get("FRONTEND_URL"):
    settings.FRONTEND_URL = os.environ["FRONTEND_URL"]

if os.environ.get("LIT_AI_ENGINE_URL"):
    settings.LIT_AI_ENGINE_URL = os.environ["LIT_AI_ENGINE_URL"]
elif os.environ.get("AI_SERVICE_URL"):
    settings.LIT_AI_ENGINE_URL = os.environ["AI_SERVICE_URL"]

# Normalize URL values once after env overrides.
settings.FRONTEND_URL = settings.normalized_frontend_url
settings.LIT_AI_ENGINE_URL = settings.normalized_lit_ai_engine_url

# Guard rail for production deployments.
if settings.is_production and not settings.JWT_SECRET:
    raise RuntimeError("JWT_SECRET must be set in production")


# ================= DEBUG =================
if not settings.is_production:
    print("\n" + "=" * 50)
    print("🔍 CONFIG CHECK")
    print(f"ENV: {settings.ENVIRONMENT}")
    print(f"CORS: {settings.cors_origins_list}")
    print(f"FRONTEND: {settings.normalized_frontend_url}")
    print(f"LIT_AI_ENGINE_URL: {settings.normalized_lit_ai_engine_url}")
    print("=" * 50 + "\n")