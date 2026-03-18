from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    DB_URL_NEON: str = ""
    ENVIRONMENT: str = "development"
    STRIPE_API_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    CURRENCY: str = "usd"
    
    CORS_ORIGINS: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

settings = Settings()
