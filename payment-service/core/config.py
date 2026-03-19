from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    # Database
    DB_URL_NEON: str = ""
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # Razorpay Settings (replacing Stripe)
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""
    
    # Currency (Razorpay supports INR, USD, etc.)
    CURRENCY: str = "INR"  # Default to INR for Razorpay
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:5173"
    
    # Optional: Razorpay API Base URL (for testing vs production)
    RAZORPAY_API_URL: str = "https://api.razorpay.com/v1"  # Default to production

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

settings = Settings()