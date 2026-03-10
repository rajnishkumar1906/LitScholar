from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import os

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

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # Frontend
    FRONTEND_URL: str = "http://localhost:5173"

    # API Keys
    GEMINI_API_KEY: str = ""

    # Environment
    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

# Create settings instance
settings = Settings()

# Debug output
print("\n" + "="*50)
print("🔍 ENVIRONMENT VARIABLES CHECK:")
print(f".env file exists: {Path('.env').exists()}")
print(f"GEMINI_API_KEY from settings: '{settings.GEMINI_API_KEY}'")
if not settings.GEMINI_API_KEY:
    # Try to read .env file directly
    try:
        with open('.env', 'r') as f:
            env_content = f.read()
            if 'GEMINI_API_KEY' in env_content:
                print("✅ GEMINI_API_KEY found in .env file but not loading")
                # Extract the key to verify
                for line in env_content.split('\n'):
                    if line.startswith('GEMINI_API_KEY='):
                        key = line.split('=', 1)[1]
                        print(f"Key in .env: '{key[:6]}...'")
                        break
    except Exception as e:
        print(f"❌ Could not read .env file: {e}")
print("="*50 + "\n")